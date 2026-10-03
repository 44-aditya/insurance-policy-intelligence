"""Measure unchanged pages using transparent lexical vectors; no model calls."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import re
import statistics
import time

from evaluation.validate_gold_dataset import (
    load_corpus_page_counts, load_extracted_pages, normalize_whitespace, validate_dataset,
)

DEFAULT_CONFIG = Path("evals/retrieval_baseline.config.json")
PLUS_FILE = "Tata_AIG_Medi_Care_Plus_e8a0cf5358.pdf"
PROBLEM_PAGES = {8, 20, 21}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def page_id(document: dict, page: int) -> str:
    """Bind locators to PDF bytes, so another version cannot share an ID."""
    return f"{document['sha256']}:p{page:04d}"


class PageIndex:
    """Sparse TF-IDF vectors over full raw pages, with deterministic tie breaks.

    Tokenization is a vector representation only: we never rewrite, repair,
    reorder, split, or strip furniture from the authoritative page output.
    This lexical control is NOT a pretrained semantic embedding baseline.
    """

    def __init__(self, pages: dict[tuple[str, int], str], pattern: str):
        self.keys = sorted(pages)
        self.pattern = re.compile(pattern)
        counts = [Counter(self.tokens(pages[key])) for key in self.keys]
        df = Counter(term for count in counts for term in count)
        self.idf = {term: math.log((1 + len(counts)) / (1 + freq)) + 1
                    for term, freq in sorted(df.items())}
        self.vectors = [self.vector(count) for count in counts]

    def tokens(self, text: str) -> list[str]:
        return self.pattern.findall(text.lower())

    def vector(self, counts: Counter) -> dict[str, float]:
        values = {term: count * self.idf[term] for term, count in sorted(counts.items())
                  if term in self.idf}
        length = math.sqrt(sum(value * value for value in values.values()))
        return {term: value / length for term, value in values.items()} if length else {}

    def search(self, question: str, k: int) -> list[tuple[tuple[str, int], float]]:
        query = self.vector(Counter(self.tokens(question)))
        scores = [(key, sum(query.get(term, 0.0) * value for term, value in vec.items()))
                  for key, vec in zip(self.keys, self.vectors)]
        # Zero-score pages are not hits; an out-of-vocabulary query must fail
        # visibly instead of producing arbitrary source pages.
        return sorted((item for item in scores if item[1] > 0),
                      key=lambda item: (-item[1], item[0]))[:k]


def assess(record: dict, hits: list[dict], ks: list[int]) -> dict:
    """All distinct annotated pages must be present; partial evidence is visible."""
    gold = {(span["source_file"], span["source_page"]) for span in record["evidence_spans"]}
    sources = {file for file, _ in gold}
    result = {}
    for k in ks:
        selected = hits[:k]
        retrieved = {(hit["source_file"], hit["page_number"]) for hit in selected}
        result[str(k)] = {
            "all_gold_pages_retrieved": gold <= retrieved,
            "gold_page_recall": len(gold & retrieved) / len(gold),
            "wrong_document_count": sum(hit["source_file"] not in sources for hit in selected),
            "missing_gold_pages": [{"source_file": file, "page_number": page}
                                   for file, page in sorted(gold - retrieved)],
        }
    ranks = [hit["rank"] for hit in hits if (hit["source_file"], hit["page_number"]) in gold]
    return {"at_k": result, "reciprocal_rank_at_max_k": 1 / min(ranks) if ranks else 0.0}


def aggregate(rows: list[dict], ks: list[int]) -> dict:
    # Failed attempts stay in the denominator. Empty slices use null, not 0%.
    return {"n": len(rows), "runtime_failures": sum(row["error"] is not None for row in rows),
            "at_k": {str(k): {
                "page_sufficiency_rate": (sum(row["metrics"]["at_k"][str(k)]["all_gold_pages_retrieved"]
                                             for row in rows) / len(rows)) if rows else None,
                "mean_gold_page_recall": statistics.mean(
                    row["metrics"]["at_k"][str(k)]["gold_page_recall"] for row in rows) if rows else None,
                "queries_with_wrong_document": sum(
                    row["metrics"]["at_k"][str(k)]["wrong_document_count"] > 0 for row in rows),
                "wrong_document_results": sum(
                    row["metrics"]["at_k"][str(k)]["wrong_document_count"] for row in rows),
            } for k in ks},
            "mrr_at_max_k": statistics.mean(row["metrics"]["reciprocal_rank_at_max_k"]
                                             for row in rows) if rows else None}


def run(dataset_path: Path, pages_path: Path, metadata_path: Path,
        corpus_dir: Path, config_path: Path, output_dir: Path) -> dict:
    started = time.perf_counter()
    config = json.loads(config_path.read_text())
    # Reject misleading configuration rather than silently ignoring knobs.
    reference = {"backend": "tfidf_cosine_v1", "token_pattern": r"(?u)\b\w\w+\b",
                 "lowercase": True, "term_frequency": "raw_count",
                 "idf": "log((1 + n_pages) / (1 + document_frequency)) + 1",
                 "normalization": "l2", "document_filter": "none"}
    if set(config) != set(reference) | {"ks"} or any(config.get(key) != value for key, value in reference.items()):
        raise ValueError("Unsupported baseline configuration")
    ks = config["ks"]
    if not isinstance(ks, list) or not ks or any(type(k) is not int or k < 1 for k in ks) or ks != sorted(set(ks)):
        raise ValueError("ks must be sorted, unique, positive integers")
    dataset = json.loads(dataset_path.read_text())
    if dataset.get("dataset_status") == "examples_only":
        raise ValueError("examples_only records must not be scored; supply a separate pilot")
    pages = load_extracted_pages(pages_path)
    validation = validate_dataset(dataset, corpus_dir, load_corpus_page_counts(metadata_path), pages)
    if validation.errors or not dataset.get("records"):
        raise ValueError(f"Invalid or empty pilot: {validation.errors}")
    metadata = json.loads(metadata_path.read_text())
    documents = {doc["filename"]: doc for doc in metadata["documents"]}
    for filename, doc in documents.items():
        if digest(corpus_dir / filename) != doc["sha256"]:
            raise ValueError(f"PDF hash mismatch: {filename}")
    expected = {(filename, page) for filename, doc in documents.items()
                for page in range(1, doc["page_count"] + 1)}
    if set(pages) != expected:
        raise ValueError("Extraction pages do not exactly match manifest page coverage")
    index_start = time.perf_counter()
    index = PageIndex(pages, config["token_pattern"])
    index_ms = (time.perf_counter() - index_start) * 1000
    fingerprints = {"dataset": digest(dataset_path), "pages": digest(pages_path),
                    "metadata": digest(metadata_path), "config": digest(config_path),
                    "implementation": digest(Path(__file__)),
                    "validator": digest(Path(__file__).parents[1] / "evaluation/validate_gold_dataset.py")}
    experiment_id = hashlib.sha256(json.dumps(fingerprints, sort_keys=True).encode()).hexdigest()
    rows = []
    for record in dataset["records"]:
        query_start = time.perf_counter()
        error = None
        hits = []
        try:
            ranked = index.search(record["question"], max(ks))
            retrieval_ms = (time.perf_counter() - query_start) * 1000
            for rank, ((file, page), score) in enumerate(ranked, 1):
                doc = documents[file]
                hits.append({"page_id": page_id(doc, page), "source_file": file,
                             "page_number": page, "rank": rank, "score": score,
                             "pdf_sha256": doc["sha256"], "product_name": doc["product_name"],
                             "uin": doc["UIN"], "version": doc["version"],
                             "effective_version_date": doc["effective_version_date"],
                             "text_sha256": hashlib.sha256(pages[file, page].encode()).hexdigest()})
        except Exception as exc:
            # Preserve query-level errors; never discard difficult questions.
            retrieval_ms = (time.perf_counter() - query_start) * 1000
            error = {"type": type(exc).__name__, "message": str(exc)}
        metrics = assess(record, hits, ks)
        gold = {(s["source_file"], s["source_page"]) for s in record["evidence_spans"]}
        mismatch = [s for s in record["evidence_spans"] if normalize_whitespace(s["text"])
                    not in normalize_whitespace(pages[s["source_file"], s["source_page"]])]
        flags = []
        if not hits:
            flags.append("no_positive_score_results")
        if not metrics["at_k"][str(max(ks))]["all_gold_pages_retrieved"]:
            flags.append("missing_gold_page_at_max_k")
        if metrics["at_k"][str(max(ks))]["wrong_document_count"]:
            flags.append("wrong_document_in_top_k")
        if mismatch:
            flags.append("gold_quote_not_found_in_raw_extraction")
        rows.append({"experiment_id": experiment_id, "question_id": record["question_id"],
                     "question": record["question"], "question_type": record["question_type"],
                     "evidence_format": record["evidence_format"], "difficulty": record["difficulty"],
                     "retrieved_pages": hits, "metrics": metrics, "retrieval_latency_ms": retrieval_ms,
                     "query_wall_latency_ms": (time.perf_counter() - query_start) * 1000,
                     "token_usage": {"embedding_input_tokens": 0, "llm_input_tokens": 0,
                                     "llm_output_tokens": 0, "tokenizer": "not_applicable_no_model_calls",
                                     "lexical_query_terms": len(index.tokens(record["question"]))},
                     "paid_api_cost_usd": 0.0, "error": error, "failure_flags": flags,
                     "slices": {"table_dependent": record["evidence_format"] in {"table", "mixed"},
                                "plus_problem_pages": any(file == PLUS_FILE and page in PROBLEM_PAGES
                                                          for file, page in gold)},
                     "version_assessment": "not_testable_no_alternate_versions_and_unknown_dates"})
    latencies = sorted(row["retrieval_latency_ms"] for row in rows)
    summary = {"experiment_id": experiment_id, "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
               "fingerprints": fingerprints, "python": platform.python_version(), "config": config,
               "dataset_status": dataset["dataset_status"], "pages_indexed": len(pages),
               "metric_kind": "interim_all_annotated_pages_proxy_not_passage_or_answer_recall",
               "aggregate": aggregate(rows, ks),
               "slices": {name: aggregate([row for row in rows if row["slices"][name]], ks)
                          for name in ("table_dependent", "plus_problem_pages")},
               "version_slice": {"status": "not_testable", "alternate_versions": 0,
                                 "reason": "One PDF per product; version/effective dates unknown. PDF hashes identify bytes only."},
               "extraction_warnings": validation.warnings,
               "index_build_latency_ms": index_ms,
               "retrieval_latency_ms": {"p50": statistics.median(latencies),
                                        "p95_nearest_rank": latencies[math.ceil(.95 * len(latencies)) - 1]},
               "environment": {"concurrency": 1, "repetitions": 1, "index_state": "warm_after_one_cold_build",
                               "network_calls": 0, "retries": 0},
               "token_usage": {"embedding_input_tokens": 0, "llm_input_tokens": 0, "llm_output_tokens": 0},
               "cost_per_experiment": {"currency": "USD", "paid_api_cost": 0.0,
                                       "ingestion_paid_api_cost": 0.0, "query_paid_api_cost": 0.0,
                                       "grader_paid_api_cost": 0.0, "attempted_queries": len(rows),
                                       "successful_queries": sum(row["error"] is None for row in rows),
                                       "paid_api_cost_per_successful_query": 0.0 if any(row["error"] is None for row in rows) else None,
                                       "compute_cost": None, "human_review_cost": None,
                                       "accounting": "No metered APIs. Local compute and human time unpriced; total cost not zero."},
               "experiment_wall_latency_ms": (time.perf_counter() - started) * 1000}
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "query_results.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    (output_dir / "experiment_metrics.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    (output_dir / "baseline_report.md").write_text(report(summary, rows), encoding="utf-8")
    return summary


def report(summary: dict, rows: list[dict]) -> str:
    ks = summary["config"]["ks"]
    lines = ["# Page retrieval baseline", "",
             "Local TF-IDF/cosine lexical vector control; not a pretrained semantic embedding experiment.",
             f"{summary['pages_indexed']} unchanged pages; {len(rows)} {summary['dataset_status']} pilot questions.",
             "Draft labels are provisional and source-selected; these results are diagnostic, not a reviewed benchmark.",
             "Examples-only records are refused. No cleanup, document filtering, reranking, fine-tuning, or generation.", "",
             "Interim proxy: fraction of questions retrieving ALL distinct annotated PDF pages in top K.",
             "This overestimates usable evidence when tables/words are damaged, and ignores alternative sufficient evidence sets.",
             "Wrong-document counts mean pages outside the annotated source files; they are distractor diagnostics, not relevance judgments.", "",
             "| Slice | n | " + " | ".join(f"Page sufficiency@{k}" for k in ks) + " |",
             "| --- | ---: | " + " | ".join("---:" for _ in ks) + " |"]
    for name, value in [("All", summary["aggregate"]), *summary["slices"].items()]:
        values = [value["at_k"][str(k)]["page_sufficiency_rate"] for k in ks]
        lines.append(f"| {name} | {value['n']} | " + " | ".join(
            f"{v:.1%}" if v is not None else "N/A" for v in values) + " |")
    lines += ["", f"MRR at max K: {summary['aggregate']['mrr_at_max_k']:.3f} (first gold page only).",
              "", "| Question | First gold rank | Missing gold pages at max K | Wrong-document hits at max K |",
              "| --- | ---: | --- | ---: |"]
    for row in rows:
        m = row["metrics"]["at_k"][str(max(ks))]
        rr = row["metrics"]["reciprocal_rank_at_max_k"]
        missing = ", ".join(f"{p['source_file']} p{p['page_number']}" for p in m["missing_gold_pages"]) or "none"
        lines.append(f"| {row['question_id']} | {round(1/rr) if rr else 'not retrieved'} | {missing} | {m['wrong_document_count']} |")
    lines += ["", "Version retrieval: **not testable**. Only one file per product; all explicit versions/dates are null.",
              "Hash-based page IDs distinguish PDF bytes but do not prove currentness. Wrong-product retrieval is measured without gold-derived filtering.",
              "MediCare Plus pages 8/21 contain spurious characters; page 20 interleaves table/prose. Retrieving these pages does not fix their fidelity.",
              f"Extraction quote warnings: {len(summary['extraction_warnings'])}; runtime failures: {summary['aggregate']['runtime_failures']}.",
              "", f"Retrieval p50 / p95: {summary['retrieval_latency_ms']['p50']:.3f} / {summary['retrieval_latency_ms']['p95_nearest_rank']:.3f} ms.",
              f"Cold index build: {summary['index_build_latency_ms']:.3f} ms; concurrency 1, one repetition, local warm queries.",
              "Embedding and LLM input/output tokens: 0 (no model called). Lexical term counts are separate, not model tokens.",
              "Paid API cost per experiment: USD 0.00. Compute and human review cost: unknown/unpriced. No claim of zero total cost.",
              "Answer correctness, faithfulness, citation entailment, and generation latency are unmeasured.",
              "", "Next experiment: independently review/expand pilot labels, then compare a pinned semantic embedding model on the same pages and questions.",
              "Keep extraction unchanged so any gain is attributable to retrieval. Inspect table fidelity before treating page hits as usable evidence.",
              "", f"Experiment ID: `{summary['experiment_id']}`. Fingerprints and run accounting are in experiment_metrics.json.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("evals/retrieval_pilot.draft.json"))
    parser.add_argument("--pages", type=Path, default=Path("artifacts/extraction/policy_pages.jsonl"))
    parser.add_argument("--metadata", type=Path, default=Path("corpus/metadata.json"))
    parser.add_argument("--corpus-dir", type=Path, default=Path("corpus/policy_wordings"))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/retrieval/baseline"))
    args = parser.parse_args()
    try:
        result = run(args.dataset, args.pages, args.metadata, args.corpus_dir, args.config, args.output_dir)
    except (OSError, ValueError, KeyError, TypeError) as error:
        # Structural/index failures exit nonzero, rather than publishing a score.
        print(f"Baseline failed: {type(error).__name__}: {error}")
        return 1
    print(f"Baseline complete: {result['experiment_id']} ({result['aggregate']['n']} queries)")
    return 1 if result["aggregate"]["runtime_failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
