"""Auditable, API-free validation and aggregation for generation contract v1.

Semantic judgments are explicit human annotations.  This module validates those
annotations against existing source truth and deterministically derives metrics;
it deliberately does not infer correctness from answer wording.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any


class ContractError(ValueError):
    """Raised when an experiment record is not auditable against source truth."""


def _index(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {record["question_id"]: record for record in records}


def _authoritative_locations(
    gold_record: dict[str, Any], evidence_record: dict[str, Any]
) -> set[tuple[str, int]]:
    locations = {
        (span["source_file"], span["source_page"])
        for span in gold_record["evidence_spans"]
    }
    for unit in evidence_record["evidence_units"]:
        locations.update(
            (fragment["source_file"], fragment["source_page"])
            for fragment in unit["source_fragments"]
        )
    return locations


def validate_and_derive(
    record: dict[str, Any],
    gold_record: dict[str, Any],
    evidence_record: dict[str, Any],
) -> dict[str, Any]:
    """Validate one reviewed output and derive only mechanical outcomes."""
    qid = record["question_id"]
    if qid != gold_record["question_id"] or qid != evidence_record["question_id"]:
        raise ContractError(f"{qid}: authoritative record mismatch")
    if record["question"] != gold_record["question"]:
        raise ContractError(f"{qid}: question must exactly match gold source truth")
    if record["rubric_reference"] != f"evals/gold_dataset.json#/records/{qid}":
        raise ContractError(f"{qid}: invalid rubric reference")
    if record["usage"]["total_tokens"] != (
        record["usage"]["input_tokens"] + record["usage"]["output_tokens"]
    ):
        raise ContractError(f"{qid}: total_tokens is inconsistent")

    negative_space = evidence_record["evaluation_mode"] == "negative_space"
    abstention = record["abstention"]
    if abstention["applicable"] != negative_space:
        raise ContractError(
            f"{qid}: abstention applicability disagrees with Contract v2"
        )
    if negative_space:
        if (
            record["correctness"]["label"] != "not_applicable"
            or record["required_fact_results"]
        ):
            raise ContractError(
                f"{qid}: negative-space case cannot receive ordinary positive scoring"
            )
    elif abstention["label"] != "not_applicable":
        raise ContractError(
            f"{qid}: positive case must use not_applicable abstention label"
        )

    expected_facts = gold_record["answer_rubric"]["required_facts"]
    fact_results = record["required_fact_results"]
    if not negative_space and sorted(
        item["fact_index"] for item in fact_results
    ) != list(range(len(expected_facts))):
        raise ContractError(
            f"{qid}: required-fact annotations must cover every gold fact exactly once"
        )

    claim_ids = [claim["claim_id"] for claim in record["claims"]]
    citation_ids = [citation["citation_id"] for citation in record["citations"]]
    if len(set(claim_ids)) != len(claim_ids) or len(set(citation_ids)) != len(
        citation_ids
    ):
        raise ContractError(f"{qid}: claim and citation IDs must be unique")
    known_claims, known_citations = set(claim_ids), set(citation_ids)
    for claim in record["claims"]:
        if not set(claim["citation_ids"]) <= known_citations:
            raise ContractError(f"{qid}: claim references an unknown citation")
    for citation in record["citations"]:
        if not set(citation["claim_ids"]) <= known_claims:
            raise ContractError(f"{qid}: citation references an unknown claim")
    claim_links = {
        (claim["claim_id"], cid)
        for claim in record["claims"]
        for cid in claim["citation_ids"]
    }
    citation_links = {
        (claim_id, citation["citation_id"])
        for citation in record["citations"]
        for claim_id in citation["claim_ids"]
    }
    if claim_links != citation_links:
        raise ContractError(f"{qid}: claim/citation links must be reciprocal")

    context_locations = {
        (item["source_file"], item["source_page"])
        for item in record["context"]["items"]
    }
    authoritative = _authoritative_locations(gold_record, evidence_record)
    citations = []
    for citation in record["citations"]:
        location = (citation["source_file"], citation["source_page"])
        citations.append(
            {
                **citation,
                "exists": True,
                "resolves": location in context_locations and location in authoritative,
            }
        )

    required_ids = {
        unit["unit_id"]
        for unit in evidence_record["evidence_units"]
        if unit["required"]
    }
    supplied_ids = {
        unit_id
        for item in record["context"]["items"]
        for unit_id in item.get("evidence_unit_ids", [])
    }
    evidence_sufficient = required_ids <= supplied_ids if not negative_space else None
    if (
        record["experiment_arm"] == "oracle_context"
        and not negative_space
        and not evidence_sufficient
    ):
        raise ContractError(f"{qid}: oracle context omits a required evidence unit")

    complete = not negative_space and all(
        item["status"] == "present" for item in fact_results
    )
    supported_claims = sum(
        claim["grounding"] == "supported" for claim in record["claims"]
    )
    return {
        **record,
        "derived": {
            "complete": complete if not negative_space else None,
            "required_facts_present": sum(
                item["status"] == "present" for item in fact_results
            ),
            "required_facts_total": len(fact_results),
            "supported_claims": supported_claims,
            "factual_claims_total": len(record["claims"]),
            "unsupported_claim_ids": [
                claim["claim_id"]
                for claim in record["claims"]
                if claim["grounding"] == "unsupported"
            ],
            "citations": citations,
            "context_has_all_required_evidence": evidence_sufficient,
        },
    }


def _ratio(numerator: int, denominator: int) -> dict[str, Any]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "value": numerator / denominator if denominator else None,
    }


def aggregate(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate reviewed records without an opaque composite score."""
    completed = [record for record in records if record["failure"] is None]
    positive = [
        record for record in completed if not record["abstention"]["applicable"]
    ]
    negative = [record for record in completed if record["abstention"]["applicable"]]
    claims = [claim for record in completed for claim in record["claims"]]
    citations = [
        citation for record in completed for citation in record["derived"]["citations"]
    ]
    resolved = [citation for citation in citations if citation["resolves"]]
    usage = [record["usage"] for record in records]
    return {
        "answer_correctness_rate": _ratio(
            sum(r["correctness"]["label"] == "correct" for r in positive), len(positive)
        ),
        "complete_answer_rate": _ratio(
            sum(r["derived"]["complete"] for r in positive), len(positive)
        ),
        "required_fact_coverage": _ratio(
            sum(r["derived"]["required_facts_present"] for r in positive),
            sum(r["derived"]["required_facts_total"] for r in positive),
        ),
        "grounded_claim_rate": _ratio(
            sum(c["grounding"] == "supported" for c in claims), len(claims)
        ),
        "citation_resolution_rate": _ratio(
            sum(c["resolves"] for c in citations), len(citations)
        ),
        "citation_support_rate": _ratio(
            sum(c["support"] == "supported" for c in resolved), len(resolved)
        ),
        "abstention_accuracy": _ratio(
            sum(
                r["abstention"]["label"] == "appropriate"
                and not r["abstention"]["asserted_unsupported_rule"]
                for r in negative
            ),
            len(negative),
        ),
        "latency_ms_per_query": (
            sum(u["latency_ms"] for u in usage) / len(usage) if usage else None
        ),
        "input_tokens_per_query": (
            sum(u["input_tokens"] for u in usage) / len(usage) if usage else None
        ),
        "output_tokens_per_query": (
            sum(u["output_tokens"] for u in usage) / len(usage) if usage else None
        ),
        "total_tokens_per_query": (
            sum(u["total_tokens"] for u in usage) / len(usage) if usage else None
        ),
        "estimated_cost_usd_per_query": (
            sum(u["estimated_cost_usd"] for u in usage) / len(usage) if usage else None
        ),
        "experiment_total_estimated_cost_usd": sum(
            u["estimated_cost_usd"] for u in usage
        ),
        "execution_failures": _ratio(
            sum(r["failure"] is not None for r in records), len(records)
        ),
        "evaluation_uncertainties": sum(
            r["correctness"]["label"] == "uncertain"
            or any(f["status"] == "uncertain" for f in r["required_fact_results"])
            or any(c["grounding"] == "uncertain" for c in r["claims"])
            or any(c["support"] == "uncertain" for c in r["citations"])
            or r["abstention"]["label"] == "uncertain"
            for r in completed
        ),
    }


def compare_arms(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Produce question-level diagnosis while retaining all component outcomes."""
    paired: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for record in records:
        paired[record["question_id"]][record["experiment_arm"]] = record
    output = []
    for qid, arms in sorted(paired.items()):
        oracle = arms.get("oracle_context")
        end_to_end = arms.get("stage2b_end_to_end")
        labels: list[str] = []
        if not oracle or not end_to_end:
            labels.append("evaluation_uncertainty_unpaired")
        elif end_to_end["abstention"]["applicable"]:
            if (
                end_to_end["abstention"]["label"] != "appropriate"
                or end_to_end["abstention"]["asserted_unsupported_rule"]
            ):
                labels.append("abstention_failure")
        else:
            o_correct = oracle["correctness"]["label"] == "correct"
            e_correct = end_to_end["correctness"]["label"] == "correct"
            evidence = end_to_end["derived"]["context_has_all_required_evidence"]
            if o_correct and not e_correct and not evidence:
                labels.append("retrieval_context_contribution")
            if not e_correct and evidence:
                labels.append("generation_failure")
            if not o_correct and not e_correct:
                labels.append("generation_prompt_model_or_contract_issue")
            if e_correct and not evidence:
                labels.append("unsupported_prior_knowledge_risk")
        for arm in (oracle, end_to_end):
            if not arm:
                continue
            if arm["derived"]["unsupported_claim_ids"]:
                labels.append(f"{arm['experiment_arm']}:grounding_failure")
            if any(
                not c["resolves"] or c["support"] != "supported"
                for c in arm["derived"]["citations"]
            ):
                labels.append(f"{arm['experiment_arm']}:citation_failure")
        output.append(
            {
                "question_id": qid,
                "oracle": oracle,
                "stage2b_end_to_end": end_to_end,
                "diagnostic_labels": sorted(set(labels)),
            }
        )
    return output


def evaluate_run(
    output: dict[str, Any], gold: dict[str, Any], evidence_contract: dict[str, Any]
) -> dict[str, Any]:
    """Validate a full output and return per-arm metrics plus paired diagnostics."""
    records = output["records"]
    identities = [
        (record["question_id"], record["experiment_arm"]) for record in records
    ]
    if len(set(identities)) != len(identities):
        raise ContractError("each question/arm pair must occur at most once")
    controls = {
        (
            record["model_identifier"],
            record["prompt_version"],
            record["answer_schema_version"],
            record["evaluator_version"],
        )
        for record in records
    }
    if len(controls) > 1:
        raise ContractError(
            "model, prompt, answer schema, and evaluator must be shared"
        )
    gold_by_id = _index(gold["records"])
    evidence_by_id = _index(evidence_contract["records"])
    reviewed = [
        validate_and_derive(
            r, gold_by_id[r["question_id"]], evidence_by_id[r["question_id"]]
        )
        for r in records
    ]
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in reviewed:
        groups[record["experiment_arm"]].append(record)
    return {
        "evaluator_version": "generation-v1",
        "experiment_id": output["experiment_id"],
        "metrics_by_arm": {
            arm: aggregate(items) for arm, items in sorted(groups.items())
        },
        "paired_question_diagnostics": compare_arms(reviewed),
    }
