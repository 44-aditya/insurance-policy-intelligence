import json
from pathlib import Path

import pytest

from semantic_retrieval.stage2b_voyage_reranking import RerankResponse, run_experiment


ROOT = Path(__file__).parents[1]


class FakeReranker:
    def __init__(self, *, promote_index=None, shuffled=False):
        self.promote_index = promote_index
        self.shuffled = shuffled
        self.calls = []

    def rerank(self, query, documents):
        self.calls.append((query, list(documents)))
        results = [(index, 1.0 if index == self.promote_index else 0.0) for index in range(30)]
        if self.shuffled:
            results.reverse()
        return RerankResponse(results, total_tokens=100, returned_model="rerank-3")


class BrokenReranker:
    def rerank(self, query, documents):
        raise ConnectionError("provider unavailable")


def fixture_data():
    chunks = []
    questions = []
    records = []
    pages = []
    for number in range(1, 40):
        qid = f"Q{number:03d}"
        retrieved = []
        for index in range(31):
            chunk_id = f"{qid}-c{index}"
            text = f"{qid} noise {index}"
            if index == (9 if qid == "Q001" else 0):
                text = f"{qid} primary evidence"
            if qid == "Q001" and index == 10:
                text = "Q001 rescued evidence"
            chunks.append({
                "chunk_id": chunk_id, "text": text, "source_file": f"{qid}.pdf",
                "page_number": 1, "product_name": qid,
            })
            retrieved.append({
                "rank": index + 1, "chunk_id": chunk_id, "source_file": f"{qid}.pdf",
                "page_number": 1, "product_name": qid, "cosine_similarity": 1 - index / 100,
            })
        page = f"{qid} primary evidence filler"
        units = [{
            "unit_id": "U1", "required": True,
            "source_fragments": [{"source_file": f"{qid}.pdf", "source_page": 1, "text": f"{qid} primary evidence"}],
        }]
        if qid == "Q001":
            page += " Q001 rescued evidence"
            units.append({
                "unit_id": "U2", "required": True,
                "source_fragments": [{"source_file": "Q001.pdf", "source_page": 1, "text": "Q001 rescued evidence"}],
            })
        pages.append({"source_file": f"{qid}.pdf", "page_number": 1, "text": page})
        questions.append({"question_id": qid, "query_text": f"question {qid}", "retrieved": retrieved})
        records.append({"question_id": qid, "evaluation_mode": "positive", "evidence_units": units})
    config = {
        "model": "rerank-3", "candidate_depth": 30, "final_depth": 10,
        "truncation": False, "client_max_retries": 2,
        "price_usd_per_million_tokens": 0.05, "pricing_source": "test",
        "required_stage1_configuration": {
            "embedding_model": "voyage-4", "embedding_dimension": 1024,
            "chunk_size_tokens": 512, "chunk_overlap_tokens": 100,
        },
        "expected_first_cover_ranks": {},
        "frozen_stage1_counts": {
            "top_10_covered_units": 39, "top_10_sufficient_questions": 38,
            "top_30_covered_units": 40, "top_30_sufficient_questions": 39,
        },
    }
    rankings = {
        "status": "completed", "configuration": config["required_stage1_configuration"],
        "questions": questions,
    }
    return config, rankings, chunks, pages, {"records": records}


def test_exact_top30_mapping_ties_rescues_losses_and_cost():
    config, rankings, chunks, pages, contract = fixture_data()
    fake = FakeReranker(promote_index=10, shuffled=True)

    result = run_experiment(config, rankings, chunks, pages, contract, reranker=fake)

    assert len(fake.calls) == 39
    assert all(len(documents) == 30 for _, documents in fake.calls)
    assert all("noise 30" not in documents for _, documents in fake.calls)
    q1 = result["questions"][0]
    assert q1["candidates"][0]["stage1_rank"] == 11
    assert q1["candidates"][0]["stage1_cosine_similarity"] == pytest.approx(0.90)
    assert q1["candidates"][1]["stage1_rank"] == 1  # tied scores fall back to Stage 1 rank
    changes = result["quality_changes"]
    assert [(x["question_id"], x["unit_id"]) for x in changes["rescued_units"]] == [("Q001", "U2")]
    assert [(x["question_id"], x["unit_id"]) for x in changes["lost_units"]] == [("Q001", "U1")]
    assert changes["net_evidence_unit_change"] == 0
    assert result["usage_and_cost"]["provider_reported_total_tokens"] == 3900
    assert result["usage_and_cost"]["estimated_list_price_usd"] == pytest.approx(0.000195)
    assert result["decision"]["clear_net_quality_improvement"] is False


def test_equal_scores_preserve_original_order_deterministically():
    config, rankings, chunks, pages, contract = fixture_data()
    result = run_experiment(config, rankings, chunks, pages, contract, reranker=FakeReranker(shuffled=True))
    assert [item["stage1_rank"] for item in result["questions"][0]["candidates"]] == list(range(1, 31))


def test_rejects_incomplete_or_duplicate_result_mapping():
    config, rankings, chunks, pages, contract = fixture_data()

    class Duplicate:
        def rerank(self, query, documents):
            return RerankResponse([(0, 0.1)] * 30, 10)

    with pytest.raises(ValueError, match="every candidate exactly once"):
        run_experiment(config, rankings, chunks, pages, contract, reranker=Duplicate())


def test_validates_all_four_frozen_baseline_counts_before_api_calls():
    config, rankings, chunks, pages, contract = fixture_data()
    config["frozen_stage1_counts"]["top_30_sufficient_questions"] = 38
    fake = FakeReranker()
    with pytest.raises(ValueError, match="does not reproduce frozen Contract v2 counts"):
        run_experiment(config, rankings, chunks, pages, contract, reranker=fake)
    assert fake.calls == []


def test_api_failure_is_not_converted_to_results():
    config, rankings, chunks, pages, contract = fixture_data()
    with pytest.raises(ConnectionError, match="provider unavailable"):
        run_experiment(config, rankings, chunks, pages, contract, reranker=BrokenReranker())


def test_no_network_actual_committed_schemas_fail_before_reranking():
    """Exercise canonical chunk/page/contract/ranking schemas with no synthetic adapters."""
    config = json.loads((ROOT / "configs/stage2b_voyage_rerank3.json").read_text())
    rankings = json.loads((ROOT / "artifacts/retrieval/stage1_voyage4/retrieval_results.json").read_text())
    chunks = [json.loads(line) for line in (ROOT / "artifacts/retrieval/stage1_voyage4/chunks.jsonl").read_text().splitlines()]
    pages = [json.loads(line) for line in (ROOT / "artifacts/extraction/policy_pages.jsonl").read_text().splitlines()]
    contract = json.loads((ROOT / "evals/evaluation_contract_v2.json").read_text())
    positive = {record["question_id"] for record in contract["records"] if record.get("evaluation_mode") != "negative_space"}
    rankings["questions"] = [question for question in rankings["questions"] if question["question_id"] in positive]
    for question in rankings["questions"]:
        question["query_text"] = question["question"]
    fake = FakeReranker()
    with pytest.raises(ValueError, match="has 10 candidates; at least 30 are required"):
        run_experiment(config, rankings, chunks, pages, contract, reranker=fake)
    assert fake.calls == []
