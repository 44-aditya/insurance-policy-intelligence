"""Gold-span mapping, retrieval metrics, and diagnostic slices."""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from typing import Any

from .chunking import Chunk


def normalize_text(text: str) -> str:
    """Normalize Unicode, smart punctuation, whitespace, and case deterministically."""
    text = unicodedata.normalize("NFKC", text).casefold()
    text = text.translate(
        str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-"})
    )
    return re.sub(r"\s+", " ", text).strip()


def map_evidence(
    records: list[dict[str, Any]],
    chunks: list[Chunk],
    pages: dict[tuple[str, int], str],
) -> dict[str, list[dict[str, Any]]]:
    by_page: dict[tuple[str, int], list[Chunk]] = defaultdict(list)
    for chunk in chunks:
        by_page[(chunk.source_file, chunk.page_number)].append(chunk)
    mappings: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        mapped = []
        for index, span in enumerate(record.get("evidence_spans", [])):
            key = (span["source_file"], span["source_page"])
            needle = normalize_text(span["text"])
            page = normalize_text(pages.get(key, ""))
            candidates = [
                chunk.chunk_id
                for chunk in by_page.get(key, [])
                if needle and needle in normalize_text(chunk.text)
            ]
            occurrences = page.count(needle) if needle else 0
            status = (
                "matched"
                if candidates and occurrences == 1
                else (
                    "ambiguous_multiple_page_occurrences" if candidates else "unmatched"
                )
            )
            mapped.append(
                {
                    "evidence_index": index,
                    "source_file": key[0],
                    "source_page": key[1],
                    "candidate_chunk_ids": candidates,
                    "page_occurrences": occurrences,
                    "status": status,
                    "human_review_required": status != "matched",
                }
            )
        mappings[record["question_id"]] = mapped
    return mappings


def score_question(
    question_id: str,
    mappings: dict[str, list[dict[str, Any]]],
    retrieved_ids: list[str],
    *,
    abstention_probe: bool = False,
) -> dict[str, Any]:
    if abstention_probe:
        return {
            "question_id": question_id,
            "excluded_from_positive_aggregation": True,
            "evidence_recall": None,
            "sufficient_evidence": None,
        }
    spans = mappings[question_id]
    retrieved = set(retrieved_ids)
    covered = [
        bool(retrieved.intersection(span["candidate_chunk_ids"])) for span in spans
    ]
    return {
        "question_id": question_id,
        "excluded_from_positive_aggregation": False,
        "covered_evidence_spans": sum(covered),
        "required_evidence_spans": len(spans),
        "evidence_recall": sum(covered) / len(spans) if spans else 0.0,
        "sufficient_evidence": int(bool(spans) and all(covered)),
        "mapping_review_required": any(span["human_review_required"] for span in spans),
    }


def aggregate(scores: list[dict[str, Any]]) -> dict[str, float | int]:
    included = [
        score for score in scores if not score["excluded_from_positive_aggregation"]
    ]
    required = sum(score["required_evidence_spans"] for score in included)
    covered = sum(score["covered_evidence_spans"] for score in included)
    return {
        "evaluated_questions": len(included),
        "required_evidence_spans": required,
        "covered_evidence_spans": covered,
        "evidence_recall": covered / required if required else 0.0,
        "sufficient_evidence": sum(score["sufficient_evidence"] for score in included)
        / len(included)
        if included
        else 0.0,
    }
