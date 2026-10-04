- Date: 2026-10-04
- Task / purpose: Implement Evaluation Contract v2 and rescore stored Stage 1 retrieval results
- Git branch: implement/evaluation-contract-v2
- Related PR: to be created
- Commit SHA: created by this task; see branch history
- Output status: Raw/verbatim (PR metadata and final commit SHA are necessarily reported after this file is committed)

---

Complete final task response follows here.

### Summary

- Implemented the separately versioned Evaluation Contract v2 with authoritative atomic evidence units, the approved Q002/Q034 corrections, explicit required/optional Q029 units, and Q040 excluded as a negative-space case.
- Added deterministic scoring over stored Experiment 1 rankings only: Unicode/case, quote/dash, soft-hyphen, whitespace, punctuation, and extraction-fragment normalization; exact source/document/page anchoring; and collective Top-K interval coverage with auditable chunk/rank witnesses.
- Published the v2 machine-readable result artifact and concise report. Atomic Evidence Recall is 38.9%/63.9%/79.2%/88.9% at K=1/3/5/10, and Sufficient Evidence is 23.1%/53.8%/66.7%/79.5%. Incremental API cost is $0.
- Preserved the immutable v1 result (59.3% Recall@10). Of the 18 reviewed v1-unmappable spans, 16 were measurement-contract or negative-space cases and two (Q002/Q034) remain genuine Top-10 misses. Across the full v2 benchmark, eight questions retain a required-unit failure, each classified with supporting evidence.
- Added adversarial tests proving reviewed normalization and collective coverage while rejecting wrong numbers, removed negation, wrong documents/products, incomplete fragments, and semantic paraphrases.
- Updated the timelapse with the material learning that v1 partly measured annotation/evaluator defects, while v2 separates measurement defects from genuine retrieval failures. Evaluation Contract v2 is now closed; no embeddings, retrieval, extraction, reranking, hybrid search, or chunk-size experiment was run.

### Assumptions and limitations

- V2's decomposed 72-unit denominator is intentionally not directly interchangeable with v1's 54-span denominator; both are reported rather than silently replacing history.
- Explicit extraction locators are used only for reviewed parser corruption. Authoritative fragment text remains separate and unchanged.
- This evaluates evidence availability, not generated-answer correctness or abstention quality.
- No new dependencies, credentials, external documents, or customer data were introduced.

**Testing**

- ✅ `pytest -q` (28 passed)
- ✅ `PYTHONPATH=src python -m evaluation.contract_v2` (reproduced the stored v2 artifact without API calls)
- ✅ `python -m json.tool evals/evaluation_contract_v2.json >/dev/null`
- ✅ `python -m json.tool artifacts/retrieval/stage1_voyage4/evaluation_v2_results.json >/dev/null`
- ✅ `git diff --check`
