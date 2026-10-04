# Stage 2B — controlled Voyage rerank-3 experiment

## Decision status: UNMEASURED / BLOCKED

**Question:** Did Voyage rerank-3 materially improve Top-10 evidence retrieval
relative to the frozen Voyage-4 cosine baseline, and was the improvement worth
its latency, cost, and complexity?

**Current answer:** **Unmeasured.** This repository checkout does not contain the
large local Stage 1 full-ranking artifact, so validation stopped before client
construction or an API call. No Stage 2B quality, latency, token-usage, or cost
result has been inferred. The blocked record is at
`artifacts/retrieval/stage2b_voyage_rerank3/20261004T_blocked_missing_full_rankings/run_blocked.json`.

| System | Atomic Evidence Recall@10 | Sufficient Evidence@10 | Latency/query | API cost | Status |
|---|---:|---:|---:|---:|---|
| Stage 1 — Voyage-4 cosine | 64/72 (88.9%) | 31/39 (79.5%) | baseline | previously measured | frozen baseline |
| Stage 2A — MiniLM | 56/72 (77.8%) | 27/39 (69.2%) | 1,347.8 ms | $0 | rejected |
| Stage 2B — Voyage rerank-3 | **unmeasured** | **unmeasured** | **unmeasured** | **unmeasured** | blocked locally |

Stage 1's unchanged Top-30 ceiling is 69/72 (95.8%) atomic evidence and
36/39 (92.3%) sufficient questions. Stage 2B is successful only if its **net**
quality improvement is clear and its measured latency, estimated list-price
cost, and added provider dependency are acceptable. An isolated rescue is not a
success when comparable or greater evidence is displaced.

## Controlled implementation

`stage2b_voyage_reranking.py` reads the completed Stage 1 ranking and validates
all four frozen Top-10/Top-30 counts **before any paid request**. It requires
exactly Q001–Q039, selects only explicit ranks 1–30, uses each stored original
`query_text`, and sends all 30 chunk texts in one official `voyageai.Client.rerank`
call with model `rerank-3`, `top_k=None`, and truncation disabled. Every returned
index must occur exactly once. It then orders by descending relevance score and
original Stage 1 rank as the deterministic tie-break.

The output retains all 30 candidates per question, including source, page,
original rank/cosine score, rerank score/rank, query, latency, and provider usage.
It also stores input SHA-256 hashes, requested/returned model metadata, request
and pair counts, configured retry policy, rescue/loss/net counts, sufficiency
transitions, evidence-witness rank changes, and cost distinctions. Actual billed
cost remains unknown because it is not returned by the rerank API.

The official Voyage documentation describes `Client.rerank`, its complete result
index mapping, and `total_tokens`: <https://docs.voyageai.com/docs/reranker>.
The frozen pricing assumption is $0.05 per million processed tokens for
`rerank-3`, sourced from <https://docs.voyageai.com/docs/pricing> on 2026-10-04.
Estimated list-price cost is calculated only from provider-reported tokens. Free
tier or account credits are not interpreted as actual billed cost.

## Exact Mac execution

Place the immutable local artifact at:

`artifacts/retrieval/stage1_voyage4_diagnostics/20261004_full360/full_rankings.json`

It is intentionally gitignored. Then, from the repository root on the owner's
Mac, run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
export VOYAGE_API_KEY='<your Voyage API key>'
PYTHONPATH=src python -m semantic_retrieval.stage2b_voyage_reranking \
  --output artifacts/retrieval/stage2b_voyage_rerank3/20261004_full360/experiment_results.json
pytest -q
```

Do not paste, print, or commit the key. The runner does not persist it. A
completed experiment makes 39 successful requests and scores 1,170
query-document pairs. The SDK is configured for at most two retries after an
initial request and a 60-second timeout. SDK response objects do not expose the
observed retry count, so the output states that limitation rather than inventing
one.

## Required result interpretation

The five reachable baseline failures are Q017 U2 (Stage 1 rank 11), Q030 U1
(13), Q002 U2 (28), Q031 U1 (28), and Q034 U1 (28). The completed output reports
each explicitly. Q034 retains its page-boundary representation complication.

Q037 U2 (rank 40), Q014 U2 (rank 41), and Q008 U4 (rank 106) are outside the
frozen Top-30. They cannot be rescued by Stage 2B, and their continued absence
must not be classified as reranker failure.

## Assumptions, limitations, and implications

- The supplied local artifact is the authoritative completed Stage 1 run; the
  harness rejects it unless deterministic Contract v2 scoring reproduces all
  frozen counts.
- Provider latency depends on network and service conditions. Measurement covers
  each rerank call, not input validation or artifact I/O.
- API failure can leave some requests billable before the final blocked output;
  therefore a failure artifact does not claim zero usage or cost.
- Sending policy chunk text to Voyage is a new external data-flow dependency.
  This corpus is public project material, but private/customer documents must
  not be substituted without an approved data-handling review.
- No embeddings, extraction, chunks, gold evidence, benchmark questions,
  retrieval results, or Stage 2A artifacts are modified. No LLM generation,
  query rewriting, hybrid search, filtering, fine-tuning, or agents are added.

**Recommended next experiment:** none until this single controlled run is
executed and reviewed. Afterward, compare net evidence and sufficiency changes
against measured latency and list-price cost before deciding whether any further
architecture experiment is justified.
