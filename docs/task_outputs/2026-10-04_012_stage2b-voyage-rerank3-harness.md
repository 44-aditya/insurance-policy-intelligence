- Date: 2026-10-04
- Task / purpose: Implement the controlled Stage 2B Voyage rerank-3 experiment
- Git branch: work
- Related PR: prepared after implementation commit
- Commit SHA: see Git history (this record is committed with the implementation)
- Output status: Raw/verbatim; no secrets included

---

### Summary
* Added a separately configured Stage 2B harness using the official Voyage SDK. It validates the frozen Voyage-4/512-token/100-overlap configuration, Q001–Q039, all four baseline/ceiling counts, and all eight known first-cover ranks before any paid call; reranks exactly 30 candidates; rejects missing/duplicate response indices; and breaks ties by original Stage 1 rank. 【F:src/semantic_retrieval/stage2b_voyage_reranking.py†L38-L64】【F:src/semantic_retrieval/stage2b_voyage_reranking.py†L131-L225】
* Added complete experiment observability: all 30 candidate movements with original cosine and rerank scores, Contract v2 baseline/ceiling/final metrics, rescued/lost/net units, sufficiency transitions, known reachable and unreachable outcomes, latency, provider-reported usage, list-price estimates, hashes, model metadata, and explicit billed-cost/retry limitations. 【F:src/semantic_retrieval/stage2b_voyage_reranking.py†L227-L363】
* Added no-network tests for exact Top-30 selection, response mapping, deterministic ties, rescue/loss/net detection, all-four-count baseline validation before API use, provider failure propagation, cost calculation, and compatibility with the real committed ranking/chunk/page/Contract schemas. 【F:tests/test_stage2b_voyage_reranking.py†L89-L157】
* Added the controlled configuration and intentionally ignored the large local full-ranking input. The frozen parameters include `rerank-3`, 30→10 depths, no truncation, timeout/retry policy, pricing provenance, Stage 1 controls, all eight known ranks, and baseline counts. 【F:configs/stage2b_voyage_rerank3.json†L1-L33】
* Produced the Stage 2B report and permanent timelapse entry. Stage 2B is explicitly **UNMEASURED / BLOCKED** because the required local `20261004_full360/full_rankings.json` is absent; Stage 1 remains 64/72 and 31/39, Stage 2A remains rejected at 56/72 and 27/39, and no Stage 2B outcome, usage, latency, or cost was fabricated. 【F:docs/stage2b_voyage_rerank3_experiment.md†L3-L25】【F:docs/timelapse.md†L400-L431】

### Evaluation result
* **Stage 2B:** UNMEASURED / BLOCKED before API client construction. The missing full-ranking artifact is an execution prerequisite, not a reranker result.
* **Stage 1:** 64/72 (88.9%) atomic evidence and 31/39 (79.5%) sufficient; Top-30 ceilings 69/72 and 36/39.
* **Stage 2A:** 56/72 (77.8%) atomic evidence and 27/39 (69.2%) sufficient, zero rescues, eight losses, approximately 1,347.8 ms/query, $0 API cost; rejected.
* **Stage 2B:** no quality, latency, token, estimated-cost, or billed-cost measurement exists yet. Therefore the question “was it materially better and worth the overhead?” cannot yet be answered.

### Local execution
Place the immutable Stage 1 artifact at `artifacts/retrieval/stage1_voyage4_diagnostics/20261004_full360/full_rankings.json`, then run on the owner's Mac:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
export VOYAGE_API_KEY='<your Voyage API key>'
PYTHONPATH=src python -m semantic_retrieval.stage2b_voyage_reranking \
  --output artifacts/retrieval/stage2b_voyage_rerank3/20261004_full360/experiment_results.json
pytest -q
```

Do not paste, print, or commit the key. Full instructions and interpretation rules are documented in the report. 【F:docs/stage2b_voyage_rerank3_experiment.md†L51-L85】

### Assumptions, limitations, security, cost, and next step
* Assumption: the owner's local full-ranking artifact is the authoritative completed Stage 1 output. The harness will reject it if configuration, IDs, deterministic metrics, or known first-cover ranks differ.
* Limitation: Voyage SDK rerank responses provide token usage but do not expose observed retry counts; the configured maximum is recorded and observed retries remain `null` rather than fabricated.
* Security: `VOYAGE_API_KEY` is read only from the environment and never persisted. Reranking sends query and policy chunk text to Voyage, so private/customer content requires a separate approved data-handling review.
* Cost: pricing is frozen at the documented 2026-10-04 list-price assumption of $0.05/million processed tokens. Estimated total/per-query costs are calculated only from provider-reported usage; actual billed cost remains unavailable and distinct.
* Known reachability: Q017 U2, Q030 U1, Q002 U2, Q031 U1, and Q034 U1 are eligible for rescue. Q037 U2 (40), Q014 U2 (41), and Q008 U4 (106) cannot be rescued at depth 30 and are not reranker failures. Q034 retains its page-boundary complication. 【F:docs/stage2b_voyage_rerank3_experiment.md†L77-L101】
* Recommended next experiment: none. First run this controlled Stage 2B experiment locally, then jointly review net quality, latency, and cost before authorizing any further architectural change.

**Testing**
* ✅ `pytest -q` (37 passed)
* ✅ `python -m compileall -q src tests`
* ✅ `git diff --check`
* ⚠️ `PYTHONPATH=src python -m semantic_retrieval.stage2b_voyage_reranking --output artifacts/retrieval/stage2b_voyage_rerank3/20261004T_blocked_missing_full_rankings/run_blocked.json` (expected environment limitation: the intentionally uncommitted full-ranking artifact is absent; exited 2 before any API call)
