- Date: 2026-10-04
- Task / purpose: Implement and attempt the Stage 2 controlled Top-30 reranking experiment
- Git branch: work
- Related PR: unknown
- Commit SHA: 536b838 (base revision inspected before implementation)
- Output status: Raw/verbatim (PR metadata and final commit SHA were not available when the required pre-response record was created)

---

### Summary

* Implemented an isolated Stage 2 runner that consumes exactly the immutable
  Stage 1 Top-30, locally scores 1,170 query/passage pairs with a revision-pinned
  MiniLM cross-encoder, retains Top-10, and evaluates both arms through the
  existing deterministic Contract v2 scorer. It validates the frozen 64/72,
  31/39, and 69/72 Stage 1 counts before accepting a run; reports rescues,
  losses, per-question rankings, latency, usage, costs, errors, and input hashes;
  and never invokes embeddings or answer generation.
* Added separate Stage 2 configuration and the optional `stage2` dependency,
  pinning the local Apache-2.0 model revision, candidate/final depths, CPU device,
  deterministic original-rank tie breaking, and frozen baseline counts.
* Added focused reranking coverage plus a no-network integration test that loads
  the actual committed Contract v2, chunks, pages, and Stage 1 results. The latter
  proves the harness rejects the current ten-candidate artifact rather than
  silently pretending it is Top-30. Also corrected an existing diagnostic test's
  CSV fixture, which contained literal backslash-n characters.
* Documented model rationale, licensing, download/compute/API trade-offs,
  reproduction steps, acceptance checks, failure modes, and the candidate-depth
  ceiling. Q037 U2 (40), Q014 U2 (41), and Q008 U4 (106) cannot be rescued from
  Top-30; Q034 retains its page-boundary representation complication.
* The experiment is **blocked, not measured**: this repository snapshot has only
  the historical Top-10 result and a failed diagnostic record, not the completed
  `full_rankings.json`. The supplied aggregates and eight first-cover ranks cannot
  reconstruct all Top-30 lists. A blocked-run artifact preserves that fact without
  fabricated quality or latency results. Consequently, there is no evidence yet
  that reranking materially improves quality relative to latency, cost, and
  complexity, and no Stage 3 or other architecture change is recommended.

**Testing**

* ✅ `pytest -q` — 31 passed.
* ✅ `python -m compileall -q src tests`
* ✅ `git diff --check`
* ⚠️ `PYTHONPATH=src python -m semantic_retrieval.stage2_reranking --rankings artifacts/retrieval/stage1_voyage4_diagnostics/completed/full_rankings.json --output /tmp/stage2-blocked.json` — intentionally exited 2 and wrote a non-fabricated blocked result because the required completed Stage 1 artifact is absent from this repository snapshot.

### Assumptions, limitations, security, cost, and next action

* **Assumption:** the task-provided frozen metrics and first-cover ranks describe
  a completed artifact that has not been included in this checkout; they are not
  treated as sufficient substitutes for candidate records.
* **Known limitations:** no quality change or reranking latency is measurable
  without the artifact. Local timing will be hardware-specific, MiniLM has MS
  MARCO rather than insurance-domain training, and combined inputs truncate at
  512 tokens. Only evidence at Stage 1 rank 30 or better is eligible for rescue.
* **Security:** no keys or credentials are accepted. Model weights stay in an
  external cache and no weights, embedding vectors, or derived caches are committed.
* **Cost:** the local reranker has $0 incremental API cost and no API token usage.
  Local compute cost remains unknown until a machine price and real runtime exist.
* **Recommended next experiment:** none beyond completing this already-defined
  Stage 2 experiment. Supply the immutable completed `full_rankings.json` and run
  the documented command; evaluate the resulting measured delta and displacement
  against latency before making any architecture recommendation.
