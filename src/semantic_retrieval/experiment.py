"""Run the minimal Voyage semantic-retrieval experiment end to end."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from .chunking import VoyageTokenizer, chunk_jsonl, write_chunks
from .evaluation import aggregate, map_evidence, score_question
from .ranking import rank_vectors


class Embedder(Protocol):
    def embed(
        self, texts: list[str], *, input_type: str
    ) -> tuple[list[list[float]], int | None]: ...


class VoyageEmbedder:
    def __init__(self, api_key: str, model: str, dimension: int) -> None:
        import voyageai

        self._client = voyageai.Client(api_key=api_key)
        self.model = model
        self.dimension = dimension

    def embed(
        self, texts: list[str], *, input_type: str
    ) -> tuple[list[list[float]], int | None]:
        response = self._client.embed(
            texts,
            model=self.model,
            input_type=input_type,
            output_dimension=self.dimension,
            truncation=False,
        )
        return response.embeddings, getattr(response, "total_tokens", None)


def fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_pages(path: Path) -> dict[tuple[str, int], str]:
    pages = {}
    with path.open(encoding="utf-8") as lines:
        for line in lines:
            page = json.loads(line)
            pages[(page["source_file"], page["page_number"])] = page["text"]
    return pages


def embed_batches(
    embedder: Embedder, texts: list[str], input_type: str, batch_size: int
) -> tuple[list[list[float]], int | None, int, float]:
    vectors: list[list[float]] = []
    total_tokens: int | None = 0
    calls = 0
    started = time.perf_counter()
    for offset in range(0, len(texts), batch_size):
        batch_vectors, tokens = embedder.embed(
            texts[offset : offset + batch_size], input_type=input_type
        )
        vectors.extend(batch_vectors)
        calls += 1
        total_tokens = (
            total_tokens + tokens
            if total_tokens is not None and tokens is not None
            else None
        )
    return vectors, total_tokens, calls, (time.perf_counter() - started) * 1000


def validate_vectors(
    vectors: list[list[float]], expected_count: int, dimension: int
) -> None:
    if len(vectors) != expected_count:
        raise ValueError(
            f"expected {expected_count} embeddings, received {len(vectors)}"
        )
    if any(len(vector) != dimension for vector in vectors):
        raise ValueError(
            f"one or more embeddings do not have configured dimension {dimension}"
        )


def diagnostic_slices(question_results: list[dict[str, Any]], k: int) -> dict[str, Any]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    for field in ("difficulty", "evidence_format", "span_type", "product"):
        values: dict[str, list[dict[str, Any]]] = {}
        for item in question_results:
            if item["question_id"] == "Q040":
                continue
            values.setdefault(str(item[field]), []).append(
                item["evaluation_by_k"][str(k)]
            )
        buckets[field] = {
            name: aggregate(scores) for name, scores in sorted(values.items())
        }
    return buckets


def run_experiment(
    config: dict[str, Any],
    pages_path: Path,
    gold_path: Path,
    output_dir: Path,
    *,
    tokenizer: Any,
    embedder: Embedder,
) -> dict[str, Any]:
    started_at = datetime.now(timezone.utc)
    chunks = chunk_jsonl(
        pages_path,
        tokenizer,
        config["chunk_size_tokens"],
        config["chunk_overlap_tokens"],
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    write_chunks(chunks, output_dir / "chunks.jsonl")

    document_vectors, document_tokens, document_calls, document_latency = embed_batches(
        embedder,
        [chunk.text for chunk in chunks],
        "document",
        config["document_batch_size"],
    )
    validate_vectors(document_vectors, len(chunks), config["embedding_dimension"])
    (output_dir / "vectors.json").write_text(
        json.dumps(
            {"chunk_ids": [c.chunk_id for c in chunks], "vectors": document_vectors},
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )

    gold = json.loads(gold_path.read_text(encoding="utf-8"))["records"]
    mappings = map_evidence(gold, chunks, read_pages(pages_path))
    chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    k_values = config["k_values"]
    questions = []
    query_tokens = 0
    query_tokens_available = True
    query_calls = 0
    query_embedding_latency = 0.0
    for record in gold:
        item: dict[str, Any] = {
            "question_id": record["question_id"],
            "question": record["question"],
            "difficulty": record["difficulty"],
            "evidence_format": record["evidence_format"],
            "span_type": "multi_span"
            if len(record["evidence_spans"]) > 1
            else "single_span",
            "product": record["evidence_spans"][0]["source_file"]
            if record["evidence_spans"]
            else "none",
            "gold_mapping": mappings[record["question_id"]],
            "failures": [],
        }
        try:
            before = time.perf_counter()
            vectors, tokens = embedder.embed([record["question"]], input_type="query")
            elapsed = (time.perf_counter() - before) * 1000
            query_embedding_latency += elapsed
            query_calls += 1
            if tokens is None:
                query_tokens_available = False
            else:
                query_tokens += tokens
            validate_vectors(vectors, 1, config["embedding_dimension"])
            retrieval_started = time.perf_counter()
            ranked = rank_vectors(
                vectors[0],
                [c.chunk_id for c in chunks],
                document_vectors,
                max(k_values),
            )
            retrieval_latency = (time.perf_counter() - retrieval_started) * 1000
            item["query_embedding_tokens"] = tokens
            item["query_embedding_latency_ms"] = elapsed
            item["retrieval_latency_ms"] = retrieval_latency
            item["retrieved"] = [
                {
                    "rank": rank,
                    "chunk_id": chunk_id,
                    "source_file": chunk_by_id[chunk_id].source_file,
                    "product_name": chunk_by_id[chunk_id].product_name,
                    "page_number": chunk_by_id[chunk_id].page_number,
                    "cosine_similarity": score,
                }
                for rank, (chunk_id, score) in enumerate(ranked, 1)
            ]
            gold_sources = {span["source_file"] for span in record["evidence_spans"]}
            item["wrong_document_at_k"] = {
                str(k): sum(
                    hit["source_file"] not in gold_sources
                    for hit in item["retrieved"][:k]
                )
                for k in k_values
            }
            item["evaluation_by_k"] = {
                str(k): score_question(
                    record["question_id"],
                    mappings,
                    [hit["chunk_id"] for hit in item["retrieved"][:k]],
                    abstention_probe=record["question_id"] == "Q040",
                )
                for k in k_values
            }
        except Exception as error:  # Per-question errors belong in experiment output.
            item["failures"].append(
                {"type": type(error).__name__, "message": str(error)}
            )
            item["evaluation_by_k"] = {
                str(k): score_question(
                    record["question_id"],
                    mappings,
                    [],
                    abstention_probe=record["question_id"] == "Q040",
                )
                for k in k_values
            }
        questions.append(item)

    metrics = {
        str(k): aggregate([item["evaluation_by_k"][str(k)] for item in questions])
        for k in k_values
    }
    price = config.get("price_usd_per_million_tokens")
    total_query_tokens = query_tokens if query_tokens_available else None
    result = {
        "status": "completed",
        "timestamp_utc": started_at.isoformat(),
        "configuration": config,
        "inputs": {
            str(pages_path): fingerprint(pages_path),
            str(gold_path): fingerprint(gold_path),
        },
        "software": {"python": platform.python_version()},
        "corpus_embedding": {
            "chunks_embedded": len(chunks),
            "tokens": document_tokens,
            "api_calls": document_calls,
            "latency_ms": document_latency,
            "estimated_list_price_usd": document_tokens * price / 1_000_000
            if document_tokens is not None and price is not None
            else None,
        },
        "query_embedding": {
            "questions_attempted": len(gold),
            "tokens": total_query_tokens,
            "api_calls": query_calls,
            "latency_ms": query_embedding_latency,
            "estimated_list_price_usd": total_query_tokens * price / 1_000_000
            if total_query_tokens is not None and price is not None
            else None,
        },
        "metrics_by_k": metrics,
        "diagnostic_slices_at_k_10": diagnostic_slices(questions, 10),
        "medicare_plus_mapping_review": [
            item["question_id"]
            for item in questions
            if "Medi_Care_Plus" in item["product"]
            and any(span["human_review_required"] for span in item["gold_mapping"])
        ],
        "abstention_probe": {
            "question_id": "Q040",
            "positive_recall_aggregation": "excluded",
            "evaluation": "not defined by this positive-evidence experiment",
        },
        "questions": questions,
    }
    (output_dir / "retrieval_results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/stage1_voyage4.json")
    )
    parser.add_argument(
        "--pages", type=Path, default=Path("artifacts/extraction/policy_pages.jsonl")
    )
    parser.add_argument("--gold", type=Path, default=Path("evals/gold_dataset.json"))
    parser.add_argument(
        "--output-dir", type=Path, default=Path("artifacts/retrieval/stage1_voyage4")
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    api_key = os.environ.get("VOYAGE_API_KEY")
    if not api_key:
        raise SystemExit(
            "VOYAGE_API_KEY is required; no API key was found in the environment"
        )
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_experiment(
        config,
        args.pages,
        args.gold,
        args.output_dir,
        tokenizer=VoyageTokenizer(config["tokenizer_model"]),
        embedder=VoyageEmbedder(
            api_key, config["embedding_model"], config["embedding_dimension"]
        ),
    )
    print(
        json.dumps(
            {"status": result["status"], "metrics_by_k": result["metrics_by_k"]},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
