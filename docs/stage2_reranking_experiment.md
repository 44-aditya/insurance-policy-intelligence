# Stage 2 controlled reranking experiment

## Decision status: measured; Stage 2A hypothesis rejected

The Stage 2A harness was executed locally against the real completed Stage 1
`20261004_full360/full_rankings.json`. The measured result is negative:

> **Stage 2A hypothesis rejected. `cross-encoder/ms-marco-MiniLM-L6-v2`
> materially degraded retrieval quality while adding latency. This result
> rejects this reranker/configuration, not reranking as an architectural
> pattern.**

The earlier repository-only attempt remains preserved as a blocked-run artifact
because that checkout did not contain the full-ranking input. It is an execution
history record, not the final experimental outcome.

## Controlled variable and model selection

The sole new ranking variable is
[`cross-encoder/ms-marco-MiniLM-L6-v2`](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2),
pinned to model revision `f130f2b05c9b70e021b4833afe43c6993e2c7563`.
Its model card identifies it as an English passage-ranking cross-encoder trained
on MS MARCO, reports 22.7M parameters, Apache-2.0 licensing, and 74.30 NDCG@10
on TREC-DL 2019 / 39.01 MRR@10 on MS MARCO dev. That is an appropriate,
deliberately small first test of query-passage interaction, not evidence of
insurance-domain quality. The card's 1,800 documents/second figure was measured
on a V100 GPU and is not used as an expected CPU measurement.

The model runs locally: there is no per-request API or token charge. A first run
may download roughly 91 MB of safetensors plus tokenizer/config files; model
files remain in the external Hugging Face cache and must not be committed.
Incremental API cost is therefore $0/query, while local compute cost is unknown
until the owner assigns a machine price. Expected trade-offs are 1,170 pair
scores per experiment (39 × 30), model-download/storage overhead, model loading,
and materially more CPU latency than cosine sorting. The harness measures every
30-pair prediction call rather than substituting a vendor benchmark.

The major new failure modes are model-download/cache failure, CPU/device
variance, cross-encoder truncation at 512 tokens for the combined query/passage,
domain shift from web passage training, and displacement of already-retrieved
evidence. Every displacement is explicitly reported.

## Reproduction

Use the completed, immutable diagnostic at:

`artifacts/retrieval/stage1_voyage4_diagnostics/20261004_full360/full_rankings.json`

Then run:

```bash
python -m pip install -e '.[stage2,test]'
PYTHONPATH=src python -m semantic_retrieval.stage2_reranking \
  --rankings artifacts/retrieval/stage1_voyage4_diagnostics/20261004_full360/full_rankings.json \
  --output artifacts/retrieval/stage2_minilm/20261004_full360/experiment_results.json
pytest -q
```

The runner verifies a completed artifact with exactly Q001–Q039, selects exactly
Stage 1 ranks 1–30, scores all 30 query/passage pairs, breaks equal reranker
scores by original rank, keeps 10, and invokes the existing deterministic
Evaluation Contract v2 `score_unit` implementation for both arms. Q040 is
excluded. Inputs are SHA-256 fingerprinted in a completed result; no embedding
vectors, model weights, credentials, or document caches are written.

## Measured results

| Metric | Stage 1 | Stage 2A MiniLM | Change |
|---|---:|---:|---:|
| Atomic Evidence Recall@10 | 64/72 (88.9%) | 56/72 (77.8%) | −8 units / −11.1 pp |
| Sufficient Evidence@10 | 31/39 (79.5%) | 27/39 (69.2%) | −4 questions / −10.3 pp |

The unchanged Stage 1 Top-30 candidate pool contained 69/72 evidence units
(95.8%) and was sufficient for 36/39 questions (92.3%). Despite that available
headroom, MiniLM rescued **zero** missing evidence units and displaced **eight**
units that Stage 1 had already covered. The supplied measured summary reports
the counts but not the eight unit identities; this report does not invent them.

Reranking scored 1,170 query-document pairs in 52,562.843 ms total, or
1,347.8 ms/query across 39 positive questions. It used no API calls and incurred
$0 API cost. Local compute cost was not priced. Thus the measured configuration
both reduced quality and added about 1.35 seconds of reranking latency per query,
plus the previously documented local model/dependency complexity.

No LLM answer generation was introduced. Stage 1 extraction, chunking,
embeddings, dimensions, gold evidence, Evaluation Contract v2, and rankings
remain unchanged.

## Candidate-depth limitations

Only Q017 U2 (rank 11), Q030 U1 (13), Q002 U2 (28), Q031 U1 (28), and Q034 U1
(28) are inside the candidate pool among the eight known failures. Q037 U2 (40),
Q014 U2 (41), and especially Q008 U4 (106) are structurally unreachable at
candidate depth 30. Q034 also retains its known page-boundary representation
complication; reranking cannot repair representation.

## Architectural verdict

Reranking with this MiniLM model and fixed configuration did **not** materially
improve retrieval relative to cost and complexity; it materially worsened both
quality metrics while adding latency. Preserve this as negative experimental
evidence. Do not promote this configuration, do not introduce another reranker
in PR #16, and do not generalize the result into a rejection of reranking as a
whole architectural pattern.
