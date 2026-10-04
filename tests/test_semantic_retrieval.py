import json
from pathlib import Path

import pytest

from semantic_retrieval.chunking import Chunk, chunk_page
from semantic_retrieval.evaluation import aggregate, map_evidence, score_question
from semantic_retrieval.experiment import run_experiment
from semantic_retrieval.full_ranking_diagnostic import run_diagnostic
from semantic_retrieval.ranking import rank_vectors


class WordTokenizer:
    def offsets(self, text: str) -> list[tuple[int, int]]:
        offsets = []
        cursor = 0
        for word in text.split():
            start = text.index(word, cursor)
            offsets.append((start, start + len(word)))
            cursor = start + len(word)
        return offsets


def page(text: str, source: str = "policy.pdf", number: int = 1) -> dict[str, object]:
    return {
        "source_file": source,
        "product_name": "Policy",
        "page_number": number,
        "text": text,
    }


def test_chunk_ids_and_boundaries_are_deterministic() -> None:
    first = chunk_page(page("one two three four five six"), WordTokenizer(), 4, 2)
    second = chunk_page(page("one two three four five six"), WordTokenizer(), 4, 2)
    other_page = chunk_page(page("one two three four", number=2), WordTokenizer(), 4, 2)

    assert [chunk.chunk_id for chunk in first] == [chunk.chunk_id for chunk in second]
    assert first[0].chunk_id != other_page[0].chunk_id
    assert [chunk.text for chunk in first] == [
        "one two three four",
        "three four five six",
    ]
    assert [(chunk.token_start, chunk.token_end) for chunk in first] == [(0, 4), (2, 6)]
    assert all(
        chunk.source_file == "policy.pdf" and chunk.page_number == 1 for chunk in first
    )


@pytest.mark.parametrize("size,overlap", [(0, 0), (4, -1), (4, 4), (4, 5)])
def test_invalid_chunk_configuration_fails(size: int, overlap: int) -> None:
    with pytest.raises(ValueError):
        chunk_page(page("text"), WordTokenizer(), size, overlap)


def test_cosine_ranking_and_stable_tie_break() -> None:
    ranked = rank_vectors(
        [1.0, 0.0], ["b", "a", "opposite"], [[1.0, 0.0], [1.0, 0.0], [-1.0, 0.0]], 3
    )
    assert [item[0] for item in ranked] == ["a", "b", "opposite"]
    assert [item[1] for item in ranked] == pytest.approx([1.0, 1.0, -1.0])


def make_chunk(chunk_id: str, text: str, page_number: int = 1) -> Chunk:
    return Chunk(chunk_id, "policy.pdf", "Policy", page_number, 0, 0, 10, 10, text)


def test_normalized_evidence_mapping_and_coverage() -> None:
    records = [
        {
            "question_id": "Q001",
            "evidence_spans": [
                {
                    "source_file": "policy.pdf",
                    "source_page": 1,
                    "text": "Covered  evidence",
                }
            ],
        }
    ]
    chunks = [make_chunk("c1", "Prefix COVERED\nevidence suffix")]
    mappings = map_evidence(
        records, chunks, {("policy.pdf", 1): "Prefix covered evidence suffix"}
    )

    assert mappings["Q001"][0]["status"] == "matched"
    assert score_question("Q001", mappings, ["c1"])["evidence_recall"] == 1.0
    assert score_question("Q001", mappings, ["other"])["sufficient_evidence"] == 0


def test_multiple_spans_require_all_evidence() -> None:
    mappings = {
        "Q002": [
            {"candidate_chunk_ids": ["a"], "human_review_required": False},
            {"candidate_chunk_ids": ["b"], "human_review_required": False},
        ]
    }
    partial = score_question("Q002", mappings, ["a"])
    complete = score_question("Q002", mappings, ["a", "b"])

    assert partial["evidence_recall"] == 0.5
    assert partial["sufficient_evidence"] == 0
    assert complete["sufficient_evidence"] == 1


def test_ambiguous_and_unmatched_mapping_require_review() -> None:
    records = [
        {
            "question_id": "Q",
            "evidence_spans": [
                {"source_file": "policy.pdf", "source_page": 1, "text": "repeat"},
                {"source_file": "policy.pdf", "source_page": 1, "text": "missing"},
            ],
        }
    ]
    mappings = map_evidence(
        records,
        [make_chunk("c", "repeat repeat")],
        {("policy.pdf", 1): "repeat repeat"},
    )["Q"]
    assert [item["status"] for item in mappings] == [
        "ambiguous_multiple_page_occurrences",
        "unmatched",
    ]
    assert all(item["human_review_required"] for item in mappings)


def test_q040_is_excluded_from_aggregate() -> None:
    mappings = {
        "Q001": [{"candidate_chunk_ids": ["a"], "human_review_required": False}],
        "Q040": [{"candidate_chunk_ids": ["x"], "human_review_required": False}],
    }
    positive = score_question("Q001", mappings, ["a"])
    probe = score_question("Q040", mappings, ["x"], abstention_probe=True)
    result = aggregate([positive, probe])
    assert probe["evidence_recall"] is None
    assert result["evaluated_questions"] == 1
    assert result["sufficient_evidence"] == 1.0


class MockEmbedder:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def embed(self, texts: list[str], *, input_type: str):
        self.calls.append(input_type)
        if texts == ["broken question"]:
            raise RuntimeError("mock API failure")
        return [[1.0, 0.0] for _ in texts], len(texts)


def test_experiment_uses_input_types_and_records_query_failure(tmp_path: Path) -> None:
    pages = tmp_path / "pages.jsonl"
    pages.write_text(json.dumps(page("gold evidence")) + "\n", encoding="utf-8")
    gold = tmp_path / "gold.json"
    gold.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "question_id": "Q001",
                        "question": "working",
                        "difficulty": "easy",
                        "evidence_format": "prose",
                        "evidence_spans": [
                            {
                                "source_file": "policy.pdf",
                                "source_page": 1,
                                "text": "gold evidence",
                            }
                        ],
                    },
                    {
                        "question_id": "Q002",
                        "question": "broken question",
                        "difficulty": "hard",
                        "evidence_format": "table",
                        "evidence_spans": [
                            {
                                "source_file": "policy.pdf",
                                "source_page": 1,
                                "text": "gold evidence",
                            }
                        ],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    config = {
        "chunk_size_tokens": 4,
        "chunk_overlap_tokens": 1,
        "document_batch_size": 2,
        "embedding_dimension": 2,
        "embedding_model": "mock",
        "tokenizer_model": "mock",
        "k_values": [1, 3, 5, 10],
        "price_usd_per_million_tokens": None,
    }
    embedder = MockEmbedder()

    result = run_experiment(
        config,
        pages,
        gold,
        tmp_path / "out",
        tokenizer=WordTokenizer(),
        embedder=embedder,
    )

    assert embedder.calls == ["document", "query", "query"]
    assert result["questions"][1]["failures"] == [
        {"type": "RuntimeError", "message": "mock API failure"}
    ]
    assert result["corpus_embedding"]["api_calls"] == 1
    assert (tmp_path / "out" / "retrieval_results.json").exists()


class DiagnosticEmbedder:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def embed(self, texts: list[str], *, input_type: str):
        self.calls.append((input_type, len(texts)))
        vectors = [[1.0, float(index)] for index, _ in enumerate(texts)]
        return vectors, len(texts) * 2, "mock-version"


def test_full_diagnostic_reuses_chunks_and_persists_all_ranks(tmp_path: Path) -> None:
    chunks = tmp_path / "chunks.jsonl"
    chunks.write_text("\n".join(json.dumps({
        "chunk_id": f"c{i}", "source_file": "policy.pdf", "product_name": "Policy",
        "page_number": 1, "text": text,
    }) for i, text in enumerate(("gold evidence", "other", "third"))) + "\n")
    pages = tmp_path / "pages.jsonl"
    pages.write_text(json.dumps(page("gold evidence other third")) + "\n")
    contract = tmp_path / "contract.json"
    contract.write_text(json.dumps({"records": [{
        "question_id": "Q001", "question": "unchanged query",
        "evidence_units": [{"unit_id": "U1", "required": True, "source_fragments": [{
            "source_file": "policy.pdf", "source_page": 1, "text": "gold evidence"
        }]}],
    }]}))
    embedder = DiagnosticEmbedder()
    output = tmp_path / "run-1"
    result = run_diagnostic({
        "embedding_dimension": 2, "embedding_model": "mock", "document_batch_size": 2,
        "price_usd_per_million_tokens": 1.0,
    }, chunks, pages, contract, output, embedder=embedder)

    assert embedder.calls == [("document", 2), ("document", 1), ("query", 1)]
    assert len(result["questions"][0]["retrieved"]) == 3
    assert result["questions"][0]["query_text"] == "unchanged query"
    assert result["persistence"]["embedding_vectors"] is False
    assert result["usage_and_cost"] == {
        "total_tokens": 8, "total_api_calls": 3,
        "price_usd_per_million_tokens": 1.0, "estimated_list_price_usd": 0.000008,
    }
