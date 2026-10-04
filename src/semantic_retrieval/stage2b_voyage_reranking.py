"""Controlled Stage 2B Voyage rerank-3 experiment over frozen Stage 1 candidates."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol, Sequence

from evaluation.contract_v2 import score_unit


EXPECTED_QUESTION_IDS = {f"Q{number:03d}" for number in range(1, 40)}
KNOWN_RESCUABLE = ("Q017 U2", "Q030 U1", "Q002 U2", "Q031 U1", "Q034 U1")
KNOWN_UNREACHABLE = {"Q037 U2": 40, "Q014 U2": 41, "Q008 U4": 106}


@dataclass(frozen=True)
class RerankResponse:
    """Provider-neutral representation of a complete reranking response."""

    results: Sequence[tuple[int, float]]
    total_tokens: int | None
    returned_model: str | None = None


class Reranker(Protocol):
    def rerank(self, query: str, documents: Sequence[str]) -> RerankResponse: ...


class VoyageReranker:
    """Official Voyage SDK adapter; the API key is read from the environment."""

    def __init__(self, config: dict[str, Any]) -> None:
        import voyageai

        self._model = config["model"]
        self._truncation = config["truncation"]
        self._client = voyageai.Client(
            api_key=os.environ["VOYAGE_API_KEY"],
            max_retries=config["client_max_retries"],
            timeout=config["client_timeout_seconds"],
        )

    def rerank(self, query: str, documents: Sequence[str]) -> RerankResponse:
        response = self._client.rerank(
            query=query,
            documents=list(documents),
            model=self._model,
            top_k=None,  # Require scores for all 30; never let the provider drop candidates.
            truncation=self._truncation,
        )
        return RerankResponse(
            results=[(int(item.index), float(item.relevance_score)) for item in response.results],
            total_tokens=getattr(response, "total_tokens", None),
            returned_model=getattr(response, "model", None),
        )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _positive_records(contract: dict[str, Any]) -> list[dict[str, Any]]:
    return [record for record in contract["records"] if record.get("evaluation_mode") != "negative_space"]


def _score(
    records: list[dict[str, Any]],
    rankings: dict[str, list[dict[str, Any]]],
    chunk_text: dict[str, str],
    page_text: dict[tuple[str, int], str],
) -> tuple[dict[str, Any], dict[tuple[str, str], dict[str, Any]]]:
    details: list[dict[str, Any]] = []
    outcomes: dict[tuple[str, str], dict[str, Any]] = {}
    for record in records:
        required = [unit for unit in record["evidence_units"] if unit["required"]]
        scored = [score_unit(unit, rankings[record["question_id"]], chunk_text, page_text) for unit in required]
        for unit in scored:
            outcomes[(record["question_id"], unit["unit_id"])] = unit
        details.append({
            "question_id": record["question_id"],
            "covered_required_units": sum(unit["matched"] for unit in scored),
            "required_units": len(scored),
            "sufficient_evidence": all(unit["matched"] for unit in scored),
            "evidence_units": scored,
        })
    required_count = len(outcomes)
    covered = sum(unit["matched"] for unit in outcomes.values())
    sufficient = sum(question["sufficient_evidence"] for question in details)
    return ({
        "evaluated_questions": len(records),
        "required_evidence_units": required_count,
        "covered_evidence_units": covered,
        "atomic_evidence_recall_at_10": covered / required_count,
        "sufficient_evidence_questions": sufficient,
        "sufficient_evidence_at_10": sufficient / len(records),
        "questions": details,
    }, outcomes)


def _witness_ranks(unit: dict[str, Any]) -> list[int]:
    return sorted({witness["rank"] for fragment in unit["fragments"] for witness in fragment["witnesses"]})


def _validate_response(response: RerankResponse, count: int) -> list[tuple[int, float]]:
    results = list(response.results)
    indices = [index for index, _ in results]
    if len(results) != count or sorted(indices) != list(range(count)):
        raise ValueError(
            f"reranker must return every candidate exactly once; expected indices 0..{count - 1}, got {indices}"
        )
    if not all(math.isfinite(score) for _, score in results):
        raise ValueError("reranker returned a non-finite score")
    if response.total_tokens is not None and response.total_tokens < 0:
        raise ValueError("reranker returned invalid token usage")
    return results


def run_experiment(
    config: dict[str, Any],
    full_rankings: dict[str, Any],
    chunks: list[dict[str, Any]],
    pages: list[dict[str, Any]],
    contract: dict[str, Any],
    *,
    reranker: Reranker,
) -> dict[str, Any]:
    """Rerank exactly the frozen Top-30 and evaluate the final Top-10."""
    if (config["candidate_depth"], config["final_depth"]) != (30, 10):
        raise ValueError("controlled Stage 2B requires candidate_depth=30 and final_depth=10")
    if config["model"] != "rerank-3":
        raise ValueError("controlled Stage 2B requires model=rerank-3")
    if full_rankings.get("status") != "completed":
        raise ValueError("Stage 1 full-ranking artifact is not completed")
    stage1_configuration = full_rankings.get("configuration", {})
    mismatches = {
        key: {"expected": value, "actual": stage1_configuration.get(key)}
        for key, value in config["required_stage1_configuration"].items()
        if stage1_configuration.get(key) != value
    }
    if mismatches:
        raise ValueError(f"Stage 1 artifact configuration is not frozen Voyage-4: {mismatches}")

    records = _positive_records(contract)
    record_ids = [record["question_id"] for record in records]
    if len(record_ids) != 39 or set(record_ids) != EXPECTED_QUESTION_IDS:
        raise ValueError("Evaluation Contract v2 must contain exactly positive questions Q001-Q039")
    questions = full_rankings.get("questions", [])
    by_question = {question["question_id"]: question for question in questions}
    if len(questions) != 39 or set(by_question) != EXPECTED_QUESTION_IDS:
        raise ValueError("Stage 1 rankings must contain exactly Q001-Q039 (Q040 excluded)")

    chunk_by_id = {chunk["chunk_id"]: chunk for chunk in chunks}
    if len(chunk_by_id) != len(chunks):
        raise ValueError("chunk artifact contains duplicate chunk_id values")
    chunk_text = {chunk_id: chunk["text"] for chunk_id, chunk in chunk_by_id.items()}
    page_text = {(page["source_file"], page["page_number"]): page["text"] for page in pages}
    baseline: dict[str, list[dict[str, Any]]] = {}
    candidate_pool: dict[str, list[dict[str, Any]]] = {}

    # Validate all frozen inputs and both baseline ceilings before making any paid calls.
    for question_id in sorted(EXPECTED_QUESTION_IDS):
        retrieved = by_question[question_id].get("retrieved", [])
        if len(retrieved) < 30:
            raise ValueError(f"{question_id} has {len(retrieved)} candidates; at least 30 are required")
        candidates = retrieved[:30]
        if [item.get("rank") for item in candidates] != list(range(1, 31)):
            raise ValueError(f"{question_id} candidates are not contiguous Stage 1 ranks 1..30")
        if any("cosine_similarity" not in item for item in candidates):
            raise ValueError(f"{question_id} candidate is missing its original cosine score")
        unknown = [item["chunk_id"] for item in candidates if item["chunk_id"] not in chunk_by_id]
        if unknown:
            raise ValueError(f"{question_id} rankings reference unknown chunks: {unknown}")
        baseline[question_id] = candidates[:10]
        candidate_pool[question_id] = candidates

    baseline_metrics, before = _score(records, baseline, chunk_text, page_text)
    ceiling_metrics, _ = _score(records, candidate_pool, chunk_text, page_text)
    actual = (
        baseline_metrics["covered_evidence_units"],
        baseline_metrics["sufficient_evidence_questions"],
        ceiling_metrics["covered_evidence_units"],
        ceiling_metrics["sufficient_evidence_questions"],
    )
    frozen = config["frozen_stage1_counts"]
    expected = (
        frozen["top_10_covered_units"], frozen["top_10_sufficient_questions"],
        frozen["top_30_covered_units"], frozen["top_30_sufficient_questions"],
    )
    if actual != expected:
        raise ValueError(
            "Stage 1 artifact does not reproduce frozen Contract v2 counts "
            f"(Top-10 covered/sufficient, Top-30 covered/sufficient): {actual}; expected {expected}"
        )
    units_by_key = {
        (record["question_id"], unit["unit_id"]): unit
        for record in records for unit in record["evidence_units"] if unit["required"]
    }
    for label, expected_rank in config.get("expected_first_cover_ranks", {}).items():
        key = tuple(label.split())
        if key not in units_by_key:
            raise ValueError(f"frozen evidence unit is absent from Contract v2: {label}")
        retrieved = by_question[key[0]]["retrieved"]
        if len(retrieved) < expected_rank:
            raise ValueError(f"{label} requires rank {expected_rank}, but the artifact ends at {len(retrieved)}")
        observed_rank = next((
            rank for rank in range(1, len(retrieved) + 1)
            if score_unit(units_by_key[key], retrieved[:rank], chunk_text, page_text)["matched"]
        ), None)
        if observed_rank != expected_rank:
            raise ValueError(
                f"{label} first-cover rank is {observed_rank}; expected frozen rank {expected_rank}"
            )

    reranked: dict[str, list[dict[str, Any]]] = {}
    question_runs: list[dict[str, Any]] = []
    total_latency_ms = 0.0
    total_tokens = 0
    all_usage_reported = True
    returned_models: set[str] = set()
    for record in records:
        question_id = record["question_id"]
        source = by_question[question_id]
        query = source.get("query_text")
        if not isinstance(query, str) or not query.strip():
            raise ValueError(f"{question_id} is missing its original query_text")
        candidates = candidate_pool[question_id]
        documents = [chunk_by_id[item["chunk_id"]]["text"] for item in candidates]
        started = time.perf_counter()
        response = reranker.rerank(query, documents)
        latency_ms = (time.perf_counter() - started) * 1000
        results = _validate_response(response, 30)
        score_by_index = dict(results)
        # The explicit secondary key makes provider ties reproducible.
        ordered = sorted(enumerate(candidates), key=lambda pair: (-score_by_index[pair[0]], pair[1]["rank"]))
        all_candidates = [
            {
                **candidate,
                "stage1_rank": candidate["rank"],
                "stage1_cosine_similarity": candidate["cosine_similarity"],
                "rerank_score": score_by_index[index],
                "reranked_rank": rank,
                "rank": rank,
            }
            for rank, (index, candidate) in enumerate(ordered, 1)
        ]
        reranked[question_id] = all_candidates[:10]
        total_latency_ms += latency_ms
        if response.total_tokens is None:
            all_usage_reported = False
        else:
            total_tokens += response.total_tokens
        if response.returned_model:
            returned_models.add(response.returned_model)
        question_runs.append({
            "question_id": question_id,
            "query_text": query,
            "latency_ms": latency_ms,
            "provider_reported_tokens": response.total_tokens,
            "candidates": all_candidates,
            "final_top_10_chunk_ids": [item["chunk_id"] for item in all_candidates[:10]],
        })

    reranked_metrics, after = _score(records, reranked, chunk_text, page_text)
    unit_changes = []
    for key, old in before.items():
        new = after[key]
        if old["matched"] != new["matched"]:
            unit_changes.append({
                "question_id": key[0], "unit_id": key[1],
                "change": "rescued" if new["matched"] else "lost",
                "stage1_matched": old["matched"], "stage2b_matched": new["matched"],
                "stage1_witness_ranks": _witness_ranks(old),
                "stage2b_witness_ranks": _witness_ranks(new),
            })
    rescued = [change for change in unit_changes if change["change"] == "rescued"]
    lost = [change for change in unit_changes if change["change"] == "lost"]
    old_sufficient = {q["question_id"]: q["sufficient_evidence"] for q in baseline_metrics["questions"]}
    new_sufficient = {q["question_id"]: q["sufficient_evidence"] for q in reranked_metrics["questions"]}
    becoming_sufficient = sorted(qid for qid in old_sufficient if not old_sufficient[qid] and new_sufficient[qid])
    becoming_insufficient = sorted(qid for qid in old_sufficient if old_sufficient[qid] and not new_sufficient[qid])
    change_by_unit = {f'{item["question_id"]} {item["unit_id"]}': item for item in unit_changes}
    known_rescuable_outcomes = {}
    for label in KNOWN_RESCUABLE:
        key = tuple(label.split())
        if label in change_by_unit:
            known_rescuable_outcomes[label] = change_by_unit[label]
        elif key in after:
            known_rescuable_outcomes[label] = {
                "change": "already_covered" if after[key]["matched"] else "still_missing"
            }
        else:  # Supports narrowly scoped synthetic contracts used by no-network tests.
            known_rescuable_outcomes[label] = {"change": "not_present_in_contract"}
    measured_tokens = total_tokens if all_usage_reported else None
    estimated_cost = None if measured_tokens is None else measured_tokens * config["price_usd_per_million_tokens"] / 1_000_000
    net_change = len(rescued) - len(lost)
    clear_quality_improvement = (
        reranked_metrics["covered_evidence_units"] > baseline_metrics["covered_evidence_units"]
        and reranked_metrics["sufficient_evidence_questions"] >= baseline_metrics["sufficient_evidence_questions"]
    )
    return {
        "status": "completed",
        "run_id": f"stage2b-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "architecture": "frozen Stage 1 Voyage-4 Top-30 -> Voyage rerank-3 -> Top-10",
        "configuration": config,
        "software": {"python": platform.python_version()},
        "evaluation_contract_version": "2.0",
        "negative_space_excluded": ["Q040"],
        "stage1_top_10": baseline_metrics,
        "stage1_top_30_candidate_ceiling": ceiling_metrics,
        "stage2b_reranked_top_10": reranked_metrics,
        "quality_changes": {
            "rescued_units": rescued, "lost_units": lost,
            "net_evidence_unit_change": net_change,
            "questions_becoming_sufficient": becoming_sufficient,
            "questions_becoming_insufficient": becoming_insufficient,
        },
        "known_top_30_rescuable_outcomes": known_rescuable_outcomes,
        "unreachable_evidence_units": [
            {"evidence_unit": label, "stage1_rank": rank, "reason": "outside frozen Top-30 candidate set"}
            for label, rank in KNOWN_UNREACHABLE.items()
        ],
        "known_representation_complication": "Q034 U1 crosses a page boundary; reranking cannot repair its representation.",
        "reranking_latency": {
            "total_ms": total_latency_ms,
            "mean_per_query_ms": total_latency_ms / len(records),
            "measurement_scope": "Voyage rerank calls only; excludes artifact validation and I/O",
        },
        "usage_and_cost": {
            "questions": len(records), "query_document_pairs": len(records) * 30,
            "successful_api_requests": len(records),
            "configured_max_retries_per_request": config["client_max_retries"],
            "observed_retry_count": None,
            "observed_retry_count_note": "The Voyage SDK does not expose retry counts in the rerank response.",
            "provider_reported_total_tokens": measured_tokens,
            "usage_complete": all_usage_reported,
            "price_usd_per_million_tokens": config["price_usd_per_million_tokens"],
            "pricing_source": config["pricing_source"],
            "estimated_list_price_usd": estimated_cost,
            "estimated_incremental_cost_per_query_usd": None if estimated_cost is None else estimated_cost / len(records),
            "actual_billed_cost_usd": None,
            "actual_billed_cost_note": "Billing data is not available from the rerank response.",
        },
        "api_model_metadata": {"requested_model": config["model"], "response_models": sorted(returned_models)},
        "failures": [],
        "decision": {
            "clear_net_quality_improvement": clear_quality_improvement,
            "verdict": "quality_improved_pending_latency_cost_judgment" if clear_quality_improvement else "stage2b_not_successful",
            "note": "Success also requires owner judgment that measured latency, cost, and complexity are acceptable.",
        },
        "questions": question_runs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/stage2b_voyage_rerank3.json"))
    parser.add_argument("--rankings", type=Path, default=Path("artifacts/retrieval/stage1_voyage4_diagnostics/20261004_full360/full_rankings.json"))
    parser.add_argument("--chunks", type=Path, default=Path("artifacts/retrieval/stage1_voyage4/chunks.jsonl"))
    parser.add_argument("--pages", type=Path, default=Path("artifacts/extraction/policy_pages.jsonl"))
    parser.add_argument("--contract", type=Path, default=Path("evals/evaluation_contract_v2.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    inputs = [args.config, args.rankings, args.chunks, args.pages, args.contract]
    result: dict[str, Any]
    try:
        missing = [str(path) for path in inputs if not path.is_file()]
        if missing:
            raise FileNotFoundError(f"required experiment inputs are missing: {missing}")
        if not os.environ.get("VOYAGE_API_KEY"):
            raise RuntimeError("VOYAGE_API_KEY is required for the Voyage rerank-3 experiment")
        config = json.loads(args.config.read_text(encoding="utf-8"))
        result = run_experiment(
            config,
            json.loads(args.rankings.read_text(encoding="utf-8")),
            _read_jsonl(args.chunks), _read_jsonl(args.pages),
            json.loads(args.contract.read_text(encoding="utf-8")),
            reranker=VoyageReranker(config),
        )
        result["inputs"] = {str(path): _sha256(path) for path in inputs}
    except Exception as error:
        result = {
            "status": "blocked", "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "error_type": type(error).__name__, "error": str(error),
            "fabricated_results": False,
            "api_usage": None,
            "recovery": "Supply the frozen full_rankings.json, export VOYAGE_API_KEY, and rerun the documented Stage 2B command.",
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("status", "error") if key in result}, indent=2))
    return 0 if result["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
