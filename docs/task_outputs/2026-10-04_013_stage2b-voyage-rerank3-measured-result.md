- Date: 2026-10-04
- Task / purpose: Record the measured Stage 2B Voyage rerank-3 result
- Git branch: work
- Related PR: #18
- Commit SHA: see Git history (this record is committed with the measured-result update)
- Output status: Raw/verbatim; no secrets included; complete local experiment output unavailable

---

### Summary

* Added a compact measured Stage 2B artifact recording the supplied baseline, candidate ceiling, Voyage rerank-3 result, rescue/loss/net counts, sufficiency transitions, latency, provider-reported tokens, estimated costs, and accepted verdict. It explicitly records that the full local output and per-unit rescue identities were unavailable and were not reconstructed. 【F:artifacts/retrieval/stage2b_voyage_rerank3/20261004_full360/measured_summary.json†L1-L68】
* Updated the Stage 2B report from **UNMEASURED / BLOCKED** to **measured; hypothesis supported**. Voyage rerank-3 improved Atomic Evidence Recall@10 from 64/72 (88.9%) to 68/72 (94.4%) and Sufficient Evidence@10 from 31/39 (79.5%) to 35/39 (89.7%), rescuing four units while losing none. 【F:docs/stage2b_voyage_rerank3_experiment.md†L3-L19】
* Preserved the Stage 2A negative result in the three-system comparison: MiniLM remained at 56/72 and 27/39, with zero rescues and eight losses. The resulting evidence supports Voyage rerank-3 on this corpus and benchmark—not reranking generically. 【F:docs/stage2b_voyage_rerank3_experiment.md†L21-L32】【F:docs/stage2b_voyage_rerank3_experiment.md†L85-L87】
* Recorded the measured trade-off: 738.8023247949604 ms/query, 502,230 provider-reported tokens, $0.0251115 estimated total cost, and a derived $0.0006438846/query. Actual billed cost remains unavailable. 【F:docs/stage2b_voyage_rerank3_experiment.md†L40-L50】
* Recorded that Stage 2B recovered four of the five additional evidence units available in the frozen Top-30 and reached 68/72 against the 69/72 ceiling. With one unit of candidate-pool headroom remaining, another reranker has limited potential under the current pool. 【F:docs/stage2b_voyage_rerank3_experiment.md†L34-L38】
* Added the measured milestone to the project timelapse while preserving the earlier blocked attempt as execution history. Stage 2 now accepts `Voyage-4 Top-30 → Voyage rerank-3 → Top-10`, subject to the latency/cost trade-off. 【F:docs/timelapse.md†L433-L469】

### Evaluation and decision

* **Stage 1:** 64/72 atomic evidence and 31/39 sufficient questions.
* **Stage 2A MiniLM:** 56/72 atomic evidence and 27/39 sufficient questions; 0 rescued, 8 lost; rejected.
* **Stage 2B Voyage rerank-3:** 68/72 atomic evidence and 35/39 sufficient questions; 4 rescued, 0 lost, +4 net. Q002, Q030, Q031, and Q034 became sufficient; no question became insufficient.
* **Decision:** Stage 2B hypothesis supported. Accept Voyage rerank-3 as the Stage 2 retrieval architecture for this project, subject to approximately 739 ms/query additional latency and approximately $0.000644/query estimated API cost. 【F:docs/stage2b_voyage_rerank3_experiment.md†L78-L87】
* **Next stage:** do not add another reranker, fine-tune embeddings, change chunking, introduce hybrid search, or add generation in this PR. Separately evaluate answer generation and end-to-end RAG quality next. 【F:docs/stage2b_voyage_rerank3_experiment.md†L89-L92】

### Provenance, assumptions, and limitations

* The complete local `experiment_results.json` was unavailable in this environment. Only the owner-supplied aggregate measurements were recorded.
* Per-unit rescue identities, input hashes, API request/retry counts, returned model metadata, and actual billed cost were not supplied and were not inferred. 【F:docs/stage2b_voyage_rerank3_experiment.md†L61-L72】
* The total latency in the compact artifact is explicitly derived from the supplied mean × 39 rather than represented as an independently measured value.
* The existing Stage 1, Stage 2A, benchmark, Evaluation Contract v2, extraction, chunking, embedding, and reranker configuration artifacts were not modified.
* Security behavior is unchanged: `VOYAGE_API_KEY` remains environment-only, and private/customer documents require separate data-handling approval before external reranking. 【F:docs/stage2b_voyage_rerank3_experiment.md†L94-L101】

**Testing**

* ✅ `pytest -q` — 37 passed.
* ✅ `python -m compileall -q src tests`
* ✅ `python -m json.tool artifacts/retrieval/stage2b_voyage_rerank3/20261004_full360/measured_summary.json >/dev/null`
* ✅ `git diff --check`
