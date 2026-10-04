# Stage 2B — controlled Voyage rerank-3 experiment

## Decision status: measured; Stage 2B hypothesis supported

**Question:** Did Voyage rerank-3 materially improve Top-10 evidence retrieval
relative to the frozen Voyage-4 cosine baseline, and was the improvement worth
its latency, cost, and complexity?

**Answer:** **Yes, for this corpus, benchmark, and frozen configuration.** Voyage
`rerank-3` improved atomic evidence from 64/72 to 68/72 and sufficient questions
from 31/39 to 35/39. It rescued four evidence units, displaced none, and added
approximately 739 ms/query at an estimated incremental API cost of approximately
$0.000644/query. Stage 2B is accepted as the Stage 2 retrieval architecture,
subject to this measured latency/cost trade-off.

This is evidence for **Voyage rerank-3 in this measured setting**, not for
reranking as a generic pattern. Stage 2A remains important counter-evidence: its
MiniLM reranker reduced both quality metrics, rescued nothing, and lost eight
previously covered units.

## Three-system comparison

| System | Atomic Evidence Recall@10 | Sufficient Evidence@10 | Rescue / loss | Mean rerank latency | Reranking cost | Decision |
|---|---:|---:|---:|---:|---:|---|
| Stage 1 — Voyage-4 cosine | 64/72 (88.9%) | 31/39 (79.5%) | baseline | none | none | frozen baseline |
| Stage 2A — MiniLM | 56/72 (77.8%) | 27/39 (69.2%) | 0 / 8 | 1,347.8 ms/query | $0 API | rejected |
| Stage 2B — Voyage rerank-3 | **68/72 (94.4%)** | **35/39 (89.7%)** | **4 / 0** | **738.802 ms/query** | **$0.0251115 total estimated; ~$0.000644/query** | **accepted** |

Using the displayed percentages, Stage 2B improved atomic recall by 5.5
percentage points and sufficient evidence by 10.2 percentage points over Stage
1. The exact fraction deltas are 5.56 and 10.26 percentage points, respectively.
No question became insufficient. Q002, Q030, Q031, and Q034 became sufficient.

The unchanged Top-30 ceiling is 69/72 (95.8%) atomic evidence and 36/39 (92.3%)
sufficient questions. Stage 2B achieved 68/72 and recovered four of the five
additional evidence units available above Stage 1 Top-10. Only one candidate-pool
unit of headroom remains, so further reranker experimentation has limited
potential under the current frozen candidate pool. Do not add another reranker.

## Performance and cost

The experiment evaluated 39 queries and 1,170 query-document pairs. Mean Voyage
reranking latency was 738.8023247949604 ms/query. Multiplying the supplied mean
by 39 gives a derived total of 28,813.290667 ms; this derived value is not
presented as a separately measured total.

Voyage reported 502,230 processed tokens. Estimated experiment cost was
$0.0251115. Dividing by 39 gives $0.0006438846/query, reported operationally as
approximately $0.000644/query. This is an estimated reranking API cost, not an
actual invoice; actual billed cost was not supplied.

## Controlled implementation and provenance

The experiment changed only the reranker. The harness reads the completed Stage
1 ranking, validates the frozen Voyage-4 configuration, exactly Q001–Q039, all
four Top-10/Top-30 Contract v2 counts, and the eight known first-cover ranks
before a paid call. It selects exact ranks 1–30, submits the original `query_text`
and all 30 chunk texts through the official Voyage SDK, and requires every
candidate index exactly once. Equal scores fall back to original Stage 1 rank.

The full local `experiment_results.json` was not available in this environment.
The committed compact summary records only the aggregate measured values supplied
by the owner. It does **not** invent per-unit rescue identities, input hashes,
request or retry counts, returned API model metadata, or actual billed cost. The
earlier blocked artifact remains immutable execution history rather than being
rewritten as if the first attempt had succeeded.

The five Top-30-reachable baseline misses were Q017 U2 (rank 11), Q030 U1 (13),
Q002 U2 (28), Q031 U1 (28), and Q034 U1 (28). The supplied result establishes
four rescues and the four question-level sufficiency transitions above, but does
not include the complete per-unit output, so this report does not assign the four
rescue identities. Q034 retains its page-boundary representation complication.

Q037 U2 (rank 40), Q014 U2 (rank 41), and Q008 U4 (rank 106) remained outside the
Top-30 candidate set and could not be rescued. Their absence is not a Voyage
reranker failure.

## Architecture decision and next stage

**Decision:** accept `Voyage-4 Top-30 → Voyage rerank-3 → Top-10` as the Stage 2
retrieval architecture for this project. The empirical benefit is +4 net evidence
units and +4 sufficient questions, with no regression, for approximately 739 ms
and $0.000644 estimated incremental cost per query.

The value came from the measured performance of Voyage rerank-3 on this corpus
and benchmark, not from reranking as a generic architectural pattern. Preserve
the Stage 2A negative result alongside Stage 2B.

Do not introduce another reranker, fine-tune embeddings, change chunking, add
hybrid search, or add LLM generation in this PR. The next project stage will
separately evaluate answer generation and end-to-end RAG correctness,
faithfulness, citation quality, latency, token consumption, and cost.

## Security and limitations

- `VOYAGE_API_KEY` remains environment-only and is never persisted.
- The API sends benchmark queries and policy chunk text to Voyage. Private or
  customer documents require a separate approved data-handling review.
- Provider/network latency can vary by location and service conditions.
- The conclusion is benchmark-specific and should be reevaluated if the corpus,
  questions, evidence contract, chunks, embeddings, or candidate depth changes.
