- Date: 2026-10-04
- Task / purpose: Run a separately versioned exhaustive Stage 1 Voyage-4 diagnostic
- Git branch: work
- Related PR: unknown / none
- Commit SHA: 2f26dcb (base revision before this task)
- Output status: Raw/verbatim (credential values and proxy details not recorded)

---

### Summary

* Added a standalone full-ranking diagnostic that consumes the existing committed
  360 chunks without invoking extraction or chunking. It embeds the corpus as
  `document` and the unchanged 39 positive Evaluation Contract v2 questions as
  `query`, validates 1,024-dimensional responses, computes exhaustive cosine
  rankings, and is configured to persist every rank, score, chunk ID, source,
  page, query, latency, usage count, cost input, timestamp, run ID, and input hash.
* Added v2 Atomic Evidence Recall@K and Sufficient Evidence@K calculation for
  K=1,3,5,10,20,30,50 directly over each exhaustive ranking.
* The result format explicitly records that full rankings are persisted while
  embedding vectors are not. This follows repository policy and avoids committing
  a large reproducible vector cache.
* Added a deterministic test proving the diagnostic reuses supplied chunks,
  preserves the query text, calls the embedder with the correct input types,
  retains all ranked chunks, reports API usage/cost, and omits vectors.
* Attempted live run `20261004T_diagnostic_v2_full360`. The first Voyage corpus
  request could not cross the execution environment's proxy (HTTP 403), before
  an API response was received. The versioned failure artifact records this
  without including the credential or proxy configuration.

### Diagnostic outcome

The requested measurements do **not** exist. The failed transport produced no
Voyage embeddings, no full rankings, no below-Top-10 ranks or cosine scores, no
candidate-recall curve, and no API-returned model identifier. Consequently, the
requested eight-row evidence diagnosis cannot be completed honestly and no
classification can be assigned from this attempt.

Actual Voyage token usage and billable cost are also unknown because no API usage
response was received. They are intentionally `null` in the failure artifact;
the historical `$0.00906792` is not reused, and zero is not asserted as though it
were provider-confirmed usage.

### Decision

There is not enough measured evidence to recommend an architectural experiment.
Doing so would contradict the evaluation-first principle and the user's rule to
show ranks before classification. The single operational next action is to rerun
the prepared diagnostic unchanged in an environment whose network policy permits
the Voyage API. Once it completes, exactly one architectural experiment should be
selected from the observed rank distribution; this task does not implement one.

### Assumptions, limitations, security, and cost

* **Assumption:** the committed chunk artifact, v2 contract, and extraction pages
  identified by SHA-256 in the failure record are the authoritative inputs.
* **Limitation:** environment network policy prevented the required paid service
  call, so none of the substantive retrieval claims can be made.
* **Security:** the runner reads the key only from `VOYAGE_API_KEY`; neither the
  key, its value, nor proxy details are persisted. Inputs are the repository's
  public policy corpus and derived artifacts.
* **Cost:** provider-reported usage and estimated cost are unavailable, rather
  than assumed to be zero. No vector cache was created or committed.

**Testing**

* ✅ `pytest -q` — 29 passed.
* ⚠️ `python -m semantic_retrieval.full_ranking_diagnostic --output-dir artifacts/retrieval/stage1_voyage4_diagnostics/20261004T_diagnostic_v2_full360` — failed before execution because the package was not installed on the default module path; rerun with `PYTHONPATH=src`.
* ⚠️ `PYTHONPATH=src python -m semantic_retrieval.full_ranking_diagnostic --output-dir artifacts/retrieval/stage1_voyage4_diagnostics/20261004T_diagnostic_v2_full360` — environment proxy returned HTTP 403 before the first Voyage API response.
