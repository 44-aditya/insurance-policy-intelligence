"""Offline structural revalidation of preserved oracle calibration responses."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from evaluation.oracle_generation_calibration import (
    CalibrationError,
    _review_markdown,
    load_json,
    parse_structured_output,
)


def response_text(raw: dict[str, Any]) -> str:
    """Read the Responses API's serialized message content without an SDK client."""
    if raw.get("status") != "completed":
        raise CalibrationError("saved response is not completed")
    parts = []
    for item in raw["output"]:
        if item.get("type") != "message":
            continue
        for content in item["content"]:
            if content.get("type") == "refusal":
                raise CalibrationError("saved response contains a refusal")
            if content.get("type") == "output_text":
                parts.append(content["text"])
    if not parts:
        raise CalibrationError("saved response contains no output_text")
    return "".join(parts)


def reprocess_run(source_dir: Path, output_dir: Path) -> Path:
    """Write a new derived run; keep all source accounting and inputs intact."""
    source_dir, output_dir = source_dir.resolve(), output_dir.resolve()
    if (output_dir == source_dir or source_dir in output_dir.parents
            or output_dir in source_dir.parents):
        raise CalibrationError("derived directory must be separate from the source run")
    if output_dir.exists():
        raise CalibrationError("derived directory already exists")
    source_manifest = load_json(source_dir / "run_manifest.json")
    source_records = load_json(source_dir / "generation_records.json")
    records = deepcopy(source_records["records"])
    question_ids = [record["question_id"] for record in records]
    if (len(set(question_ids)) != len(question_ids)
            or any(not re.fullmatch(r"Q[0-9]+", qid) for qid in question_ids)):
        raise CalibrationError("source question IDs must be unique and safe filenames")

    for record in records:
        raw_path = source_dir / "raw_responses" / f"{record['question_id']}.json"
        provenance: dict[str, Any] = {
            "source_run_id": source_manifest["run_id"],
            "source_raw_response_path": str(raw_path),
            "original_execution_status": record["execution_status"],
            "original_validation_failure": deepcopy(record["failure"]),
            "original_usage": deepcopy(record["usage"]),
            "raw_response_sha256": None,
            "raw_response_usage": None,
            "claim_id_mapping": [],
            "api_calls": 0,
            "estimated_api_cost_usd": 0.0,
        }
        record["reprocessing"] = provenance
        record.update(generated_answer=None, factual_claims=[], insufficient_evidence=None,
                      review_status="pending_human_review")
        try:
            # Never follow a raw-response symlink outside the source run.
            if source_dir not in raw_path.resolve().parents:
                raise CalibrationError("raw response resolves outside the source run")
            raw_bytes = raw_path.read_bytes()
            provenance["raw_response_sha256"] = hashlib.sha256(raw_bytes).hexdigest()
            raw = json.loads(raw_bytes)
            provenance["raw_response_usage"] = raw.get("usage")
            text = response_text(raw)
            parsed = parse_structured_output(
                text, {item["context_id"] for item in record["context_provenance"]}
            )
            original_claims = json.loads(text)["factual_claims"]
            provenance["claim_id_mapping"] = [
                {"original": old["claim_id"], "canonical": new["claim_id"]}
                for old, new in zip(original_claims, parsed["factual_claims"], strict=True)
            ]
            record.update(generated_answer=parsed["answer"],
                          factual_claims=parsed["factual_claims"],
                          insufficient_evidence=parsed["insufficient_evidence"],
                          failure=None, execution_status="succeeded")
            provenance["outcome"] = "succeeded"
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
            record["failure"] = {
                "stage": "offline_reprocessing", "error_type": type(error).__name__,
                "message": str(error),
            }
            record["execution_status"] = "failed"
            provenance["outcome"] = "failed"

    succeeded = sum(r["reprocessing"]["outcome"] == "succeeded" for r in records)
    manifest = {
        "schema_version": "1.0", "run_id": output_dir.name,
        "mode": "offline_reprocessing",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source_run_id": source_manifest["run_id"],
        "source_run_path": str(source_dir),
        "source_manifest": source_manifest,
        "total_api_calls": 0, "total_estimated_api_cost_usd": 0.0,
        "reprocessing_succeeded": succeeded,
        "reprocessing_failed": len(records) - succeeded,
        "human_review_status": "not_started",
    }
    # Prepare the worksheet before creating the destination, so invalid source
    # records cannot leave a seemingly complete derived run.
    worksheet = _review_markdown(records)
    output_dir.mkdir(parents=True, exist_ok=False)
    for name, value in (
        ("run_manifest.json", manifest),
        ("generation_records.json", {
            **source_records, "experiment_id": output_dir.name, "records": records,
        }),
    ):
        (output_dir / name).write_text(
            json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    (output_dir / "human_review.md").write_text(worksheet, encoding="utf-8")
    return output_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        output = reprocess_run(args.source_dir, args.output_dir)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, f"Reprocessing failed: {error}\n")
    print(output)
    return 1 if load_json(output / "run_manifest.json")["reprocessing_failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
