# Corpus structure measurements

Generated at **2026-10-03T12:39:14+00:00**. This is measurement only; it does not select or implement a chunking configuration.

## Method and reproducibility

- Token counting: Unicode regex lexical tokens: words/numbers (internal apostrophes retained) and each punctuation mark. This dependency-free proxy is deterministic but is **not** a model tokenizer.
- Percentiles: nearest-rank; means are rounded to one decimal.
- Inputs:
- `artifacts/extraction/policy_pages.jsonl`: SHA-256 `b406c909089a352b2acd83e6c03c6d56037d08d11bd8c993e330581d30883ddc` (170 records)
- `evals/gold_dataset.json`: SHA-256 `db8c834ce4680a895c0be1dc2ec818cf77d7c32d4031782ed2388f62b15bb9e6` (40 records)
- Reproduce from a checkout without installing the package: `PYTHONPATH=src python -m corpus_analysis.analyze --output docs/corpus_structure_report.md`
- Paid model/API cost: **$0** (local Python analysis only).

## Page length (tokens)

| Scope | count | tokens | min | p25 | p50 | mean | p75 | p90 | p95 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Entire corpus | 170 | 93292 | 134 | 471 | 537 | 548.8 | 629 | 700 | 738 | 1765 |
| TATA AIG MediCare Plus | 26 | 18218 | 348 | 564 | 637 | 700.7 | 756 | 783 | 1491 | 1765 |
| TATA AIG MediCare Premier | 60 | 27986 | 232 | 416 | 476 | 466.4 | 517 | 588 | 597 | 629 |
| TATA AIG MediCare Reserve | 40 | 23726 | 278 | 532 | 596 | 593.1 | 650 | 697 | 720 | 760 |
| TATA AIG MediCare Select | 44 | 23362 | 134 | 485 | 556 | 531.0 | 633 | 676 | 692 | 738 |

## Gold evidence spans

Q001-Q039 contain **54** conventional positive-evidence spans.

| Scope | count | min | P25 | P50 | mean | P75 | P90 | P95 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Evidence spans | 54 | 15 | 34 | 64 | 71.0 | 85 | 126 | 170 | 275 |

- Questions with one span: **28**
- Questions with multiple spans: **11**
- Span-count distribution (`spans: questions`): **{1: 28, 2: 7, 3: 4}**
- Q040 is kept separate: abstention/insufficient-evidence probe; not conventional positive evidence. It has 2 nearby/context spans of [37, 38] tokens; they are excluded from positive-evidence statistics and chunk exceedance rates.

## Approximate section/clause length

The heuristic joins extracted pages per source, then starts a clause at a short line (at most 120 characters and 18 lexical tokens) that either begins with `Section`, a numeric/Roman/alphabetic marker, or is all uppercase. It found **872** blocks.

| P50 | P75 | P90 | P95 | max |
|---:|---:|---:|---:|---:|
| 38 | 115 | 277 | 452 | 1693 |

## Candidate fixed-size implications

Chunk counts split each extracted page independently as `ceil(page tokens / size)` and therefore estimate fixed chunks **before overlap**. This is an arithmetic comparison, not an implemented chunker.

| Size | Gold spans longer | Heuristic clauses longer | Approx. chunks |
|---:|---:|---:|---:|
| 256 | 1 (1.9%) | 91 (10.4%) | 446 |
| 512 | 0 (0.0%) | 35 (4.0%) | 274 |
| 768 | 0 (0.0%) | 11 (1.3%) | 175 |
| 1024 | 0 (0.0%) | 4 (0.5%) | 172 |

The clause-exceedance column provides a corpus-based fragmentation indicator; the gold-span exceedance column is a lower bound because even a shorter span can cross a fixed boundary. Smaller candidates also create more boundaries and therefore more opportunities to split content. These measurements do not evaluate retrieval precision, ranking dilution, latency, or downstream token cost. No candidate is declared optimal.

## Limitations and assumptions

- Lexical-token counts differ from embedding-model tokens; rerun with the eventual model tokenizer before locking configuration.
- Headers, footers, and extraction artifacts remain in page counts because the existing page-level output is measured as-is.
- Heading detection is intentionally shallow. It can mistake numbered list items or repeated uppercase furniture for clauses, miss wrapped/stylized headings, and count repeated page furniture inside a block. The maximum is especially sensitive to missed headings.
- Evidence spans measure individually annotated spans, not the distance between multiple spans or the context needed to interpret them. Fixed chunks can split spans shorter than the chunk due to boundary position, so exceedance is a lower bound on fragmentation risk.
- The chunk-count estimate preserves page boundaries and assumes no overlap, header removal, section-aware splitting, or cross-page chunks.
- The gold dataset is draft and small; Q040 requires a separate abstention protocol.

## Recommended next experiment

Have the architect select one or more candidate configurations, then measure retrieval Recall@K, ranking quality, citation accuracy, latency, and token/cost effects against this gold set. That experiment—not this descriptive analysis—should drive configuration choice.
