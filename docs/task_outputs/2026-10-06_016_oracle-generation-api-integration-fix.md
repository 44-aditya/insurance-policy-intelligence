- Date: 2026-10-06
- Task / purpose: Correct oracle-generation Structured Outputs and SDK integration defects
- Git branch: work
- Related PR: new corrective PR (identifier unavailable in this environment)
- Commit SHA: this task's corrective commit (see Git history)
- Output status: Raw/verbatim; no secrets or API-key values included

---

### Summary

* Fixed the boundary-contract root cause: OpenAI's Structured Outputs subset rejects `uniqueItems`, so the API-facing `citation_context_ids` schema now remains a strict array of strings without that unsupported keyword. The full schema was inspected; no other unsupported keyword identified in the current general-model Structured Outputs subset was introduced or changed.
* Preserved the logical invariant by making `parse_structured_output` reject duplicate citation context IDs deterministically after parsing, while retaining existing unknown-citation and valid-response behavior.
* Made the OpenAI Python SDK a normal runtime dependency (`openai>=2,<3`) rather than an optional extra, consistent with the project's existing bounded dependency convention and the installed live harness entry point.
* Added deterministic tests for the committed API-facing schema, duplicate-citation rejection, valid structured parsing, the exact schema object passed at `responses.create(..., text.format.schema)`, and runtime dependency declaration. These mocked tests improve boundary coverage but explicitly do not claim to reproduce the provider's server-side schema validator.
* Documented the exact failed-run chronology: missing SDK; malformed locally exported key causing `UnicodeEncodeError`; then ten HTTP 400 schema rejections before inference. GPT-5.4 generation remains unevaluated, recorded token usage remains 0, no quality conclusion is possible, and incremental estimated API cost is $0.
* Updated the timelapse with the engineering lesson that dry runs and mocks test our code path, not an external provider's restricted/evolving schema dialect. Deterministic post-parse uniqueness validation retains an invariant the provider schema subset cannot express.
* Did not change the frozen experiment design, questions, prompt, model, gold evidence, retrieval, reranking, or Generation Evaluation Contract v1. No live generation or network API call was run in Codex.

### Root cause and exact correction

The live request crossed the application/provider boundary but was rejected before inference because `evals/generation_answer_v1.schema.json` placed `"uniqueItems": true` on each claim's `citation_context_ids`. The corrected provider-facing schema removes exactly that keyword. Citation uniqueness is now checked by comparing the citation list length with the size of its set in `parse_structured_output`; duplicates raise `CalibrationError` before a response can be accepted as successful.

### Validation results

* Full suite: 66 passed.
* Focused oracle harness suite: 15 passed.
* Validation-only frozen calibration: completed successfully with zero API calls.
* Diff whitespace check: passed.
* Evaluation result: none; GPT-5.4 inference did not occur and generation quality remains unmeasured.
* Security: no key or secret was read, printed, logged, or committed; tests use an explicit non-secret placeholder only with a fake client.
* Cost: incremental API cost $0 because no live API request was made.
* Known limitation: offline request-shape tests cannot guarantee acceptance by OpenAI's live, evolving Structured Outputs validator.
* Recommended next experiment: after review and merge, rerun only the unchanged frozen ten-question oracle calibration locally, then conduct the already-defined human review before drawing any generation-quality conclusion.

### Exact local rerun command after merge

Install/update the project so its declared SDK dependency is present, export `OPENAI_API_KEY` securely in the shell without typographic quote characters, then run:

```bash
PYTHONPATH=src python -m evaluation.oracle_generation_calibration \
  --config configs/oracle_generation_calibration_v1.json \
  --run-id "$(date -u +%Y%m%dT%H%M%SZ)"
```

### Testing

* ✅ `pytest -q`
* ✅ `pytest -q tests/test_oracle_generation_calibration.py`
* ✅ `git diff --check`
* ✅ `PYTHONPATH=src python -m evaluation.oracle_generation_calibration --config configs/oracle_generation_calibration_v1.json --output-root /tmp/oracle-schema-fix-dry-run --dry-run --run-id validation`
