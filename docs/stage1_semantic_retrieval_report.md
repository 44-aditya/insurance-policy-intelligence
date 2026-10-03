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

No live retrieval measurement was performed in this development environment:
`VOYAGE_API_KEY` was absent. The committed machine-readable result records this
blocked status. Therefore no Recall@K, Sufficient Evidence@K, latency, token, or
cost number is reported here. The full local test suite passed with a mock
embedder and requires no key.

## INTERPRETATION

There is no retrieval-quality result to interpret until an authorized run is
made. The absence of a key is an execution constraint, not evidence for or
against semantic retrieval. After a run, classify failures using the persisted
mapping status, wrong-document counts, rank/provenance, span count, difficulty,
format, and product slices before considering any change.

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
  can be large. No credential is persisted.
- The one-time corpus cost is separate from per-run query cost. Local ranking
  incurs no API charge. No inference-generation cost exists in this scope.

The next experiment is simply the authorized run of this fixed configuration,
followed by review of flagged mappings and classified failures. No architecture
change is warranted before those measurements exist.
