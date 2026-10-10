- Date: 2026-10-10
- Task / purpose: Complete PR #22's Responses API Structured Outputs compatibility correction
- Git branch: work (existing PR #22 branch)
- Related PR: #22
- Commit SHA: this task's follow-up commit (see Git history)
- Output status: Raw/verbatim; no secrets or API-key values included

---

### Summary

* Completed the full API-facing schema audit. The validation keywords found across the original PR #22 schema were `uniqueItems`, `pattern`, and `minLength`. PR #22 had already removed `uniqueItems`; this follow-up removes `pattern` from `claim_id` and both `minLength` occurrences from `answer` and factual-claim `text`. The schema retains the existing object/array/string/boolean structure, required properties, array items, and `additionalProperties: false`.
* Preserved every logical invariant in deterministic post-parse validation. `answer` was already checked as a non-empty string. The validator now also requires every claim ID to match `^C[0-9]+$` and every claim text to be a non-empty string. Existing claim-ID uniqueness, citation-context-ID uniqueness, and unknown-citation rejection remain in place.
* Replaced the single-keyword schema assertion with a recursive, schema-specific allowlist covering only the keywords used by this answer schema. The exact schema captured from `responses.create(..., text.format.schema)` is checked with the same allowlist.
* Added regression cases for malformed claim IDs and whitespace-only answer/claim text. Existing tests continue to cover duplicate citations, unknown citations, valid output, and the exact request-construction path.
* Updated the calibration documentation and timelapse to distinguish provider-enforced supported structure from deterministic application-enforced invariants, and to state that offline tests cannot guarantee acceptance by the live provider's evolving validator.
* Did not modify the GPT-5.4 model, reasoning effort, prompt, selected questions, gold evidence, Generation Evaluation Contract, retrieval/reranking architecture, or pricing assumptions. No live API call was made, no API key was accessed or printed, and incremental API cost was $0.

### Validation and remaining uncertainty

* Full suite: 73 passed.
* Focused oracle harness suite: 22 passed.
* Frozen calibration dry run: passed with zero API calls.
* Diff whitespace check: passed.
* The official OpenAI Structured Outputs documentation confirms that strict mode accepts only a subset of JSON Schema and that unsupported schemas can be rejected before inference. Provider documentation and accepted dialects can evolve and may differ by model category; therefore the recursive offline allowlist verifies only the deliberately minimal schema we send and cannot guarantee future live server acceptance.
* Recommended next experiment: after PR #22 is reviewed and merged, rerun only the unchanged frozen ten-question calibration locally, then conduct the predefined human review before drawing any generation-quality conclusion.

### Testing

* ✅ `pytest -q` — 73 passed.
* ✅ `pytest -q tests/test_oracle_generation_calibration.py` — 22 passed.
* ✅ `git diff --check`
* ✅ `PYTHONPATH=src python -m evaluation.oracle_generation_calibration --config configs/oracle_generation_calibration_v1.json --output-root /tmp/oracle-schema-compat-20261010 --dry-run --run-id validation` — completed with zero API calls.
