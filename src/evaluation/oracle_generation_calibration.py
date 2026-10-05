"""Reproducible GPT-5.4 oracle-context generation calibration harness."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


class CalibrationError(ValueError):
    """Raised before a paid call when calibration inputs are unsafe or incomplete."""


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_config(config: dict[str, Any]) -> list[str]:
    if config["experiment_arm"] != "oracle_context":
        raise CalibrationError("only the oracle_context arm is permitted")
    selected = [item["question_id"] for item in config["question_selection"]]
    if not selected or len(selected) > config["max_questions"]:
        raise CalibrationError("calibration selection is empty or exceeds max_questions")
    if len(selected) != len(set(selected)):
        raise CalibrationError("calibration question IDs must be unique")
    if "Q040" not in selected:
        raise CalibrationError("Q040 is required by the negative-space protocol")
    return selected


def construct_oracle_context(
    question_id: str, gold: dict[str, Any], evidence: dict[str, Any]
) -> list[dict[str, Any]]:
    """Build deterministic context from v2 units, or Q040's reviewed nearby spans."""
    if evidence["question_id"] != question_id or gold["question_id"] != question_id:
        raise CalibrationError(f"{question_id}: authoritative record mismatch")
    items: list[dict[str, Any]] = []
    if evidence["evaluation_mode"] == "negative_space":
        if question_id != "Q040" or evidence["evidence_units"]:
            raise CalibrationError(f"{question_id}: invalid negative-space binding")
        for index, span in enumerate(gold["evidence_spans"], 1):
            items.append({
                "context_id": f"{question_id}-NEARBY-{index}",
                "source_file": span["source_file"],
                "source_page": span["source_page"],
                "evidence_unit_ids": [],
                "role": "nearby_clause_not_positive_evidence",
                "text": span["text"],
            })
        return items

    required_ids = {u["unit_id"] for u in evidence["evidence_units"] if u["required"]}
    represented: set[str] = set()
    for unit in evidence["evidence_units"]:
        for index, fragment in enumerate(unit["source_fragments"], 1):
            if not fragment.get("text"):
                raise CalibrationError(
                    f"{question_id} {unit['unit_id']}: empty authoritative fragment"
                )
            items.append({
                "context_id": f"{question_id}-{unit['unit_id']}-F{index}",
                "source_file": fragment["source_file"],
                "source_page": fragment["source_page"],
                "evidence_unit_ids": [unit["unit_id"]],
                "role": "authoritative_evidence",
                "text": fragment["text"],
            })
            represented.add(unit["unit_id"])
    if not required_ids or not required_ids <= represented:
        missing = sorted(required_ids - represented)
        raise CalibrationError(f"{question_id}: incomplete oracle context; missing {missing}")
    return items


def render_prompt(template: str, question: str, context: list[dict[str, Any]]) -> str:
    blocks = [
        f"[{item['context_id']}]\nSource: {item['source_file']}, page {item['source_page']}\n"
        f"Status: {item['role']}\nText: {item['text']}"
        for item in context
    ]
    return template.replace("{question}", question).replace(
        "{context}", "\n\n".join(blocks)
    )


def parse_structured_output(text: str, valid_context_ids: set[str]) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise CalibrationError(f"model output is not JSON: {error}") from error
    if set(value) != {"answer", "factual_claims", "insufficient_evidence"}:
        raise CalibrationError("model output has missing or unexpected top-level fields")
    if not isinstance(value["answer"], str) or not value["answer"].strip():
        raise CalibrationError("answer must be a non-empty string")
    if not isinstance(value["insufficient_evidence"], bool) or not isinstance(
        value["factual_claims"], list
    ):
        raise CalibrationError("invalid structured output field types")
    claim_ids: set[str] = set()
    for claim in value["factual_claims"]:
        if set(claim) != {"claim_id", "text", "citation_context_ids"}:
            raise CalibrationError("claim has missing or unexpected fields")
        if claim["claim_id"] in claim_ids:
            raise CalibrationError("claim IDs must be unique")
        claim_ids.add(claim["claim_id"])
        unknown = set(claim["citation_context_ids"]) - valid_context_ids
        if unknown:
            raise CalibrationError(f"claim cites unknown context IDs: {sorted(unknown)}")
    return value


def estimated_cost_usd(
    input_tokens: int,
    output_tokens: int,
    pricing: dict[str, float],
    cached_input_tokens: int = 0,
) -> float:
    if not 0 <= cached_input_tokens <= input_tokens:
        raise CalibrationError("cached input tokens must be within input token usage")
    return round(
        ((input_tokens - cached_input_tokens) * pricing["input"]
         + cached_input_tokens * pricing["cached_input"]
         + output_tokens * pricing["output"])
        / 1_000_000,
        10,
    )


def _response_text(response: Any) -> str:
    text = getattr(response, "output_text", None)
    if not text:
        raise CalibrationError("API response contains no output_text")
    return text


def _usage(response: Any) -> tuple[int, int, int]:
    usage = response.usage
    input_tokens = int(usage.input_tokens)
    output_tokens = int(usage.output_tokens)
    details = getattr(usage, "input_tokens_details", None)
    cached = int(getattr(details, "cached_tokens", 0) or 0)
    return input_tokens, output_tokens, cached


def _review_markdown(records: list[dict[str, Any]]) -> str:
    lines = [
        "# Oracle-context generation calibration — human review",
        "",
        "> Semantic labels are intentionally blank. A factual claim is the smallest independently supportable policy proposition. Do not split stylistic wording; split parts that could independently be true/false or require different evidence. For example, review a waiting period separately from an independently evidenced eligibility condition.",
        "",
        "Use Generation Evaluation Contract v1 labels: correctness (`correct` / `incorrect` / `uncertain`; Q040 `not_applicable`), required facts (`present` / `absent` / `contradicted` / `uncertain`), claim grounding (`supported` / `unsupported` / `uncertain`), citation support (`supported` / `not_supported` / `uncertain`), and Q040 abstention (`appropriate` / `inappropriate` / `uncertain`).",
    ]
    for record in records:
        lines += [f"\n## {record['question_id']}", f"**Question:** {record['question']}"]
        if record["failure"]:
            lines.append(f"\n**Execution failure:** `{record['failure']['error_type']}` — {record['failure']['message']}")
        elif record["generated_answer"] is None:
            lines.append("\n**Generated answer:** Not generated (validation-only dry run).")
        else:
            lines += [f"\n**Generated answer:** {record['generated_answer']}", "\n**Generated factual claims:**"]
            for claim in record["factual_claims"]:
                lines.append(f"- `{claim['claim_id']}` {claim['text']} — citations: {', '.join(claim['citation_context_ids']) or '(none)'}")
        lines += [f"\n**Expected answer:** {record['expected_answer']}", "\n**Required facts:**"]
        lines += [f"- [ ] Fact {i}: {fact} — label: ____" for i, fact in enumerate(record["required_facts"])]
        lines.append("\n**Supplied oracle evidence / provenance:**")
        for item in record["context_provenance"]:
            lines.append(f"- `{item['context_id']}` — `{item['source_file']}`, p. {item['source_page']} ({item['role']}): {item['text']}")
        lines += [
            "\n**Reviewer labels:**",
            "- Correctness: ____",
            "- Factual claim support (label each claim): ____",
            "- Citation support (label each claim/citation link): ____",
            "- Q040 abstention appropriateness: ____",
            "- Uncertainty / comments: ____",
        ]
    return "\n".join(lines) + "\n"


def run_calibration(
    config_path: Path,
    output_root: Path,
    run_id: str,
    dry_run: bool,
    client_factory: Callable[[str], Any] | None = None,
) -> Path:
    config = load_json(config_path)
    selected = validate_config(config)
    base = config_path.parent.parent
    gold_data = load_json(base / config["gold_dataset"])
    evidence_data = load_json(base / config["evidence_contract"])
    schema = load_json(base / config["answer_schema"])
    template = (base / config["prompt_file"]).read_text(encoding="utf-8")
    gold_by_id = {item["question_id"]: item for item in gold_data["records"]}
    evidence_by_id = {item["question_id"]: item for item in evidence_data["records"]}
    if not set(selected) <= gold_by_id.keys() or not set(selected) <= evidence_by_id.keys():
        raise CalibrationError("selected question is absent from an authoritative input")

    prepared = []
    for qid in selected:
        context = construct_oracle_context(qid, gold_by_id[qid], evidence_by_id[qid])
        prepared.append((qid, context, render_prompt(template, gold_by_id[qid]["question"], context)))

    api_key = None if dry_run else os.environ.get("OPENAI_API_KEY")
    if not dry_run and not api_key:
        raise CalibrationError("OPENAI_API_KEY is required for live execution")
    run_dir = output_root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    client = None
    if not dry_run:
        if client_factory is None:
            from openai import OpenAI
            client_factory = lambda key: OpenAI(api_key=key)
        client = client_factory(api_key or "")

    records: list[dict[str, Any]] = []
    raw_dir = run_dir / "raw_responses"
    raw_dir.mkdir()
    total_calls = 0
    for qid, context, prompt in prepared:
        gold = gold_by_id[qid]
        record: dict[str, Any] = {
            "question_id": qid,
            "experiment_arm": "oracle_context",
            "question": gold["question"],
            "model_identifier": config["model"]["model_identifier"],
            "reasoning_effort": config["model"]["reasoning_effort"],
            "prompt_version": config["prompt_version"],
            "answer_schema_version": config["answer_schema_version"],
            "evaluator_version": config["evaluator_version"],
            "rubric_reference": f"evals/gold_dataset.json#/records/{qid}",
            "context_provenance": context,
            "rendered_prompt": prompt,
            "generated_answer": None,
            "factual_claims": [],
            "insufficient_evidence": None,
            "expected_answer": gold["expected_answer"],
            "required_facts": gold["answer_rubric"]["required_facts"],
            "usage": {"latency_ms": None, "input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "estimated_api_cost_usd": 0.0, "actual_billed_cost_usd": None},
            "failure": None,
            "review_status": "pending_human_review",
            "execution_status": "validated_not_called" if dry_run else "pending_call",
        }
        if not dry_run:
            started = time.perf_counter()
            try:
                total_calls += 1
                response = client.responses.create(
                    model=config["model"]["model_identifier"],
                    reasoning={"effort": config["model"]["reasoning_effort"]},
                    service_tier=config["model"]["service_tier"],
                    input=[{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
                    text={"format": {"type": "json_schema", "name": "generation_answer_v1", "strict": True, "schema": schema}},
                    tools=[],
                )
                latency = (time.perf_counter() - started) * 1000
                raw = response.model_dump(mode="json")
                (raw_dir / f"{qid}.json").write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                parsed = parse_structured_output(_response_text(response), {i["context_id"] for i in context})
                inp, out, cached = _usage(response)
                record.update({"generated_answer": parsed["answer"], "factual_claims": parsed["factual_claims"], "insufficient_evidence": parsed["insufficient_evidence"]})
                record["execution_status"] = "succeeded"
                record["usage"] = {"latency_ms": latency, "input_tokens": inp, "cached_input_tokens": cached, "output_tokens": out, "total_tokens": inp + out, "estimated_api_cost_usd": estimated_cost_usd(inp, out, config["pricing_usd_per_million_tokens"], cached), "actual_billed_cost_usd": None}
            except Exception as error:
                record["usage"]["latency_ms"] = (time.perf_counter() - started) * 1000
                record["failure"] = {"stage": "api_or_response", "error_type": type(error).__name__, "message": str(error)}
                record["execution_status"] = "failed"
        records.append(record)

    latencies = [r["usage"]["latency_ms"] for r in records if r["usage"]["latency_ms"] is not None]
    totals = {key: sum(r["usage"][key] for r in records) for key in ("input_tokens", "output_tokens", "total_tokens", "estimated_api_cost_usd")}
    manifest = {
        "schema_version": "1.0", "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(), "mode": "dry_run" if dry_run else "live",
        "selected_question_ids": selected, "model_controls": config["model"],
        "prompt_version": config["prompt_version"], "answer_schema_version": config["answer_schema_version"], "evaluator_version": config["evaluator_version"],
        "pricing_assumption": {"version": config["pricing_version"], "rates": config["pricing_usd_per_million_tokens"], "source": config["pricing_source"], "cost_status": "estimate_not_invoice"},
        "total_api_calls": total_calls, "total_input_tokens": totals["input_tokens"], "total_output_tokens": totals["output_tokens"], "total_tokens": totals["total_tokens"], "total_estimated_api_cost_usd": totals["estimated_api_cost_usd"], "actual_billed_cost_usd": None,
        "mean_latency_ms": statistics.mean(latencies) if latencies else None, "median_latency_ms": statistics.median(latencies) if latencies else None,
        "failed_calls": sum(r["failure"] is not None for r in records), "human_review_status": "not_started",
    }
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (run_dir / "generation_records.json").write_text(json.dumps({"schema_version": "1.0", "experiment_id": run_id, "records": records}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (run_dir / "human_review.md").write_text(_review_markdown(records), encoding="utf-8")
    return run_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/oracle_generation_calibration_v1.json"))
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/generation/oracle_calibration"))
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(run_calibration(args.config, args.output_root, args.run_id, args.dry_run))


if __name__ == "__main__":
    main()
