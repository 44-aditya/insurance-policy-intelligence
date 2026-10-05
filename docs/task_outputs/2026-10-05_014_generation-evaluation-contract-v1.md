- Date: 2026-10-05
- Task / purpose: Design and implement Generation Evaluation Contract v1
- Git branch: work
- Related PR: unknown (created after this record)
- Commit SHA: see Git history (this record is committed with the implementation)
- Output status: Raw/verbatim; no secrets or machine-specific paths included

---

### Summary

* Added Generation Evaluation Contract v1 with explicit oracle-context and frozen Stage 2B end-to-end arms, shared experimental controls, Q040 negative-space treatment, and references to the existing gold dataset and Evaluation Contract v2 rather than duplicated source truth. 【F:evals/generation_evaluation_contract_v1.json†L2-L45】
* Added a versioned future experiment-output schema covering context provenance, model/prompt identifiers, generated answers, rubric references, human-reviewed correctness/fact/claim/citation/abstention annotations, usage/cost, failures, and evaluator version. No generation model was selected. 【F:evals/generation_experiment_output_v1.schema.json†L23-L41】
* Implemented API-free validation and deterministic derivation for authoritative references, complete required-fact annotation, oracle evidence sufficiency, citation existence/resolution, claim grounding, per-arm metrics, shared controls, and paired failure diagnostics. Semantic correctness, completeness, claim support, citation support, and abstention appropriateness intentionally remain explicit human-review judgments. 【F:src/evaluation/generation_contract_v1.py†L37-L155】【F:src/evaluation/generation_contract_v1.py†L165-L281】
* Documented why retrieval is insufficient, the controlled-arm design, dimension boundaries, Q040 protocol, exact metric numerators/denominators, failure attribution, evaluator calibration, and why no LLM judge is justified yet. 【F:docs/generation_evaluation_contract_v1.md†L1-L143】
* Added deterministic tests for a correct complete answer; a correct headline missing an exception; wrong numeric and missing-negation cases; unsupported claims; correct answers without required context; wrong-product, wrong-page, and non-supporting citations; appropriate abstention; a hallucinated Q040 rule; oracle sufficiency; authoritative bindings; and shared controls. 【F:tests/test_generation_contract_v1.py†L107-L205】【F:tests/test_generation_contract_v1.py†L242-L293】
* Recorded the evaluation-first decision and next calibration step in the project timelapse. 【F:docs/timelapse.md†L471-L505】

### Evaluation, assumptions, and unresolved questions

* No generation results or quality metrics were calculated; this task defines the measurement instrument only.
* Deterministic checks cover structure, provenance/reference integrity, exact source/page citation resolution, derived counts/rates, usage consistency, shared controls, and diagnostic classification.
* Human review remains required for policy-conclusion correctness, semantic required-fact coverage, claim atomization/contextual support, citation-to-claim support, and Q040 abstention appropriateness. These are not disguised as objective keyword heuristics.
* Before a full experiment, the unresolved owner decisions are the claim-atomization guidance and calibration acceptance threshold. Stage 2B per-question Top-10 artifacts are also required to execute the end-to-end arm.
* Assumptions: future answers make claim-to-citation association reviewable; both arms use identical model/prompt/answer-schema/evaluator versions; pricing and tokenizer rules will be versioned with the future selected model.
* Known limitation: diagnostic labels identify evidence-consistent contributions, not causal proof. In particular, absent context can explain an error but does not prove generation would succeed with that context.
* Security: no credentials or large evidence passages were added; existing authoritative artifacts are referenced. No external or generation API was called.
* Incremental API cost: **$0**.
* Recommended next experiment: owner-approved, independently human-reviewed calibration on a small stratified set spanning both arms and the documented adversarial slices; only after calibration, run the controlled paired experiment.

**Testing**

* ✅ `pytest -q` — 51 passed.
* ✅ `python -m compileall -q src tests`
* ✅ `python -m black --check src/evaluation/generation_contract_v1.py tests/test_generation_contract_v1.py`
* ✅ `python -m json.tool evals/generation_evaluation_contract_v1.json >/dev/null && python -m json.tool evals/generation_experiment_output_v1.schema.json >/dev/null`
* ⚠️ `python -c 'import jsonschema'` — optional `jsonschema` is not installed, so Draft 2020-12 metaschema validation was not available; JSON parsing and contract tests passed.
* ✅ `git diff --check`
