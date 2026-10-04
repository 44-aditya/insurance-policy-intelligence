- Date: 2026-10-04 (original response date; captured 2026-10-04)
- Task / purpose: Preserve the supplied final response for the Evaluation Contract v2 analysis
- Git branch: codex/implement-stage-1-semantic-vector-retrieval (capture workspace)
- Related PR: unknown
- Commit SHA: d104aa7012d4468fee241d1643a3966921eb5899 (capture source revision)
- Output status: Raw/verbatim supplied assistant response; separate text blocks joined with newlines; trailing whitespace removed for repository validation. Historical claims are preserved, not independently verified by this capture.

The detailed analysis is preserved separately in [the existing contract record](2026-10-04_004_evaluation-contract-v2-design.md). This capture does not reconstruct missing analysis. The supplied response below claims a commit and a clean working tree; at capture, the contract record was untracked and the timelapse was modified. Those historical claims are not evidence that this capture committed or pushed anything. No commit or push was performed during this capture.

---

### Summary

* Designed and documented the proposed **Evaluation Contract v2** as an analysis-only recommendation. The smallest defensible contract uses:
  * PDF-authoritative atomic evidence units and contiguous source fragments;
  * conservative, character-preserving deterministic normalization; and
  * ordered collective coverage across the union of Top-K chunks.
  Semantic similarity, fuzzy matching, and LLM judging are not recommended for the primary metric.

* Preserved the distinction between authoritative gold evidence, mutable extraction/chunk representations, and the evaluator that connects them.

* Recommended replacing each free-form scoring `evidence_span` with atomic evidence units, contiguous source fragments, and—only where genuine alternatives exist—explicit sufficient evidence sets.

* Defined explicit success and failure rules for punctuation and spacing differences, bullets, non-contiguous annotations, evidence split across chunks, cross-page evidence, extraction corruption, and genuine retrieval misses.

* Compared deterministic normalization, atomic decomposition, collective coverage, fuzzy lexical matching, semantic similarity, and LLM judging across false-positive risk, false-negative risk, reproducibility, interpretability, cost, and complexity.

* Documented proposed treatment for all 18 unmatched spans without recalculating metrics. Importantly, v2 would not automatically turn every case into success: Q002 remains a genuine Top-10 miss after annotation review, Q034 remains incomplete, Q012 and Q029 require collective coverage, and Q038 requires authoritative transcription review.

* Kept Q040 outside positive-evidence Recall@K and proposed a separate abstention/negative-space evaluation contract.

* Proposed a versioned migration plan covering the gold schema, annotation review, evaluator, adversarial tests, and historical reporting. Experiment 1’s original metrics and artifact remain immutable; any v2 rescore must be published as a new result with separate provenance.

* Preserved the complete analysis in the task-output log and recorded the material learning and pending architectural decision in the timelapse.

* No implementation, gold data, extraction, chunking, embeddings, retrieval logic, or experiment artifacts were modified. No replacement metrics were calculated and no paid API calls were made.

* Committed the documentation as `cba2e02d45bfbbbef00b3d4836df43aca8515e82` and prepared the required pull-request metadata titled **“Design Stage 1 Evaluation Contract v2.”**

**Testing**

* ✅ `git diff --check`
* ✅ `python - <<'PY' ...` — verified that all 18 unmatched-span identifiers and all six required comparison approaches are present in the saved contract.
* ✅ `rg -n '/Users/|/home/|/workspace/|API_KEY=|sk-[A-Za-z0-9]' docs/task_outputs/2026-10-04_004_evaluation-contract-v2-design.md docs/timelapse.md` — found no accidental absolute local paths or common secret patterns.
* ✅ `git status --porcelain` — clean after commit.
* ⚠️ Full automated test suite not run because this task changed documentation only and explicitly prohibited implementation or benchmark changes.
