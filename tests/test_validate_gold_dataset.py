import copy
import json
from pathlib import Path

import pytest

from evaluation.validate_gold_dataset import (
    load_corpus_page_counts,
    load_extracted_pages,
    normalize_whitespace,
    validate_dataset,
)


def valid_dataset() -> dict:
    return {
        "schema_version": "1.0",
        "dataset_status": "draft",
        "records": [{
            "question_id": "Q-001",
            "question": "What is covered?",
            "expected_answer": "The stated benefit is covered.",
            "answer_rubric": {"required_facts": ["The stated benefit is covered."]},
            "evidence_spans": [{
                "source_file": "policy.pdf", "source_page": 1,
                "text": "The stated benefit is covered.",
            }],
            "question_type": "coverage_benefit",
            "difficulty": "easy",
            "evidence_format": "prose",
            "notes": "Reviewed against the authoritative PDF.",
        }],
    }


@pytest.fixture
def corpus(tmp_path: Path) -> tuple[Path, dict[str, int]]:
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    (corpus_dir / "policy.pdf").touch()
    return corpus_dir, {"policy.pdf": 2}


def test_valid_case_and_whitespace_matched_diagnostic(corpus: tuple[Path, dict[str, int]]) -> None:
    corpus_dir, page_counts = corpus
    extracted = {("policy.pdf", 1): "The stated\n benefit   is covered."}

    result = validate_dataset(valid_dataset(), corpus_dir, page_counts, extracted)

    assert result.is_valid
    assert result.errors == []
    assert result.warnings == []
    assert normalize_whitespace("one\n  two") == "one two"


def test_extraction_mismatch_is_only_a_warning(corpus: tuple[Path, dict[str, int]]) -> None:
    corpus_dir, page_counts = corpus

    result = validate_dataset(
        valid_dataset(), corpus_dir, page_counts,
        {("policy.pdf", 1): "Different extracted text"},
    )

    assert result.is_valid
    assert result.errors == []
    assert len(result.warnings) == 1
    assert "not located in current extracted text" in result.warnings[0]


def test_hard_validation_does_not_require_extraction(corpus: tuple[Path, dict[str, int]]) -> None:
    corpus_dir, page_counts = corpus

    result = validate_dataset(valid_dataset(), corpus_dir, page_counts)

    assert result.is_valid
    assert result.warnings == []


def test_duplicate_id_missing_file_and_invalid_enums_are_hard_errors(
    corpus: tuple[Path, dict[str, int]],
) -> None:
    corpus_dir, page_counts = corpus
    dataset = valid_dataset()
    duplicate = copy.deepcopy(dataset["records"][0])
    duplicate["evidence_spans"][0]["source_file"] = "missing.pdf"
    duplicate["question_type"] = "invented"
    duplicate["difficulty"] = "subjective"
    duplicate["evidence_format"] = "diagram"
    dataset["records"].append(duplicate)

    result = validate_dataset(dataset, corpus_dir, page_counts)

    assert not result.is_valid
    assert any("question_id values must be unique" in error for error in result.errors)
    assert any("does not exist in corpus" in error for error in result.errors)
    assert any("question_type must be one of" in error for error in result.errors)
    assert any("difficulty must be one of" in error for error in result.errors)
    assert any("evidence_format must be one of" in error for error in result.errors)


def test_invalid_page_empty_spans_and_bad_rubric_are_hard_errors(
    corpus: tuple[Path, dict[str, int]],
) -> None:
    corpus_dir, page_counts = corpus
    dataset = valid_dataset()
    record = dataset["records"][0]
    record["answer_rubric"] = {"required_facts": []}
    record["evidence_spans"][0]["source_page"] = 3
    record["evidence_spans"][0]["text"] = ""

    result = validate_dataset(dataset, corpus_dir, page_counts)

    assert any("required_facts must be a non-empty array" in error for error in result.errors)
    assert any("source_page exceeds" in error for error in result.errors)
    assert any("non-empty exact PDF quotation" in error for error in result.errors)

    record["evidence_spans"] = []
    assert any(
        "evidence_spans must be a non-empty array" in error
        for error in validate_dataset(dataset, corpus_dir, page_counts).errors
    )


def test_unknown_and_missing_fields_are_hard_errors(corpus: tuple[Path, dict[str, int]]) -> None:
    corpus_dir, page_counts = corpus
    dataset = valid_dataset()
    record = dataset["records"][0]
    del record["expected_answer"]
    record["chunk_id"] = "forbidden-coupling"
    record["evidence_spans"][0]["section"] = "unknown field"

    result = validate_dataset(dataset, corpus_dir, page_counts)

    assert any("missing required fields" in error for error in result.errors)
    assert sum("unknown fields" in error for error in result.errors) == 2


def test_schema_and_examples_are_accepted_by_hard_validator() -> None:
    schema = json.loads(Path("evals/gold_dataset.schema.json").read_text())
    examples = json.loads(Path("evals/gold_dataset.examples.json").read_text())
    page_counts = load_corpus_page_counts(Path("corpus/metadata.json"))

    result = validate_dataset(examples, Path("corpus/policy_wordings"), page_counts)

    assert schema["$schema"].endswith("2020-12/schema")
    assert result.is_valid, result.errors
    assert all(record["question_id"].startswith("EXAMPLE-") for record in examples["records"])


def test_loaders_reject_duplicate_entries(tmp_path: Path) -> None:
    pages_path = tmp_path / "pages.jsonl"
    page = {"source_file": "policy.pdf", "page_number": 1, "text": "text"}
    pages_path.write_text(json.dumps(page) + "\n" + json.dumps(page) + "\n")
    with pytest.raises(ValueError, match="Duplicate extracted page"):
        load_extracted_pages(pages_path)

    metadata_path = tmp_path / "metadata.json"
    document = {"filename": "policy.pdf", "page_count": 1}
    metadata_path.write_text(json.dumps({"documents": [document, document]}))
    with pytest.raises(ValueError, match="Duplicate corpus metadata"):
        load_corpus_page_counts(metadata_path)
