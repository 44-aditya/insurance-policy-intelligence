# Stage 1 semantic vector retrieval experiment

## Scope

This is the smallest experiment that isolates semantic retrieval over the
unchanged PyMuPDF page extraction: fixed-size chunks → Voyage `voyage-4` → local
float vectors → query embedding → cosine Top-K → PDF-anchored gold evaluation.
There is no generation, reranking, extraction cleanup, fine-tuning, structured
rule system, agent, or vector database.

## Reproduction and configuration

```bash
python -m pip install -e '.[test]'
export VOYAGE_API_KEY='...'
run-semantic-retrieval --config configs/stage1_voyage4.json
```

The configuration selects `voyage-4`, 1,024-dimensional float embeddings,
512-token chunks, 100-token overlap, and K = 1, 3, 5, 10. Corpus calls use
`input_type="document"`; each benchmark question uses `input_type="query"`.
Truncation is disabled so an unexpected oversize input fails rather than
silently changing the experiment. `VOYAGE_API_KEY` is mandatory and is neither
accepted as a command argument nor persisted.

### Token/counting method

The chunker uses the model-specific open tokenizer loaded by
`voyageai.Client.tokenizer("voyage-4")`. Voyage publishes this tokenizer through
its Hugging Face repository; first use can therefore require network/cache
access even before an embedding request. Token character offsets are used to
slice the **original extracted text**, rather than decoding and potentially
rewriting it.

This is not the Unicode lexical proxy in `corpus_structure_report.md`. That
proxy counts words/numbers and punctuation with a repository regex and was
explicitly only descriptive. Here, “512 tokens” means at most 512 tokens emitted
by the configured Voyage tokenizer. Each extracted page is independently
windowed at token offsets 0, 412, 824, and so on. Thus consecutive full chunks
share exactly 100 tokenizer tokens; a final chunk can be shorter. Chunks never
cross either a page or document boundary, so every chunk has one unambiguous
source file and page. Whitespace outside the first/last token is not embedded.

Chunk IDs are SHA-256-derived from source filename, one-based page number, and
page-local chunk index. They are stable for the fixed input and configuration,
but content fingerprints—not IDs alone—must be used to compare changed inputs.

## Gold mapping and metrics

Gold stays anchored to PDF source/page/text. Mapping first restricts candidates
to the annotated source file and page, then applies Unicode NFKC normalization,
case folding, smart-quote/dash canonicalization, and whitespace collapse to both
gold and chunk text. A span is covered when its full normalized text is a
substring of at least one retrieved candidate chunk. If it does not fit wholly
inside any chunk it is not covered. Multiple overlapping chunks may validly map
to the same single page occurrence. Zero page/chunk matches, or repeated
normalized occurrences on the page, are flagged `human_review_required` in the
machine output.

For Q001–Q039, Evidence Recall@K is covered required spans divided by all
required spans. Sufficient Evidence@K is one only when **every** required span
for that question is covered; its dataset value is the mean over questions.
Q040 is retained in output but explicitly excluded from both positive-evidence
aggregates. This experiment does not define an abstention metric for it.

Per-question output records ranks, scores, chunk/page/product provenance,
retrieval and query-embedding latency, token usage when returned, errors,
wrong-document counts, mappings, and metrics at every K. Aggregate slices cover
difficulty, single/multi-span, evidence format (including table), and gold
product/document. MediCare Plus mappings requiring review are separately listed;
this identifies extraction-problem areas without changing extraction.

## Observability and cost

`retrieval_results.json` fingerprints the config-relevant inputs and records
timestamps, model/dimension/chunk settings, corpus chunk/token/call/latency totals,
and separate query token/call/latency totals. `vectors.json` is the transparent
local vector store. Retrieval latency measures only in-memory cosine ranking.

The configured list price is **US$0.06 per million tokens**, captured from the
[official Voyage pricing page](https://docs.voyageai.com/docs/pricing) on
2026-10-03. Estimates multiply API-reported tokens by that rate and intentionally
do not claim the account's actual bill (free credits and pricing changes may
apply). If the API does not provide token usage, cost remains `null`; it is never
invented.

## MEASURED RESULTS

The initial implementation at `a08481a` recorded `not_run_missing_api_key`:
the development environment lacked a key, so no live metrics were claimed then.
A subsequent completed run recorded start timestamp
**2026-10-03T14:51:04.306298+00:00** with Python **3.12.15**. Its original
[machine-readable results](../artifacts/retrieval/stage1_voyage4/retrieval_results.json)
are preserved unchanged by the 2026-10-04 documentation and analysis task.
The timestamp is the runner's start timestamp, not a completion timestamp.

The run generated and embedded **360 chunks**, attempted **40 questions**, and
recorded **no per-question execution failures**. Q001–Q039 contribute 54 spans
across 39 questions; Q040 is excluded from positive-evidence aggregation.

| K | Evidence Recall@K | Covered spans | Sufficient Evidence@K | Fully supported questions |
|---|---:|---:|---:|---:|
| 1 | 0.2222222222222222 | 12/54 | 0.07692307692307693 | 3/39 |
| 3 | 0.37037037037037035 | 20/54 | 0.28205128205128205 | 11/39 |
| 5 | 0.46296296296296297 | 25/54 | 0.358974358974359 | 14/39 |
| 10 | 0.5925925925925926 | 32/54 | 0.46153846153846156 | 18/39 |

These are the original measurements under the implemented matching protocol,
not corrected semantic-coverage scores. Their use for architectural conclusions
is **provisional** for the reasons below.

| Operation | API-reported tokens | API calls | Recorded latency (ms) | Estimated list-price USD |
|---|---:|---:|---:|---:|
| Document embedding | 150,615 | 6 | 9286.665458930656 | 0.0090369 |
| Query embedding | 517 | 40 | 15093.337207799777 | 0.00003102 |
| Total embedding (sum) | 151,132 | 46 | 24380.002666730433 | 0.00906792 |

Summing per-question local ranking timings gives **2607.787664514035 ms**,
or **65.19469161285087 ms/query** on average (range
50.23937486112118–73.5133329872042 ms). These component timings do not measure
complete experiment wall time, tokenizer loading, or all artifact I/O.
Chunk metadata totals **150,807 tokenizer tokens**, distinct from the
**150,615 API-reported document tokens** used for cost estimation. The artifacts
do not establish why the counts differ; do not substitute one for the other.

The 360 cached vectors are finite and 1,024-dimensional, and their IDs match
chunk order. Both input SHA-256 fingerprints match the files inspected on
2026-10-04. The gold dataset remains **draft**. Checks above are local artifact
consistency checks, not another paid run.

### Evidence-mapping limitations found on 2026-10-04

Of **56 total spans**, **38 matched** and **18 were unmatched**; no ambiguous
matches were recorded. Two unmatched spans belong to excluded Q040, leaving
**16 unmatched spans among the 54 scored spans**. Under the unchanged evaluator,
these 16 spans cannot receive credit at any K, regardless of ranking. Even
retrieving every chunk would therefore cap this run's Evidence Recall at
38/54 (approximately 70.37%). This is a protocol limitation, not a corrected score.

The [complete raw root-cause analysis](task_outputs/2026-10-04_001_unmatched-evidence-root-cause-analysis.md)
inspected gold, raw extracted pages, generated chunks, and stored retrieval hits.
Its primary classifications are:

| Primary failure category | Spans |
|---|---:|
| Gold annotation/page-reference issue | 7 |
| Extraction representation issue | 4 |
| Chunk-boundary/coverage issue | 1 |
| Evaluator matching issue | 6 |
| Unresolved / requires human PDF review | 0 |

These classifications are qualitative artifact analysis; they do not establish
PDF-authoritative corrections. Visual PDF review remains appropriate before
changing gold. Cases can have secondary causes.

- **Q012, span 2:** the complete normalized evidence occurs once on Premier page
  17, at normalized character offsets `[1010,1839)`. Chunk 0 ends at `1830`, nine
  characters short; chunk 1 contains the ending but lacks the beginning. The
  chunks are retrieved at ranks 1 and 3. Collective coverage is available at
  K≥3, but neither chunk meets the evaluator's full-span requirement.
- **Q034:** gold assigns a cross-page, discontinuous passage to Plus page 15.
  Its opening is on page 14; page-15 chunk 0, retrieved at rank 2, preserves the
  continuation and balance-claim provision.
- **Plus Q033/Q038/Q039:** supporting meaning is retrieved despite fragmented
  words, soft hyphens, inserted page furniture, and/or discontinuous gold quotes.
  Q040's cancellation and entire-contract spans also have damaged word spacing,
  but are excluded from Recall aggregation and not retrieved in the top 10.
- **12 potential full-span semantic false negatives:** Q004, Q007, Q008, Q010,
  Q011, Q019, Q026, Q027, Q028, Q033, Q038, and Q039. Their full cited meaning
  appears in a retrieved chunk at the K thresholds documented in the raw analysis,
  while the evaluator grants no match. They must not be silently credited or
  used to publish revised metrics without an explicit reviewed protocol.

Human-review items occur in Q002, Q004, Q007, Q008, Q010, Q011, Q012, Q019,
Q026, Q027, Q028, Q029, Q033, Q034, Q038, Q039, and Q040 (two spans).
The dedicated MediCare Plus review list is Q033, Q034, Q038, Q039, Q040.

## INTERPRETATION

The original scores increase with K, but low scores cannot yet be attributed
solely to embedding or ranking quality. Exact contiguous matching conflates
retrieval misses with annotation differences, extraction damage, and chunk
coverage. Useful evidence was retrieved in 12 unmapped cases; Q012 additionally
shows that overlap does not guarantee full-span containment.

At K=10 the recorded product Evidence Recall values are Plus 0.4, Select 0.6,
Premier 0.7058823529411765, and Reserve 0.5833333333333334. Plus's lower score
is consistent with known extraction defects, but these confounded scores do not
prove that extraction is the sole cause or that a new parser would improve
retrieval. No reranker, parser replacement, larger chunk setting, or additional
architecture is justified by these measurements alone.

First review authoritative PDF evidence and the evaluation contract. Preserve
this original result and label any later corrected gold/protocol and derived
scores as a separate evaluation with its own provenance. No corrected metrics
or answer-generation quality measurements are reported here.

### Assumptions, limitations, and failure modes

- Full-string normalized matching is conservative: an otherwise relevant chunk
  that omits part of an annotated span does not cover it.
- Page-bounded chunking can produce short chunks and cannot use cross-page
  context; this is deliberate provenance-preserving behavior.
- The tokenizer artifact is fetched/cached externally and may be unavailable;
  the experiment fails rather than substituting a misleading token proxy.
- API/network/rate-limit failures are recorded per question after successful
  corpus embedding. A corpus-embedding failure aborts because retrieval cannot
  proceed.
- Local vectors contain derived representations of the public policy corpus and
  can be large. `vectors.json` is a generated 7,817,362-byte cache excluded from
  Git; retain the local file to avoid unnecessary repeat embedding charges.
  Its standalone format lacks input/config/model fingerprints, so keep it with
  the corresponding results and chunks. No credential is persisted. The inspected
  artifacts contain no detected secrets or sensitive local paths.
- The one-time corpus cost is separate from per-run query cost. Local ranking
  incurs no API charge. No inference-generation cost exists in this scope.

The next step is human PDF review of flagged annotations and an explicit decision
on contiguous spans, formatting tolerance, and collective chunk coverage. After
that decision, evaluate a separately versioned protocol against the preserved
retrieval hits where possible; this need not require another embedding run.
Any later chunking or extraction experiment must compare against the preserved
baseline and measure quality, latency, cost, complexity, and new failure modes.
