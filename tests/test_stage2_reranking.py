import json
from pathlib import Path

import pytest

from semantic_retrieval.stage2_reranking import run_experiment


ROOT = Path(__file__).parents[1]


class RankedFake:
    def predict(self, pairs):
        # Promote Stage 1 rank 11, while retaining deterministic ordering otherwise.
        return [100.0 if index == 10 else (-1000.0 if index == 0 else -float(index))
                for index, _ in enumerate(pairs)]


def test_reranks_exactly_30_and_reports_rescue_and_loss():
    chunks = [
        {"chunk_id": f"c{i}", "text": "target" if i in (0, 10) else f"noise {i}",
         "source_file": "policy.pdf", "page_number": 1}
        for i in range(30)
    ]
    # c0 covers U1 and is displaced; c10 covers U2 and is promoted.
    chunks[0]["text"] = "first evidence"
    chunks[10]["text"] = "second evidence"
    pages = [{"source_file": "policy.pdf", "page_number": 1,
              "text": "first evidence filler second evidence"}]
    contract = {"records": [{
        "question_id": "Q001", "evaluation_mode": "positive",
        "evidence_units": [
            {"unit_id": "U1", "required": True, "source_fragments": [
                {"source_file": "policy.pdf", "source_page": 1, "text": "first evidence"}]},
            {"unit_id": "U2", "required": True, "source_fragments": [
                {"source_file": "policy.pdf", "source_page": 1, "text": "second evidence"}]},
        ],
    }]}
    retrieved = [
        {"rank": i + 1, "chunk_id": f"c{i}", "source_file": "policy.pdf", "page_number": 1}
        for i in range(30)
    ]
    rankings = {"status": "completed", "questions": [
        {"question_id": "Q001", "query_text": "question", "retrieved": retrieved}
    ]}
    config = {"candidate_depth": 30, "final_depth": 10, "model": "fake"}

    result = run_experiment(config, rankings, chunks, pages, contract, reranker=RankedFake())

    assert result["stage1_top_10"]["covered_evidence_units"] == 1
    assert result["stage2_reranked_top_10"]["covered_evidence_units"] == 1
    assert result["rescued_units"][0]["unit_id"] == "U2"
    assert result["lost_units"][0]["unit_id"] == "U1"
    assert result["usage_and_cost"]["pairs_scored"] == 30
    assert len(result["questions"][0]["reranked_top_10"]) == 10


def test_no_network_actual_committed_artifacts_reject_incomplete_candidate_depth():
    """Exercise real committed schemas without importing/downloading the model."""
    config = json.loads((ROOT / "configs/stage2_minilm_reranker.json").read_text())
    stored = json.loads(
        (ROOT / "artifacts/retrieval/stage1_voyage4/retrieval_results.json").read_text()
    )
    contract = json.loads((ROOT / "evals/evaluation_contract_v2.json").read_text())
    chunks = [json.loads(line) for line in (
        ROOT / "artifacts/retrieval/stage1_voyage4/chunks.jsonl"
    ).read_text().splitlines()]
    pages = [json.loads(line) for line in (
        ROOT / "artifacts/extraction/policy_pages.jsonl"
    ).read_text().splitlines()]
    positive_ids = {
        record["question_id"] for record in contract["records"]
        if record.get("evaluation_mode") != "negative_space"
    }
    # Adapt only the earlier artifact's field name; do not invent candidates.
    stored["questions"] = [q for q in stored["questions"] if q["question_id"] in positive_ids]
    for question in stored["questions"]:
        question["query_text"] = question["question"]

    with pytest.raises(ValueError, match="has 10 candidates; exactly 30 are required"):
        run_experiment(config, stored, chunks, pages, contract, reranker=RankedFake())
