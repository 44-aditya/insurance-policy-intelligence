- Date: 2026-10-10
- Task / purpose: Normalize safe model-generated claim-ID aliases in the oracle calibration harness
- Git branch: work
- Related PR: follow-up to the current oracle-generation calibration PR
- Commit SHA: this task's corrective commit (see Git history)
- Output status: Raw/verbatim; no secrets or API-key values included

---

### Summary

* Added the smallest deterministic claim-ID normalization rule needed for the first inference-complete live run. Canonical `CN` and the observed case-insensitive aliases `cN`, `fcN`, and `claim_N` normalize to `CN` only when the numeric suffix equals the claim's one-based array position.
* Preserved claim order and provenance. The provider response continues to be serialized under `raw_responses/` before parsing and remains unchanged; only parsed `generation_records.json` and review data receive canonical IDs.
* Inspected the answer and downstream artifact contracts. The current model response contains no field other than `factual_claims[].claim_id` that references a claim ID, so there are no in-response references to rewrite. Downstream Generation Contract v1 artifacts consume the normalized canonical identifiers.
* Kept unsafe cases as hard failures: missing or empty IDs, duplicate raw IDs, unrecognized formats, and IDs whose numeric suffix disagrees with claim order are not repaired. Existing non-empty text, citation uniqueness, unknown-citation, and structural checks remain intact.
* Added tests for all three observed live forms (`cN`, `fcN`, and `claim_N`), canonical output in claim order, unchanged raw input, duplicate/empty/missing/misordered/unrecognized failures, and end-to-end preservation of raw provider payloads alongside normalized generation records.
* Documented live run `20261010_oracle_gpt54_calibration_v5` accurately: ten calls reached inference; seven responses passed local validation; Q007, Q008, and Q040 failed only the former claim-ID format check. Human evaluation is not recorded, so no generation-quality conclusion is drawn. Supplied token and cost totals for that historical live run were unavailable and were not reconstructed.
* No live API call was made for this correction, no API key was accessed or printed, and incremental API cost was $0. The frozen experiment design, model, questions, prompt, evidence, retrieval, reranking, evaluation contract, and pricing assumptions were unchanged.

### Validation

* Full suite: 82 passed.
* Focused oracle harness suite: 31 passed.
* Frozen calibration dry run: passed with zero API calls.
* Diff whitespace check: passed.
* Assumption: a claim ID is safely normalizable only when it is in the explicit observed alias family and its numeric suffix agrees with its one-based claim position.
* Known limitation: any new alias family remains a deliberate validation failure until supported by evidence and reviewed; arbitrary IDs are never silently renumbered.
* Security: raw response preservation introduces no new credential handling, and no secrets were accessed or committed.
* Cost: incremental API cost $0.
* Recommended next step: review the normalization rule, then reprocess from preserved raw responses where operationally supported or rerun the unchanged frozen calibration; complete human review before drawing quality conclusions.

### Testing

* ✅ `pytest -q` — 82 passed.
* ✅ `pytest -q tests/test_oracle_generation_calibration.py` — 31 passed.
* ✅ `git diff --check`
* ✅ `PYTHONPATH=src python -m evaluation.oracle_generation_calibration --config configs/oracle_generation_calibration_v1.json --output-root /tmp/oracle-claim-normalization-dry-run --dry-run --run-id validation` — completed with zero API calls.
