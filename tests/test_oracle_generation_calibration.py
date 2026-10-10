from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import tomllib

import pytest

from evaluation.oracle_generation_calibration import (
    CalibrationError,
    construct_oracle_context,
    estimated_cost_usd,
    parse_structured_output,
    render_prompt,
    run_calibration,
    validate_config,
)


ROOT = Path(__file__).parents[1]
CONFIG_PATH = ROOT / "configs/oracle_generation_calibration_v1.json"
GOLD = {r["question_id"]: r for r in json.loads((ROOT / "evals/gold_dataset.json").read_text())["records"]}
EVIDENCE = {r["question_id"]: r for r in json.loads((ROOT / "evals/evaluation_contract_v2.json").read_text())["records"]}


def test_fixed_calibration_selection_and_rationales() -> None:
    config = json.loads(CONFIG_PATH.read_text())
    assert validate_config(config) == [
        "Q001", "Q002", "Q007", "Q008", "Q014",
        "Q017", "Q022", "Q034", "Q038", "Q040",
    ]
    assert all(item["rationale"] for item in config["question_selection"])


def test_oracle_context_represents_every_required_unit() -> None:
    context = construct_oracle_context("Q008", GOLD["Q008"], EVIDENCE["Q008"])
    represented = {unit for item in context for unit in item["evidence_unit_ids"]}
    assert represented == {"U1", "U2", "U3", "U4"}
    assert all(item["role"] == "authoritative_evidence" for item in context)


def test_incomplete_oracle_context_fails_before_execution() -> None:
    evidence = json.loads(json.dumps(EVIDENCE["Q008"]))
    evidence["evidence_units"][0]["source_fragments"] = []
    with pytest.raises(CalibrationError, match="incomplete oracle context"):
        construct_oracle_context("Q008", GOLD["Q008"], evidence)


def test_prompt_contains_question_evidence_ids_and_guardrails() -> None:
    template = (ROOT / "prompts/oracle_policy_qa_v1.txt").read_text()
    context = construct_oracle_context("Q001", GOLD["Q001"], EVIDENCE["Q001"])
    prompt = render_prompt(template, GOLD["Q001"]["question"], context)
    assert GOLD["Q001"]["question"] in prompt
    assert "Q001-U1-F1" in prompt
    assert "Never use outside knowledge" in prompt
    assert "expected_answer" not in prompt


def test_structured_output_parsing_and_citation_validation() -> None:
    parsed = parse_structured_output(
        json.dumps({
            "answer": "An accident is sudden.",
            "factual_claims": [{"claim_id": "C1", "text": "It is sudden.", "citation_context_ids": ["Q001-U1-F1"]}],
            "insufficient_evidence": False,
        }),
        {"Q001-U1-F1"},
    )
    assert parsed["factual_claims"][0]["claim_id"] == "C1"
    with pytest.raises(CalibrationError, match="unknown context IDs"):
        parse_structured_output(
            json.dumps({"answer": "x", "factual_claims": [{"claim_id": "C1", "text": "x", "citation_context_ids": ["made-up"]}], "insufficient_evidence": False}),
            {"Q001-U1-F1"},
        )


def test_duplicate_citation_context_ids_fail_local_validation() -> None:
    with pytest.raises(CalibrationError, match="citation context IDs must be unique"):
        parse_structured_output(
            json.dumps({
                "answer": "An accident is sudden.",
                "factual_claims": [{
                    "claim_id": "C1",
                    "text": "It is sudden.",
                    "citation_context_ids": ["Q001-U1-F1", "Q001-U1-F1"],
                }],
                "insufficient_evidence": False,
            }),
            {"Q001-U1-F1"},
        )


def test_api_facing_schema_omits_unsupported_unique_items() -> None:
    schema = json.loads((ROOT / "evals/generation_answer_v1.schema.json").read_text())
    assert "uniqueItems" not in json.dumps(schema)


def test_openai_sdk_is_a_runtime_dependency() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    assert "openai>=2,<3" in project["dependencies"]
    assert all("openai" not in requirement for requirement in project.get("optional-dependencies", {}).get("generation", []))


def test_dry_run_makes_zero_api_calls(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    called = False

    def factory(_: str) -> object:
        nonlocal called
        called = True
        raise AssertionError("dry-run must not construct a client")

    output = run_calibration(CONFIG_PATH, tmp_path, "dry", True, factory)
    manifest = json.loads((output / "run_manifest.json").read_text())
    assert called is False
    assert manifest["total_api_calls"] == 0
    assert manifest["selected_question_ids"][-1] == "Q040"


def test_missing_api_key_fails_without_creating_output(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(CalibrationError, match="OPENAI_API_KEY"):
        run_calibration(CONFIG_PATH, tmp_path, "live", False)
    assert not (tmp_path / "live").exists()


def test_usage_cost_calculation_includes_cached_rate() -> None:
    rates = {"input": 2.5, "cached_input": 0.25, "output": 15.0}
    assert estimated_cost_usd(1000, 100, rates, 400) == pytest.approx(0.0031)


class FakeResponse:
    output_text = json.dumps({
        "answer": "Supported answer.",
        "factual_claims": [{"claim_id": "C1", "text": "Supported claim.", "citation_context_ids": ["Q001-U1-F1"]}],
        "insufficient_evidence": False,
    })
    usage = SimpleNamespace(input_tokens=100, output_tokens=20, input_tokens_details=SimpleNamespace(cached_tokens=0))

    def model_dump(self, mode: str) -> dict:
        assert mode == "json"
        return {"id": "response_fixture", "output_text": self.output_text}


def _single_question_config(tmp_path: Path) -> Path:
    config = json.loads(CONFIG_PATH.read_text())
    config["question_selection"] = [
        {"question_id": "Q001", "rationale": "test"},
        {"question_id": "Q040", "rationale": "test"},
    ]
    # Paths resolve relative to the config's repository root (parent.parent).
    config_path = ROOT / "configs" / "_test_oracle_calibration.json"
    config_path.write_text(json.dumps(config))
    return config_path


def test_failed_api_response_is_recorded_without_fabricated_answer(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-placeholder-not-a-secret")

    class Responses:
        def create(self, **_: object) -> object:
            raise RuntimeError("simulated provider failure")

    config_path = _single_question_config(tmp_path)
    try:
        output = run_calibration(config_path, tmp_path, "failed", False, lambda _: SimpleNamespace(responses=Responses()))
    finally:
        config_path.unlink()
    records = json.loads((output / "generation_records.json").read_text())["records"]
    assert all(record["generated_answer"] is None for record in records)
    assert all(record["failure"]["error_type"] == "RuntimeError" for record in records)


def test_request_construction_uses_corrected_api_facing_schema(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-placeholder-not-a-secret")
    requests: list[dict[str, object]] = []

    class Responses:
        def create(self, **kwargs: object) -> FakeResponse:
            requests.append(kwargs)
            return FakeResponse()

    config_path = _single_question_config(tmp_path)
    try:
        run_calibration(
            config_path,
            tmp_path,
            "request-schema",
            False,
            lambda _: SimpleNamespace(responses=Responses()),
        )
    finally:
        config_path.unlink()

    expected_schema = json.loads((ROOT / "evals/generation_answer_v1.schema.json").read_text())
    assert len(requests) == 2
    for request in requests:
        answer_format = request["text"]["format"]  # type: ignore[index]
        assert answer_format == {
            "type": "json_schema",
            "name": "generation_answer_v1",
            "strict": True,
            "schema": expected_schema,
        }
        assert "uniqueItems" not in json.dumps(answer_format)


def test_rerun_collision_protection(tmp_path: Path) -> None:
    run_calibration(CONFIG_PATH, tmp_path, "same-run", True)
    with pytest.raises(FileExistsError):
        run_calibration(CONFIG_PATH, tmp_path, "same-run", True)


def test_q040_uses_only_reviewed_nearby_clauses() -> None:
    context = construct_oracle_context("Q040", GOLD["Q040"], EVIDENCE["Q040"])
    assert len(context) == len(GOLD["Q040"]["evidence_spans"])
    assert all(item["role"] == "nearby_clause_not_positive_evidence" for item in context)
    assert all(item["evidence_unit_ids"] == [] for item in context)
