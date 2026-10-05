import copy
import json
from pathlib import Path

import pytest

from evaluation.generation_contract_v1 import (
    ContractError,
    aggregate,
    compare_arms,
    evaluate_run,
    validate_and_derive,
)

ROOT = Path(__file__).parents[1]
CONTRACT = json.loads(
    (ROOT / "evals/generation_evaluation_contract_v1.json").read_text()
)
OUTPUT_SCHEMA = json.loads(
    (ROOT / "evals/generation_experiment_output_v1.schema.json").read_text()
)
GOLD = {
    r["question_id"]: r
    for r in json.loads((ROOT / "evals/gold_dataset.json").read_text())["records"]
}
EVIDENCE = {
    r["question_id"]: r
    for r in json.loads((ROOT / "evals/evaluation_contract_v2.json").read_text())[
        "records"
    ]
}


def positive(arm: str = "oracle_context") -> dict:
    q = GOLD["Q002"]
    return {
        "question_id": "Q002",
        "experiment_arm": arm,
        "question": q["question"],
        "context": {
            "items": [
                {
                    "source_file": "medicare_select_policy_wording_0faeeb61c5.pdf",
                    "source_page": 5,
                    "evidence_unit_ids": ["U1"],
                },
                {
                    "source_file": "medicare_select_policy_wording_0faeeb61c5.pdf",
                    "source_page": 4,
                    "evidence_unit_ids": ["U2"],
                },
            ]
        },
        "model_identifier": "future-model",
        "prompt_version": "p1",
        "answer_schema_version": "a1",
        "generated_answer": "Reviewed fixture",
        "rubric_reference": "evals/gold_dataset.json#/records/Q002",
        "correctness": {"label": "correct", "review_method": "human"},
        "required_fact_results": [
            {"fact_index": i, "status": "present", "review_method": "human"}
            for i in range(3)
        ],
        "claims": [
            {
                "claim_id": "C1",
                "text": "Reviewed factual claim",
                "grounding": "supported",
                "citation_ids": ["R1"],
                "review_method": "human",
            }
        ],
        "citations": [
            {
                "citation_id": "R1",
                "claim_ids": ["C1"],
                "source_file": "medicare_select_policy_wording_0faeeb61c5.pdf",
                "source_page": 5,
                "support": "supported",
                "review_method": "human",
            }
        ],
        "abstention": {
            "applicable": False,
            "label": "not_applicable",
            "asserted_unsupported_rule": False,
            "review_method": "human",
        },
        "usage": {
            "latency_ms": 10,
            "input_tokens": 100,
            "output_tokens": 20,
            "total_tokens": 120,
            "estimated_cost_usd": 0.01,
        },
        "failure": None,
        "evaluator_version": "generation-v1",
    }


def reviewed(record: dict) -> dict:
    return validate_and_derive(
        record, GOLD[record["question_id"]], EVIDENCE[record["question_id"]]
    )


def test_contract_references_every_authoritative_question_without_copying_truth() -> (
    None
):
    bindings = CONTRACT["question_bindings"]
    assert {item["question_id"] for item in bindings} == set(GOLD) == set(EVIDENCE)
    assert CONTRACT["negative_space_questions"] == ["Q040"]
    assert all(
        "expected_answer" not in item and "evidence_spans" not in item
        for item in bindings
    )
    assert OUTPUT_SCHEMA["$defs"]["record"]["properties"]["experiment_arm"]["enum"] == [
        "oracle_context",
        "stage2b_end_to_end",
    ]


def test_correct_complete_answer_derives_separate_success_metrics() -> None:
    result = reviewed(positive())
    metrics = aggregate([result])
    assert result["derived"]["complete"] is True
    assert metrics["answer_correctness_rate"] == {
        "numerator": 1,
        "denominator": 1,
        "value": 1,
    }
    assert metrics["required_fact_coverage"] == {
        "numerator": 3,
        "denominator": 3,
        "value": 1,
    }


@pytest.mark.parametrize(
    "failure_kind",
    ["missing_material_exception", "wrong_numeric_value", "missing_negation"],
)
def test_human_reviewed_semantic_failures_are_not_hidden_by_headline_correctness(
    failure_kind: str,
) -> None:
    record = positive()
    record["generated_answer"] = failure_kind
    record["required_fact_results"][-1]["status"] = (
        "absent" if failure_kind == "missing_material_exception" else "contradicted"
    )
    if failure_kind != "missing_material_exception":
        record["correctness"]["label"] = "incorrect"
    result = reviewed(record)
    assert result["derived"]["complete"] is False
    assert result["derived"]["required_facts_present"] == 2
    assert result["correctness"]["label"] == (
        "correct" if failure_kind == "missing_material_exception" else "incorrect"
    )


def test_unsupported_claim_fails_grounding_even_when_answer_is_correct() -> None:
    record = positive()
    record["claims"][0]["grounding"] = "unsupported"
    result = reviewed(record)
    assert result["correctness"]["label"] == "correct"
    assert result["derived"]["unsupported_claim_ids"] == ["C1"]
    assert aggregate([result])["grounded_claim_rate"]["value"] == 0


def test_correct_answer_from_context_missing_required_evidence_is_diagnosed() -> None:
    oracle = reviewed(positive())
    end_record = positive("stage2b_end_to_end")
    end_record["context"]["items"] = end_record["context"]["items"][:1]
    end_record["claims"][0]["grounding"] = "unsupported"
    end = reviewed(end_record)
    labels = compare_arms([oracle, end])[0]["diagnostic_labels"]
    assert "unsupported_prior_knowledge_risk" in labels
    assert "stage2b_end_to_end:grounding_failure" in labels


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_file", "wrong_product.pdf"),
        ("source_page", 99),
    ],
)
def test_wrong_product_or_page_citation_does_not_resolve(
    field: str, value: object
) -> None:
    record = positive()
    record["citations"][0][field] = value
    result = reviewed(record)
    assert result["derived"]["citations"][0]["exists"] is True
    assert result["derived"]["citations"][0]["resolves"] is False


def test_resolved_citation_can_still_fail_claim_support() -> None:
    record = positive()
    record["citations"][0]["support"] = "not_supported"
    result = reviewed(record)
    citation = result["derived"]["citations"][0]
    assert citation["resolves"] is True
    assert citation["support"] == "not_supported"
    assert aggregate([result])["citation_support_rate"]["value"] == 0


def negative_space(appropriate: bool) -> dict:
    q = GOLD["Q040"]
    record = positive("stage2b_end_to_end")
    record.update(
        {
            "question_id": "Q040",
            "question": q["question"],
            "rubric_reference": "evals/gold_dataset.json#/records/Q040",
            "correctness": {"label": "not_applicable", "review_method": "human"},
            "required_fact_results": [],
            "claims": [],
            "citations": [],
            "context": {
                "items": [
                    {"source_file": s["source_file"], "source_page": s["source_page"]}
                    for s in q["evidence_spans"]
                ]
            },
            "generated_answer": (
                "Insufficient evidence"
                if appropriate
                else "Coverage automatically terminates"
            ),
            "abstention": {
                "applicable": True,
                "label": "appropriate" if appropriate else "inappropriate",
                "asserted_unsupported_rule": not appropriate,
                "review_method": "human",
            },
        }
    )
    return record


def test_appropriate_abstention_is_scored_only_by_negative_space_protocol() -> None:
    result = reviewed(negative_space(True))
    metrics = aggregate([result])
    assert result["derived"]["complete"] is None
    assert metrics["answer_correctness_rate"]["denominator"] == 0
    assert metrics["abstention_accuracy"] == {
        "numerator": 1,
        "denominator": 1,
        "value": 1,
    }


def test_hallucinated_rule_fails_abstention() -> None:
    result = reviewed(negative_space(False))
    assert aggregate([result])["abstention_accuracy"]["value"] == 0
    oracle = copy.deepcopy(result)
    oracle["experiment_arm"] = "oracle_context"
    assert (
        "abstention_failure" in compare_arms([oracle, result])[0]["diagnostic_labels"]
    )


def test_oracle_context_must_contain_every_required_evidence_unit() -> None:
    record = positive()
    record["context"]["items"].pop()
    with pytest.raises(ContractError, match="oracle context omits"):
        reviewed(record)


def test_paired_run_requires_shared_experimental_controls() -> None:
    oracle = positive()
    end = positive("stage2b_end_to_end")
    end["model_identifier"] = "different-model"
    with pytest.raises(ContractError, match="must be shared"):
        evaluate_run(
            {
                "schema_version": "1.0",
                "experiment_id": "fixture",
                "records": [oracle, end],
            },
            {"records": list(GOLD.values())},
            {"records": list(EVIDENCE.values())},
        )
