# Stage 2 controlled reranking experiment

## Decision status: blocked; no quality result claimed

The repository snapshot contains the Stage 1 Top-10 artifact and a failed
full-ranking diagnostic, but not the completed `full_rankings.json` containing
all 30 candidates per positive question. The baseline totals and eight
first-cover ranks supplied with the task do not identify the other candidates
or their order. Reconstructing them would fabricate an experiment input, and
rerunning Voyage would violate the requirement to reuse the completed artifact.
The harness and its tests are complete, but **the hypothesis has not been
measured**, so there is no evidence yet that reranking materially improves
quality relative to latency, cost, or complexity.

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

Place the completed, immutable diagnostic at (or pass its actual path instead of):

`artifacts/retrieval/stage1_voyage4_diagnostics/<run>/full_rankings.json`

Then run:

```bash
python -m pip install -e '.[stage2,test]'
PYTHONPATH=src python -m semantic_retrieval.stage2_reranking \
  --rankings artifacts/retrieval/stage1_voyage4_diagnostics/<run>/full_rankings.json \
  --output artifacts/retrieval/stage2_minilm/<run>/experiment_results.json
pytest -q
```

The runner verifies a completed artifact with exactly Q001–Q039, selects exactly
Stage 1 ranks 1–30, scores all 30 query/passage pairs, breaks equal reranker
scores by original rank, keeps 10, and invokes the existing deterministic
Evaluation Contract v2 `score_unit` implementation for both arms. Q040 is
excluded. Inputs are SHA-256 fingerprinted in a completed result; no embedding
vectors, model weights, credentials, or document caches are written.

## Required interpretation once unblocked

The output contains both aggregate metrics, per-question unit witnesses,
rescued/lost units, all final Top-10 rankings, prediction latency total and mean,
pair/API/token counts, costs, and errors. Compare its recomputed Stage 1 arm to
the frozen expected baseline before accepting the run:

| Metric | Frozen Stage 1 expected |
|---|---:|
| Atomic Evidence Recall@10 | 64/72 (88.9%) |
| Sufficient Evidence@10 | 31/39 (79.5%) |
| Atomic Evidence Recall@30 | 69/72 (95.8%) |

Only Q017 U2 (rank 11), Q030 U1 (13), Q002 U2 (28), Q031 U1 (28), and Q034 U1
(28) are inside the candidate pool among the eight known failures. Q037 U2 (40),
Q014 U2 (41), and especially Q008 U4 (106) are structurally unreachable at
candidate depth 30. Q034 also retains its known page-boundary representation
complication; reranking cannot repair representation.

**Answer to the experiment question:** not yet measurable. Do not recommend
Stage 3 or any further architecture change until a real completed result exists.
