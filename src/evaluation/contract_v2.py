"""Deterministic Evaluation Contract v2 scoring over stored retrieval rankings."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any


K_VALUES = (1, 3, 5, 10)


def canonicalize(text: str) -> str:
    """Preserve letters/numbers while removing extraction-only boundaries.

    Compact canonicalization intentionally does not rewrite words, numbers, or
    negation. It only removes format characters, normalizes quote/dash variants,
    case, and punctuation/spacing that PDF extraction may insert inside words.
    """
    text = unicodedata.normalize("NFKC", text).casefold().replace("\u00ad", "")
    text = text.translate(
        str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-"})
    )
    return "".join(character for character in text if character.isalnum())


def _interval(text: str, needle: str) -> tuple[int, int] | None:
    start = text.find(needle)
    return None if start < 0 else (start, start + len(needle))


def fragment_witnesses(
    fragment: dict[str, Any],
    retrieved: list[dict[str, Any]],
    chunk_text: dict[str, str],
    page_text: dict[tuple[str, int], str],
) -> dict[str, Any]:
    """Return exact, source-anchored collective coverage for one fragment."""
    source = fragment["source_file"]
    page = fragment["source_page"]
    normalized_page = canonicalize(page_text.get((source, page), ""))
    # ``extraction_text`` is allowed only as an explicit, reviewable locator for
    # known parser corruption; ``text`` remains authoritative source truth.
    normalized_fragment = canonicalize(fragment.get("extraction_text", fragment["text"]))
    target = _interval(normalized_page, normalized_fragment)
    witnesses: list[dict[str, Any]] = []
    covered_ranges: list[tuple[int, int]] = []
    if target:
        for result in retrieved:
            if result["source_file"] != source or result["page_number"] != page:
                continue
            chunk_id = result["chunk_id"]
            chunk_range = _interval(normalized_page, canonicalize(chunk_text[chunk_id]))
            if not chunk_range:
                continue
            overlap = (max(target[0], chunk_range[0]), min(target[1], chunk_range[1]))
            if overlap[0] < overlap[1]:
                covered_ranges.append(overlap)
                witnesses.append({"chunk_id": chunk_id, "rank": result["rank"]})
    cursor = target[0] if target else 0
    for start, end in sorted(covered_ranges):
        if start > cursor:
            break
        cursor = max(cursor, end)
    return {
        "matched": bool(target and cursor >= target[1]),
        "witnesses": witnesses,
        "source_interval": list(target) if target else None,
        "mapping_status": "mapped" if target else "authoritative_fragment_not_in_extraction",
    }


def score_unit(
    unit: dict[str, Any],
    retrieved: list[dict[str, Any]],
    chunk_text: dict[str, str],
    page_text: dict[tuple[str, int], str],
) -> dict[str, Any]:
    fragments = [
        fragment_witnesses(fragment, retrieved, chunk_text, page_text)
        for fragment in unit["source_fragments"]
    ]
    return {
        "unit_id": unit["unit_id"],
        "required": unit["required"],
        "matched": all(fragment["matched"] for fragment in fragments),
        "fragments": fragments,
    }


def rescore(
    contract: dict[str, Any],
    stored_results: dict[str, Any],
    chunks: list[dict[str, Any]],
    pages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Score v2 without embedding or retrieval calls."""
    questions = {item["question_id"]: item for item in stored_results["questions"]}
    chunk_text = {item["chunk_id"]: item["text"] for item in chunks}
    page_text = {(item["source_file"], item["page_number"]): item["text"] for item in pages}
    per_question: list[dict[str, Any]] = []
    aggregates: dict[str, Any] = {}
    for k in K_VALUES:
        required_total = covered_total = sufficient_total = evaluated = 0
        for record in contract["records"]:
            if record.get("evaluation_mode") == "negative_space":
                continue
            required = [unit for unit in record["evidence_units"] if unit["required"]]
            scored = [
                score_unit(unit, questions[record["question_id"]]["retrieved"][:k], chunk_text, page_text)
                for unit in record["evidence_units"]
            ]
            required_scores = [unit for unit in scored if unit["required"]]
            required_total += len(required_scores)
            covered_total += sum(unit["matched"] for unit in required_scores)
            sufficient_total += int(all(unit["matched"] for unit in required_scores))
            evaluated += 1
            if k == 10:
                per_question.append({
                    "question_id": record["question_id"],
                    "covered_required_units": sum(unit["matched"] for unit in required_scores),
                    "required_units": len(required_scores),
                    "sufficient_evidence": all(unit["matched"] for unit in required_scores),
                    "evidence_units": scored,
                    "remaining_unmatched_required_units": [unit["unit_id"] for unit in required_scores if not unit["matched"]],
                })
        aggregates[str(k)] = {
            "evaluated_questions": evaluated,
            "required_evidence_units": required_total,
            "covered_evidence_units": covered_total,
            "atomic_evidence_recall": covered_total / required_total,
            "sufficient_evidence": sufficient_total / evaluated,
        }
    negative = [record["question_id"] for record in contract["records"] if record.get("evaluation_mode") == "negative_space"]
    failure_classification = {
        "Q002": {"primary": "retrieval/ranking", "evidence": "The authoritative day-care fragment maps to the source page but no matching chunk is in Top 10."},
        "Q008": {"primary": "retrieval/ranking", "evidence": "The cataract-list unit maps to the source page but its chunk is absent from Top 10."},
        "Q014": {"primary": "retrieval/ranking", "evidence": "The required unit maps exactly but no witness is retrieved in Top 10."},
        "Q017": {"primary": "retrieval/ranking", "evidence": "The required unit maps exactly but no witness is retrieved in Top 10."},
        "Q030": {"primary": "retrieval/ranking", "evidence": "The required unit maps exactly but no witness is retrieved in Top 10."},
        "Q031": {"primary": "retrieval/ranking", "evidence": "The required unit maps exactly but no witness is retrieved in Top 10."},
        "Q034": {"primary": "retrieval/ranking", "contributing": "chunk boundary/chunking", "evidence": "Rank 2 has the page-15 continuation, but no page-14 opening is in Top 10; page-bounded chunks cannot make the cross-page unit sufficient without both."},
        "Q037": {"primary": "retrieval/ranking", "evidence": "The required unit maps exactly but no witness is retrieved in Top 10."},
    }
    return {
        "evaluation_contract_version": "2.0",
        "source_rankings": "artifacts/retrieval/stage1_voyage4/retrieval_results.json",
        "retrieval_rerun": False,
        "incremental_api_cost_usd": 0,
        "negative_space_questions": negative,
        "metrics_by_k": aggregates,
        "questions_at_k_10": per_question,
        "remaining_genuine_retrieval_failures": [
            {"question_id": item["question_id"], "unmatched_units": item["remaining_unmatched_required_units"], **failure_classification[item["question_id"]]}
            for item in per_question if item["remaining_unmatched_required_units"]
        ],
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=Path("evals/evaluation_contract_v2.json"))
    parser.add_argument("--results", type=Path, default=Path("artifacts/retrieval/stage1_voyage4/retrieval_results.json"))
    parser.add_argument("--chunks", type=Path, default=Path("artifacts/retrieval/stage1_voyage4/chunks.jsonl"))
    parser.add_argument("--pages", type=Path, default=Path("artifacts/extraction/policy_pages.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/retrieval/stage1_voyage4/evaluation_v2_results.json"))
    args = parser.parse_args()
    output = rescore(json.loads(args.contract.read_text()), json.loads(args.results.read_text()), _read_jsonl(args.chunks), _read_jsonl(args.pages))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
