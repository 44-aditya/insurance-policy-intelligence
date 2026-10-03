"""Validate gold cases and optionally diagnose current extraction mismatches."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

QUESTION_TYPES = {
    "definition", "coverage_benefit", "exclusion", "waiting_period",
    "limit_sublimit", "condition_eligibility", "claims_procedure", "cross_section",
}
DIFFICULTIES = {"easy", "medium", "hard"}
EVIDENCE_FORMATS = {"prose", "list", "table", "mixed"}
DATASET_STATUSES = {"examples_only", "draft", "reviewed", "frozen"}
REQUIRED_CASE_FIELDS = {
    "question_id", "question", "expected_answer", "answer_rubric",
    "evidence_spans", "question_type", "difficulty", "evidence_format", "notes",
}
REQUIRED_SPAN_FIELDS = {"source_file", "source_page", "text"}


@dataclass(frozen=True)
class ValidationResult:
    """Hard failures and non-blocking extraction observations."""

    errors: list[str]
    warnings: list[str]

    @property
    def is_valid(self) -> bool:
        return not self.errors


def normalize_whitespace(text: str) -> str:
    """Conservatively collapse extraction line breaks and spacing."""
    return re.sub(r"\s+", " ", text).strip()


def load_corpus_page_counts(metadata_path: Path) -> dict[str, int]:
    """Load parser-independent page bounds recorded in the corpus manifest."""
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    counts: dict[str, int] = {}
    for document in metadata.get("documents", []):
        filename, page_count = document.get("filename"), document.get("page_count")
        if not isinstance(filename, str) or not isinstance(page_count, int) or page_count < 1:
            raise ValueError("Every corpus document requires filename and positive page_count")
        if filename in counts:
            raise ValueError(f"Duplicate corpus metadata entry: {filename}")
        counts[filename] = page_count
    return counts


def load_extracted_pages(path: Path) -> dict[tuple[str, int], str]:
    """Load optional PyMuPDF output for diagnostics, never gold truth."""
    pages: dict[tuple[str, int], str] = {}
    with path.open(encoding="utf-8") as lines:
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                key = (record["source_file"], record["page_number"])
                text = record["text"]
            except (json.JSONDecodeError, KeyError, TypeError) as error:
                raise ValueError(f"Invalid extracted page at line {line_number}: {error}") from error
            if key in pages:
                raise ValueError(f"Duplicate extracted page: {key[0]} page {key[1]}")
            if not isinstance(text, str):
                raise ValueError(f"Extracted page text must be a string at line {line_number}")
            pages[key] = text
    return pages


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_dataset(
    dataset: Any,
    corpus_dir: Path,
    corpus_page_counts: dict[str, int],
    extracted_pages: dict[tuple[str, int], str] | None = None,
) -> ValidationResult:
    """Apply hard structural checks and optional soft extraction diagnostics."""
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(dataset, dict):
        return ValidationResult(["dataset must be an object"], warnings)
    expected_dataset_fields = {"schema_version", "dataset_status", "records"}
    missing_dataset_fields = expected_dataset_fields - dataset.keys()
    unknown_dataset_fields = dataset.keys() - expected_dataset_fields
    if missing_dataset_fields:
        errors.append(f"dataset missing required fields: {sorted(missing_dataset_fields)}")
    if unknown_dataset_fields:
        errors.append(f"dataset has unknown fields: {sorted(unknown_dataset_fields)}")
    if dataset.get("schema_version") != "1.0":
        errors.append("schema_version must be '1.0'")
    if dataset.get("dataset_status") not in DATASET_STATUSES:
        errors.append(f"dataset_status must be one of {sorted(DATASET_STATUSES)}")
    records = dataset.get("records")
    if not isinstance(records, list):
        return ValidationResult(errors + ["records must be an array"], warnings)

    ids = [r.get("question_id") for r in records if isinstance(r, dict) and isinstance(r.get("question_id"), str)]
    duplicates = sorted(value for value, count in Counter(ids).items() if count > 1)
    if duplicates:
        errors.append(f"question_id values must be unique; duplicates: {duplicates}")

    for index, record in enumerate(records):
        label = f"records[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label} must be an object")
            continue
        missing = REQUIRED_CASE_FIELDS - record.keys()
        unknown = record.keys() - REQUIRED_CASE_FIELDS
        if missing:
            errors.append(f"{label} missing required fields: {sorted(missing)}")
        if unknown:
            errors.append(f"{label} has unknown fields: {sorted(unknown)}")
        for field in ("question_id", "question", "expected_answer"):
            if not _non_empty_string(record.get(field)):
                errors.append(f"{label}.{field} must be a non-empty string")
        if not isinstance(record.get("notes"), str):
            errors.append(f"{label}.notes must be a string")
        if record.get("question_type") not in QUESTION_TYPES:
            errors.append(f"{label}.question_type must be one of {sorted(QUESTION_TYPES)}")
        if record.get("difficulty") not in DIFFICULTIES:
            errors.append(f"{label}.difficulty must be one of {sorted(DIFFICULTIES)}")
        if record.get("evidence_format") not in EVIDENCE_FORMATS:
            errors.append(f"{label}.evidence_format must be one of {sorted(EVIDENCE_FORMATS)}")

        rubric = record.get("answer_rubric")
        if not isinstance(rubric, dict):
            errors.append(f"{label}.answer_rubric must be an object")
        else:
            if set(rubric) != {"required_facts"}:
                errors.append(f"{label}.answer_rubric must contain only required_facts")
            facts = rubric.get("required_facts")
            if not isinstance(facts, list) or not facts or not all(_non_empty_string(fact) for fact in facts):
                errors.append(f"{label}.answer_rubric.required_facts must be a non-empty array of non-empty strings")

        spans = record.get("evidence_spans")
        if not isinstance(spans, list) or not spans:
            errors.append(f"{label}.evidence_spans must be a non-empty array")
            continue
        for span_index, span in enumerate(spans):
            span_label = f"{label}.evidence_spans[{span_index}]"
            if not isinstance(span, dict):
                errors.append(f"{span_label} must be an object")
                continue
            missing_span = REQUIRED_SPAN_FIELDS - span.keys()
            unknown_span = span.keys() - REQUIRED_SPAN_FIELDS
            if missing_span:
                errors.append(f"{span_label} missing required fields: {sorted(missing_span)}")
            if unknown_span:
                errors.append(f"{span_label} has unknown fields: {sorted(unknown_span)}")
            source_file, source_page, text = span.get("source_file"), span.get("source_page"), span.get("text")
            if not _non_empty_string(source_file):
                errors.append(f"{span_label}.source_file must be a non-empty string")
            elif source_file not in corpus_page_counts or not (corpus_dir / source_file).is_file():
                errors.append(f"{span_label}.source_file does not exist in corpus: {source_file}")
            if not isinstance(source_page, int) or isinstance(source_page, bool) or source_page < 1:
                errors.append(f"{span_label}.source_page must be a positive integer")
            elif isinstance(source_file, str) and source_file in corpus_page_counts and source_page > corpus_page_counts[source_file]:
                errors.append(f"{span_label}.source_page exceeds {source_file} page count ({corpus_page_counts[source_file]})")
            if not _non_empty_string(text):
                errors.append(f"{span_label}.text must be a non-empty exact PDF quotation")
            if extracted_pages is not None and _non_empty_string(source_file) and isinstance(source_page, int) and _non_empty_string(text):
                extracted = extracted_pages.get((source_file, source_page))
                if extracted is None:
                    warnings.append(f"{span_label}: no current extracted text for {source_file} page {source_page}")
                elif normalize_whitespace(text) not in normalize_whitespace(extracted):
                    warnings.append(f"{span_label}: gold PDF evidence was not located in current extracted text")
    return ValidationResult(errors, warnings)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--corpus-dir", type=Path, default=Path("corpus/policy_wordings"))
    parser.add_argument("--corpus-metadata", type=Path, default=Path("corpus/metadata.json"))
    parser.add_argument("--extracted-pages", type=Path, default=Path("artifacts/extraction/policy_pages.jsonl"))
    parser.add_argument("--no-extraction-diagnostics", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    diagnostic_warnings: list[str] = []
    extracted_pages = None
    if not args.no_extraction_diagnostics:
        try:
            extracted_pages = load_extracted_pages(args.extracted_pages)
        except (OSError, ValueError) as error:
            # Extraction is deliberately non-authoritative. Its absence or a
            # malformed artifact must never prevent hard dataset validation.
            diagnostic_warnings.append(f"extraction diagnostics unavailable: {error}")
    result = validate_dataset(dataset, args.corpus_dir, load_corpus_page_counts(args.corpus_metadata), extracted_pages)
    warnings = diagnostic_warnings + result.warnings
    for warning in warnings:
        print(f"WARNING: {warning}")
    if result.errors:
        print("Dataset validation failed:")
        for error in result.errors:
            print(f"- {error}")
        return 1
    print(f"Dataset validation passed: {len(dataset['records'])} records ({len(warnings)} extraction warnings)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
