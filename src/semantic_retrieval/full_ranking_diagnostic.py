"""Run a full-corpus diagnostic using the already committed Stage 1 chunks."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from evaluation.contract_v2 import score_unit
from semantic_retrieval.ranking import rank_vectors


K_VALUES = (1, 3, 5, 10, 20, 30, 50)


class Embedder(Protocol):
    def embed(
        self, texts: list[str], *, input_type: str
    ) -> tuple[list[list[float]], int, str | None]: ...


class VoyageEmbedder:
    """Small adapter that retains API-reported usage and model metadata."""

    def __init__(self, api_key: str, model: str, dimension: int) -> None:
        import voyageai

        self._client = voyageai.Client(api_key=api_key)
        self.model = model
        self.dimension = dimension

    def embed(
        self, texts: list[str], *, input_type: str
    ) -> tuple[list[list[float]], int, str | None]:
        response = self._client.embed(
            texts,
            model=self.model,
            input_type=input_type,
            output_dimension=self.dimension,
            truncation=False,
        )
        tokens = getattr(response, "total_tokens", None)
        if tokens is None:
            raise RuntimeError("Voyage response did not include token usage")
        # SDK releases differ in whether the response echoes the resolved model.
        returned_model = getattr(response, "model", None)
        return response.embeddings, tokens, returned_model


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate(vectors: list[list[float]], count: int, dimensions: int) -> None:
    if len(vectors) != count or any(len(vector) != dimensions for vector in vectors):
        raise ValueError(f"expected {count} vectors of {dimensions} dimensions")


def _embed_batches(
    embedder: Embedder,
    texts: list[str],
    *,
    input_type: str,
    batch_size: int,
) -> tuple[list[list[float]], int, int, float, list[str]]:
    vectors: list[list[float]] = []
    tokens = calls = 0
    models: set[str] = set()
    started = time.perf_counter()
    for offset in range(0, len(texts), batch_size):
        batch, usage, returned_model = embedder.embed(
            texts[offset : offset + batch_size], input_type=input_type
        )
        vectors.extend(batch)
        tokens += usage
        calls += 1
        if returned_model:
            models.add(returned_model)
    return vectors, tokens, calls, (time.perf_counter() - started) * 1000, sorted(models)


def run_diagnostic(
    config: dict[str, Any],
    chunks_path: Path,
    pages_path: Path,
    contract_path: Path,
    benchmark_path: Path,
    output_dir: Path,
    *,
    embedder: Embedder,
) -> dict[str, Any]:
    """Embed immutable inputs and persist complete rankings, but not vectors."""
    started_at = datetime.now(timezone.utc)
    run_id = output_dir.name
    chunks = _read_jsonl(chunks_path)
    pages = _read_jsonl(pages_path)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    with benchmark_path.open(encoding="utf-8", newline="") as handle:
        benchmark_questions = {
            row["question_id"]: row["question"] for row in csv.DictReader(handle)
        }
    records = [
        record
        for record in contract["records"]
        if record.get("evaluation_mode") != "negative_space"
    ]
    missing_questions = [record["question_id"] for record in records if record["question_id"] not in benchmark_questions]
    if missing_questions:
        raise ValueError(f"benchmark is missing questions for: {missing_questions}")
    dimensions = config["embedding_dimension"]

    document_vectors, document_tokens, document_calls, document_latency, document_models = _embed_batches(
        embedder,
        [chunk["text"] for chunk in chunks],
        input_type="document",
        batch_size=config["document_batch_size"],
    )
    _validate(document_vectors, len(chunks), dimensions)
    chunk_ids = [chunk["chunk_id"] for chunk in chunks]
    chunk_by_id = {chunk["chunk_id"]: chunk for chunk in chunks}
    chunk_text = {chunk["chunk_id"]: chunk["text"] for chunk in chunks}
    page_text = {(page["source_file"], page["page_number"]): page["text"] for page in pages}

    query_tokens = query_calls = 0
    query_latency = ranking_latency = 0.0
    query_models: set[str] = set()
    questions: list[dict[str, Any]] = []
    aggregate_counts = {
        str(k): {"required": 0, "covered": 0, "sufficient": 0} for k in K_VALUES
    }
    for record in records:
        before = time.perf_counter()
        vectors, tokens, returned_model = embedder.embed(
            [benchmark_questions[record["question_id"]]], input_type="query"
        )
        elapsed = (time.perf_counter() - before) * 1000
        _validate(vectors, 1, dimensions)
        query_tokens += tokens
        query_calls += 1
        query_latency += elapsed
        if returned_model:
            query_models.add(returned_model)
        before = time.perf_counter()
        ranked = rank_vectors(vectors[0], chunk_ids, document_vectors, len(chunks))
        rank_elapsed = (time.perf_counter() - before) * 1000
        ranking_latency += rank_elapsed
        retrieved = [
            {
                "rank": rank,
                "chunk_id": chunk_id,
                "source_file": chunk_by_id[chunk_id]["source_file"],
                "product_name": chunk_by_id[chunk_id]["product_name"],
                "page_number": chunk_by_id[chunk_id]["page_number"],
                "cosine_similarity": score,
            }
            for rank, (chunk_id, score) in enumerate(ranked, 1)
        ]
        evaluation_by_k: dict[str, Any] = {}
        for k in K_VALUES:
            units = [
                score_unit(unit, retrieved[:k], chunk_text, page_text)
                for unit in record["evidence_units"]
                if unit["required"]
            ]
            covered = sum(unit["matched"] for unit in units)
            sufficient = all(unit["matched"] for unit in units)
            aggregate_counts[str(k)]["required"] += len(units)
            aggregate_counts[str(k)]["covered"] += covered
            aggregate_counts[str(k)]["sufficient"] += int(sufficient)
            evaluation_by_k[str(k)] = {
                "covered_required_units": covered,
                "required_units": len(units),
                "sufficient_evidence": sufficient,
            }
        questions.append(
            {
                "question_id": record["question_id"],
                "query_text": benchmark_questions[record["question_id"]],
                "query_embedding_tokens": tokens,
                "query_embedding_latency_ms": elapsed,
                "ranking_latency_ms": rank_elapsed,
                "evaluation_by_k": evaluation_by_k,
                "retrieved": retrieved,
            }
        )

    metrics = {
        k: {
            "evaluated_questions": len(records),
            "required_evidence_units": values["required"],
            "covered_evidence_units": values["covered"],
            "atomic_evidence_recall": values["covered"] / values["required"],
            "sufficient_evidence_questions": values["sufficient"],
            "sufficient_evidence": values["sufficient"] / len(records),
        }
        for k, values in aggregate_counts.items()
    }
    price = config["price_usd_per_million_tokens"]
    total_tokens = document_tokens + query_tokens
    result = {
        "status": "completed",
        "run_id": run_id,
        "timestamp_utc": started_at.isoformat(),
        "architecture": "committed Stage 1 chunks -> Voyage embedding -> exhaustive cosine ranking",
        "configuration": {**config, "k_values": list(K_VALUES), "rank_limit": len(chunks)},
        "inputs": {
            str(chunks_path): _sha256(chunks_path),
            str(pages_path): _sha256(pages_path),
            str(contract_path): _sha256(contract_path),
            str(benchmark_path): _sha256(benchmark_path),
        },
        "software": {"python": platform.python_version()},
        "api_model_metadata": {
            "requested_model": config["embedding_model"],
            "document_response_models": document_models,
            "query_response_models": sorted(query_models),
            "note": "Empty response-model lists mean the installed Voyage SDK/API response did not echo a resolved version identifier.",
        },
        "corpus_embedding": {
            "chunks_embedded": len(chunks), "tokens": document_tokens,
            "api_calls": document_calls, "latency_ms": document_latency,
        },
        "query_embedding": {
            "questions_embedded": len(records), "tokens": query_tokens,
            "api_calls": query_calls, "latency_ms": query_latency,
        },
        "ranking": {"comparisons": len(chunks) * len(records), "latency_ms": ranking_latency},
        "usage_and_cost": {
            "total_tokens": total_tokens,
            "total_api_calls": document_calls + query_calls,
            "price_usd_per_million_tokens": price,
            "estimated_list_price_usd": total_tokens * price / 1_000_000,
        },
        "persistence": {
            "full_rankings_and_scores": True,
            "embedding_vectors": False,
            "reason": "Vectors are intentionally omitted as large reproducible caches; rankings and provenance are retained.",
        },
        "metrics_by_k": metrics,
        "questions": questions,
    }
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "full_rankings.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/stage1_voyage4.json"))
    parser.add_argument("--chunks", type=Path, default=Path("artifacts/retrieval/stage1_voyage4/chunks.jsonl"))
    parser.add_argument("--pages", type=Path, default=Path("artifacts/extraction/policy_pages.jsonl"))
    parser.add_argument("--contract", type=Path, default=Path("evals/evaluation_contract_v2.json"))
    parser.add_argument("--benchmark", type=Path, default=Path("evals/benchmark_spec_v1.csv"))
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    api_key = os.environ.get("VOYAGE_API_KEY")
    if not api_key:
        raise SystemExit("VOYAGE_API_KEY is required")
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_diagnostic(
        config, args.chunks, args.pages, args.contract, args.benchmark, args.output_dir,
        embedder=VoyageEmbedder(api_key, config["embedding_model"], config["embedding_dimension"]),
    )
    print(json.dumps({key: result[key] for key in ("run_id", "usage_and_cost", "metrics_by_k")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
