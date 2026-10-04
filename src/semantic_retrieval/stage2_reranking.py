"""Controlled Stage 2 reranking of immutable Stage 1 Top-30 candidates."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol, Sequence

from evaluation.contract_v2 import score_unit


class Reranker(Protocol):
    def predict(self, pairs: Sequence[tuple[str, str]]) -> Sequence[float]: ...


class MiniLMCrossEncoder:
    """Lazy local-model adapter; importing the module never downloads a model."""

    def __init__(self, config: dict[str, Any]) -> None:
        from sentence_transformers import CrossEncoder

        self._model = CrossEncoder(
            config["model"],
            revision=config["model_revision"],
            max_length=config["max_length"],
            device=config["device"],
        )
        self._batch_size = config["batch_size"]

    def predict(self, pairs: Sequence[tuple[str, str]]) -> Sequence[float]:
        return self._model.predict(
            list(pairs), batch_size=self._batch_size, show_progress_bar=False
        )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _positive_records(contract: dict[str, Any]) -> list[dict[str, Any]]:
    return [r for r in contract["records"] if r.get("evaluation_mode") != "negative_space"]


def _score(
    records: list[dict[str, Any]],
    rankings: dict[str, list[dict[str, Any]]],
    chunk_text: dict[str, str],
    page_text: dict[tuple[str, int], str],
) -> tuple[dict[str, Any], dict[tuple[str, str], bool]]:
    covered = sufficient = 0
    outcomes: dict[tuple[str, str], bool] = {}
    details: list[dict[str, Any]] = []
    for record in records:
        units = [u for u in record["evidence_units"] if u["required"]]
        scored = [score_unit(u, rankings[record["question_id"]], chunk_text, page_text) for u in units]
        for item in scored:
            outcomes[(record["question_id"], item["unit_id"])] = item["matched"]
        question_covered = sum(item["matched"] for item in scored)
        question_sufficient = all(item["matched"] for item in scored)
        covered += question_covered
        sufficient += int(question_sufficient)
        details.append({
            "question_id": record["question_id"],
            "covered_required_units": question_covered,
            "required_units": len(scored),
            "sufficient_evidence": question_sufficient,
            "evidence_units": scored,
        })
    required = len(outcomes)
    return ({
        "evaluated_questions": len(records),
        "required_evidence_units": required,
        "covered_evidence_units": covered,
        "atomic_evidence_recall_at_10": covered / required,
        "sufficient_evidence_questions": sufficient,
        "sufficient_evidence_at_10": sufficient / len(records),
        "questions": details,
    }, outcomes)


def run_experiment(
    config: dict[str, Any],
    full_rankings: dict[str, Any],
    chunks: list[dict[str, Any]],
    pages: list[dict[str, Any]],
    contract: dict[str, Any],
    *,
    reranker: Reranker,
) -> dict[str, Any]:
    """Rerank exactly 30 candidates and score both arms with Contract v2."""
    candidate_depth, final_depth = config["candidate_depth"], config["final_depth"]
    if (candidate_depth, final_depth) != (30, 10):
        raise ValueError("controlled experiment requires candidate_depth=30 and final_depth=10")
    if full_rankings.get("status") != "completed":
        raise ValueError("Stage 1 full-ranking artifact is not completed")

    records = _positive_records(contract)
    by_question = {q["question_id"]: q for q in full_rankings.get("questions", [])}
    expected_ids = {r["question_id"] for r in records}
    if set(by_question) != expected_ids or len(full_rankings.get("questions", [])) != len(expected_ids):
        raise ValueError("Stage 1 rankings must contain exactly the 39 positive questions (Q040 excluded)")
    chunk_by_id = {c["chunk_id"]: c for c in chunks}
    chunk_text = {chunk_id: c["text"] for chunk_id, c in chunk_by_id.items()}
    page_text = {(p["source_file"], p["page_number"]): p["text"] for p in pages}
    baseline: dict[str, list[dict[str, Any]]] = {}
    reranked: dict[str, list[dict[str, Any]]] = {}
    question_runs: list[dict[str, Any]] = []
    total_latency = 0.0

    for record in records:
        source = by_question[record["question_id"]]
        retrieved = source.get("retrieved", [])
        if len(retrieved) < candidate_depth:
            raise ValueError(
                f'{record["question_id"]} has {len(retrieved)} candidates; exactly 30 are required'
            )
        candidates = retrieved[:candidate_depth]
        if [c["rank"] for c in candidates] != list(range(1, candidate_depth + 1)):
            raise ValueError(f'{record["question_id"]} candidates are not contiguous Stage 1 ranks 1..30')
        try:
            texts = [chunk_by_id[c["chunk_id"]]["text"] for c in candidates]
        except KeyError as error:
            raise ValueError(f"ranking references unknown chunk: {error.args[0]}") from error
        started = time.perf_counter()
        scores = [float(v) for v in reranker.predict(list(zip([source["query_text"]] * 30, texts)))]
        latency = (time.perf_counter() - started) * 1000
        if len(scores) != candidate_depth:
            raise ValueError(f"reranker returned {len(scores)} scores; expected 30")
        if not all(math.isfinite(score) for score in scores):
            raise ValueError("reranker returned a non-finite score")
        # Original rank is the explicit deterministic tie-breaker.
        ordered = sorted(zip(candidates, scores), key=lambda pair: (-pair[1], pair[0]["rank"]))
        final = [
            {**candidate, "stage1_rank": candidate["rank"], "rank": rank, "reranker_score": score}
            for rank, (candidate, score) in enumerate(ordered[:final_depth], 1)
        ]
        baseline[record["question_id"]] = candidates[:final_depth]
        reranked[record["question_id"]] = final
        total_latency += latency
        question_runs.append({
            "question_id": record["question_id"], "latency_ms": latency,
            "input_candidates": candidate_depth, "output_candidates": final_depth,
            "reranked_top_10": final,
        })

    candidate_metrics, _ = _score(
        records,
        {question_id: by_question[question_id]["retrieved"][:candidate_depth]
         for question_id in expected_ids},
        chunk_text,
        page_text,
    )
    baseline_metrics, before = _score(records, baseline, chunk_text, page_text)
    reranked_metrics, after = _score(records, reranked, chunk_text, page_text)
    measured_counts = (
        baseline_metrics["covered_evidence_units"],
        baseline_metrics["sufficient_evidence_questions"],
        candidate_metrics["covered_evidence_units"],
    )
    expected = config.get("frozen_stage1_counts")
    expected_counts = None if expected is None else (
        expected["top_10_covered_units"], expected["top_10_sufficient_questions"],
        expected["top_30_covered_units"],
    )
    if expected_counts is not None and measured_counts != expected_counts:
        raise ValueError(
            "Stage 1 artifact does not reproduce frozen Contract v2 counts "
            f"(Top-10 covered, Top-10 sufficient, Top-30 covered): {measured_counts}"
        )
    changes = [
        {"question_id": qid, "unit_id": uid, "stage1_matched": matched,
         "stage2_matched": after[(qid, uid)],
         "change": "rescued" if not matched and after[(qid, uid)] else "lost"}
        for (qid, uid), matched in before.items() if matched != after[(qid, uid)]
    ]
    return {
        "status": "completed",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "architecture": "immutable Stage 1 Top-30 -> local cross-encoder -> Top-10",
        "configuration": config,
        "software": {"python": platform.python_version()},
        "evaluation_contract_version": "2.0",
        "negative_space_excluded": ["Q040"],
        "stage1_top_10": baseline_metrics,
        "stage1_top_30_candidate_ceiling": candidate_metrics,
        "stage2_reranked_top_10": reranked_metrics,
        "unit_changes": changes,
        "rescued_units": [c for c in changes if c["change"] == "rescued"],
        "lost_units": [c for c in changes if c["change"] == "lost"],
        "reranking_latency": {
            "total_ms": total_latency,
            "mean_per_query_ms": total_latency / len(records),
            "measurement_scope": "predict calls only; excludes model load and artifact I/O",
        },
        "usage_and_cost": {
            "pairs_scored": len(records) * candidate_depth,
            "api_calls": 0, "api_tokens": None,
            "estimated_api_cost_usd": 0.0,
            "estimated_incremental_api_cost_per_query_usd": 0.0,
            "local_compute_cost_usd": None,
            "note": "Local compute was not priced; wall-clock latency is reported instead.",
        },
        "failures": [],
        "candidate_depth_limitation": "Evidence below Stage 1 rank 30 cannot be rescued; Q008 U4 at rank 106 is unreachable.",
        "known_representation_complication": "Q034 U1 crosses a page boundary; reranking does not repair its representation.",
        "questions": question_runs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/stage2_minilm_reranker.json"))
    parser.add_argument("--rankings", type=Path, required=True)
    parser.add_argument("--chunks", type=Path, default=Path("artifacts/retrieval/stage1_voyage4/chunks.jsonl"))
    parser.add_argument("--pages", type=Path, default=Path("artifacts/extraction/policy_pages.jsonl"))
    parser.add_argument("--contract", type=Path, default=Path("evals/evaluation_contract_v2.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    inputs = [args.config, args.rankings, args.chunks, args.pages, args.contract]
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        result = run_experiment(
            config, json.loads(args.rankings.read_text(encoding="utf-8")),
            _read_jsonl(args.chunks), _read_jsonl(args.pages),
            json.loads(args.contract.read_text(encoding="utf-8")),
            reranker=MiniLMCrossEncoder(config),
        )
        result["inputs"] = {str(path): _sha256(path) for path in inputs}
    except Exception as error:
        result = {
            "status": "blocked", "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "error_type": type(error).__name__, "error": str(error),
            "fabricated_results": False,
            "recovery": "Provide the completed Stage 1 full_rankings.json and rerun the same command; install .[stage2] and allow the pinned model's one-time download if it is not cached.",
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "error") if k in result}, indent=2))
    return 0 if result["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
