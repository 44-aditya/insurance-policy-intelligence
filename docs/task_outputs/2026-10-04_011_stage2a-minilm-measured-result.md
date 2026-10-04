- Date: 2026-10-04
- Task / purpose: Record the measured Stage 2A MiniLM result and architectural verdict
- Git branch: work
- Related PR: #16
- Commit SHA: a2bfadd (implementation revision used before this documentation update)
- Output status: Raw/verbatim (measured values were supplied from the local run; the full local result and lost-unit identities were not available in this checkout)

---

### Summary

* Updated the Stage 2 report from its earlier blocked status to the measured
  Stage 2A result, including the Stage 1 Top-10 baseline, Top-30 ceiling, Stage 2A
  Top-10 metrics, rescue/loss counts, reranking latency, pair count, and costs.
* Added a compact machine-readable measured-summary artifact. It explicitly
  distinguishes supplied measurements from unavailable details: the full local
  output and identities of the eight lost evidence units were not supplied, so
  neither is reconstructed or invented.
* Preserved the earlier blocked-run artifact as execution history rather than
  rewriting it. Added a new timelapse milestone for the completed negative result.
* Recorded the explicit verdict: **Stage 2A hypothesis rejected.
  `cross-encoder/ms-marco-MiniLM-L6-v2` materially degraded retrieval quality
  while adding latency. This result rejects this reranker/configuration, not
  reranking as an architectural pattern.**
* Did not modify Stage 1 artifacts, experiment architecture, reranker,
  configuration, or implementation, and did not add another reranker.

### Measured evaluation

| Metric | Stage 1 | Stage 2A | Change |
|---|---:|---:|---:|
| Atomic Evidence Recall@10 | 64/72 (88.9%) | 56/72 (77.8%) | −8 units / −11.1 pp |
| Sufficient Evidence@10 | 31/39 (79.5%) | 27/39 (69.2%) | −4 questions / −10.3 pp |

The Stage 1 Top-30 ceiling was 69/72 atomic recall (95.8%) and 36/39 sufficient
(92.3%). MiniLM rescued zero evidence units and lost eight previously covered
units. It scored 1,170 pairs in 52,562.843 ms total, averaging 1,347.8 ms/query.
There were no API calls and no API cost; local compute cost was not priced.

### Interpretation and limitations

The candidate set had five additional evidence units beyond the Stage 1 Top-10,
but this reranker promoted none of the missing evidence into the final Top-10 and
instead displaced eight successful units. It therefore degraded both measured
quality metrics while adding about 1.35 seconds/query and local model complexity.

This is negative evidence about this exact local MiniLM reranker and fixed
configuration. It is not evidence that all reranking approaches fail. Q037 U2,
Q014 U2, and Q008 U4 remained outside the 30-candidate pool and could never be
rescued; Q034 retains its page-boundary representation complication. No Stage 3
or other architecture recommendation follows from this update.

**Testing**

* ✅ `pytest -q`
* ✅ `python -m compileall -q src tests`
* ✅ `python -m json.tool artifacts/retrieval/stage2_minilm/20261004_full360/measured_summary.json >/dev/null`
* ✅ `git diff --check`
