from copy import deepcopy
import json
from pathlib import Path
import socket
import sys

import pytest

from evaluation.oracle_generation_calibration import CalibrationError, run_calibration
from evaluation.reprocess_oracle_calibration import main, reprocess_run


ROOT = Path(__file__).parents[1]


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("offline reprocessing attempted an external call")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    import openai
    monkeypatch.setattr(openai, "OpenAI", forbidden)


@pytest.fixture
def source(tmp_path):
    run = run_calibration(ROOT / "configs/oracle_generation_calibration_v1.json",
                          tmp_path, "source-run", True)
    records_path = run / "generation_records.json"
    envelope = json.loads(records_path.read_text())
    record = envelope["records"][0]
    record.update(execution_status="failed", failure={
        "stage": "api_or_response", "error_type": "CalibrationError",
        "message": "claim IDs must be canonical",
    })
    record["usage"].update(latency_ms=2345.6, input_tokens=120, output_tokens=35,
                           total_tokens=155, estimated_api_cost_usd=0.00065)
    envelope["records"] = [record]
    records_path.write_text(json.dumps(envelope))
    manifest_path = run / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest.update(mode="live", total_api_calls=10,
                    total_estimated_api_cost_usd=0.025, total_input_tokens=1000)
    manifest_path.write_text(json.dumps(manifest))
    return run


def save_raw(source, ids=("c1", "c2"), citations=None):
    payload = {
        "answer": "Supported answer.", "insufficient_evidence": False,
        "factual_claims": [
            {"claim_id": claim_id, "text": f"Fact {i}.",
             "citation_context_ids": citations or ["Q001-U1-F1"]}
            for i, claim_id in enumerate(ids, 1)
        ],
    }
    raw = {
        "id": "resp_saved", "status": "completed", "model": "gpt-5.4",
        "output": [
            {"type": "reasoning", "summary": []},
            {"type": "message", "content": [
                {"type": "output_text", "text": json.dumps(payload)}]},
        ],
        "usage": {"input_tokens": 120, "output_tokens": 35, "total_tokens": 155,
                  "input_tokens_details": {"cached_tokens": 0}},
    }
    path = source / "raw_responses" / "Q001.json"
    path.write_text(json.dumps(raw))
    return path, raw


def read_record(output):
    return json.loads((output / "generation_records.json").read_text())["records"][0]


@pytest.mark.parametrize("ids", [("c1", "c2"), ("fc1", "fc2"),
                                 ("claim_1", "claim_2")])
def test_recovery_and_complete_source_immutability(source, tmp_path, ids):
    raw_path, raw = save_raw(source, ids)
    before = {str(p.relative_to(source)): p.read_bytes()
              for p in source.rglob("*") if p.is_file()}
    original = json.loads((source / "generation_records.json").read_text())["records"][0]
    manifest = json.loads((source / "run_manifest.json").read_text())
    output = reprocess_run(source, tmp_path / "derived")
    record = read_record(output)
    assert record["execution_status"] == "succeeded"
    assert record["failure"] is None
    assert [c["claim_id"] for c in record["factual_claims"]] == ["C1", "C2"]
    provenance = record["reprocessing"]
    assert provenance["original_validation_failure"] == original["failure"]
    assert provenance["source_run_id"] == "source-run"
    assert provenance["source_raw_response_path"] == str(raw_path)
    assert len(provenance["raw_response_sha256"]) == 64
    assert provenance["raw_response_usage"] == raw["usage"]
    assert provenance["claim_id_mapping"] == [
        {"original": ids[0], "canonical": "C1"},
        {"original": ids[1], "canonical": "C2"},
    ]
    for field in ("usage", "model_identifier", "prompt_version", "rendered_prompt",
                  "context_provenance", "answer_schema_version", "evaluator_version",
                  "rubric_reference", "required_facts", "expected_answer"):
        assert record[field] == original[field]
    derived_manifest = json.loads((output / "run_manifest.json").read_text())
    assert derived_manifest["source_manifest"] == manifest
    assert derived_manifest["source_manifest"]["total_api_calls"] == 10
    assert derived_manifest["source_manifest"]["total_estimated_api_cost_usd"] == 0.025
    assert derived_manifest["total_api_calls"] == 0
    assert derived_manifest["total_estimated_api_cost_usd"] == 0
    assert derived_manifest["reprocessing_succeeded"] == 1
    worksheet = (output / "human_review.md").read_text()
    assert "`C1`" in worksheet and "Correctness: ____" in worksheet
    assert before == {str(p.relative_to(source)): p.read_bytes()
                      for p in source.rglob("*") if p.is_file()}


@pytest.mark.parametrize("case, message", [
    ("missing", "No such file"), ("corrupt", "Expecting"),
    ("citation", "unknown context IDs"), ("duplicate", "unique"),
    ("misordered", "ordered alias"), ("alias_collision", "ordered alias"),
    ("incomplete", "not completed"), ("refusal", "refusal"),
    ("empty", "no output_text"), ("malformed", "not JSON"),
])
def test_remaining_failures_are_recorded(source, tmp_path, case, message):
    path, raw = save_raw(source)
    if case == "missing":
        path.unlink()
    elif case == "corrupt":
        path.write_text("{broken")
    elif case == "citation":
        save_raw(source, citations=["invented"])
    elif case == "duplicate":
        save_raw(source, ids=["c1", "c1"])
    elif case == "misordered":
        save_raw(source, ids=["c2", "c1"])
    elif case == "alias_collision":
        save_raw(source, ids=["c1", "fc1"])
    else:
        if case == "incomplete":
            raw["status"] = "incomplete"
        elif case == "refusal":
            raw["output"] = [{"type": "message", "content": [{"type": "refusal"}]}]
        elif case == "empty":
            raw["output"] = []
        else:
            raw["output"][1]["content"][0]["text"] = "not json"
        path.write_text(json.dumps(raw))
    output = reprocess_run(source, tmp_path / "derived")
    record = read_record(output)
    assert record["execution_status"] == "failed"
    assert message in record["failure"]["message"]
    assert record["reprocessing"]["original_validation_failure"]["message"] == "claim IDs must be canonical"
    assert record["generated_answer"] is None and record["factual_claims"] == []
    assert "Execution failure" in (output / "human_review.md").read_text()


def test_reprocessing_continues_after_missing_response(source, tmp_path):
    save_raw(source)
    path = source / "generation_records.json"
    data = json.loads(path.read_text())
    missing = deepcopy(data["records"][0])
    missing["question_id"] = "Q007"
    data["records"].insert(0, missing)
    path.write_text(json.dumps(data))
    output = reprocess_run(source, tmp_path / "derived")
    manifest = json.loads((output / "run_manifest.json").read_text())
    assert manifest["reprocessing_failed"] == manifest["reprocessing_succeeded"] == 1


def test_already_valid_record_and_failed_parse_accounting_are_preserved(source, tmp_path):
    save_raw(source, ids=["C1", "C2"])
    path = source / "generation_records.json"
    data = json.loads(path.read_text())
    data["records"][0].update(execution_status="succeeded", failure=None)
    data["records"][0]["usage"].update(input_tokens=0, output_tokens=0,
                                       total_tokens=0, estimated_api_cost_usd=0.0)
    path.write_text(json.dumps(data))
    record = read_record(reprocess_run(source, tmp_path / "derived"))
    assert record["failure"] is None
    assert record["reprocessing"]["original_execution_status"] == "succeeded"
    assert record["reprocessing"]["original_validation_failure"] is None
    assert record["usage"]["total_tokens"] == 0
    assert record["reprocessing"]["raw_response_usage"]["total_tokens"] == 155
    assert record["usage"]["estimated_api_cost_usd"] == 0


def test_external_raw_symlink_is_not_read(source, tmp_path):
    path, _ = save_raw(source)
    external = tmp_path / "outside.json"
    external.write_bytes(path.read_bytes())
    path.unlink()
    path.symlink_to(external)
    record = read_record(reprocess_run(source, tmp_path / "derived"))
    assert "outside the source run" in record["failure"]["message"]
    assert record["reprocessing"]["raw_response_sha256"] is None


def test_reject_source_nested_and_existing_destinations(source, tmp_path):
    for output in (source, source / "derived", tmp_path):
        with pytest.raises(CalibrationError, match="separate"):
            reprocess_run(source, output)
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(CalibrationError, match="already exists"):
        reprocess_run(source, existing)


def test_cli_reports_partial_failure_and_success(source, tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["reprocess-oracle-calibration", str(source),
                                     "--output-dir", str(tmp_path / "missing")])
    assert main() == 1
    save_raw(source)
    monkeypatch.setattr(sys, "argv", ["reprocess-oracle-calibration", str(source),
                                     "--output-dir", str(tmp_path / "good")])
    assert main() == 0
