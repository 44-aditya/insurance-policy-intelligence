# Evaluation Contract v2 — Stage 1 stored-results rescore

## Scope and method

This closes Evaluation Contract v2 by applying the owner-approved decisions to the unchanged Experiment 1 rankings. No embeddings, Voyage calls, or retrieval rankings were generated. The v1 artifact remains unchanged, including its 59.3% Recall@10. Contract v2 uses source/document/page-anchored atomic evidence units, exact character-preserving canonicalization, and collective coverage of an authoritative source interval by multiple ranked chunks.

Q040 remains a negative-space/abstention probe and is excluded from both positive denominators. Q029 requires U1/U2/U4/U5/U6/U8 and retains U3/U7 as non-required source units. Q034 requires U1/U2; clause ii is not a unit required by the current question.

## Results

| Metric | @1 | @3 | @5 | @10 |
| --- | ---: | ---: | ---: | ---: |
| Atomic Evidence Recall | 38.9% (28/72) | 63.9% (46/72) | 79.2% (57/72) | **88.9% (64/72)** |
| Sufficient Evidence | 23.1% (9/39) | 53.8% (21/39) | 66.7% (26/39) | **79.5% (31/39)** |

The separately versioned machine-readable artifact contains per-question coverage, each fragment's source interval, witness chunk IDs/ranks, unmatched units, and failure classifications. Incremental API cost was **$0**.

## v1 comparison and measurement-error finding

The immutable v1 result was 32/54 = **59.3% Evidence Recall@10** and 18/39 = **46.2% Sufficient Evidence@10**. V2 is not a silent replacement or a like-for-like denominator: decomposition increases the denominator from 54 spans to 72 required atomic units. On that stricter, auditable representation, the stored rankings score 64/72 = **88.9% Atomic Evidence Recall@10** and 31/39 = **79.5% Sufficient Evidence@10**.

Among the 18 spans in the approved review package that v1 could not map, v2 identifies **16 measurement-contract cases rather than retrieval misses**: annotation/representation/evaluator defects and the two Q040 negative-space spans that never belonged in positive recall. The remaining reviewed cases, Q002 and Q034, are genuine Top-10 failures. Across the complete v2 benchmark, eight questions retain one unmatched required unit each. Thus the original apparent failure was substantially measurement error, while v2 isolates eight genuine question-level retrieval failures rather than claiming they disappeared.

## Remaining genuine failures at Top 10

| Question | Unit | Likely bottleneck | Evidence |
| --- | --- | --- | --- |
| Q002 | U2 | retrieval/ranking | The corrected day-care definition maps to its source page, but no matching chunk is in Top 10. |
| Q008 | U4 | retrieval/ranking | The cataract-list unit maps, but its chunk is absent from Top 10. |
| Q014 | U2 | retrieval/ranking | Exact source mapping exists; no Top-10 witness. |
| Q017 | U2 | retrieval/ranking | Exact source mapping exists; no Top-10 witness. |
| Q030 | U1 | retrieval/ranking | Exact source mapping exists; no Top-10 witness. |
| Q031 | U1 | retrieval/ranking | Exact source mapping exists; no Top-10 witness. |
| Q034 | U1 | retrieval/ranking; chunk boundary/chunking contributes | Rank 2 has the page-15 continuation, but Top 10 lacks the required page-14 opening of the cross-page sentence. |
| Q037 | U2 | retrieval/ranking | Exact source mapping exists; no Top-10 witness. |

There are no remaining failures classified as extraction representation, document/product confusion, or unresolved evaluation issues: approved extraction corruptions have explicit auditable locators, and wrong-document chunks cannot witness a unit.

## Assumptions, limitations, security, and cost

- Compact canonicalization deliberately preserves all letters and numbers. It does not infer spelling variants, repair OCR characters, apply fuzzy matching, semantic similarity, embeddings, or an LLM judge.
- Explicit `extraction_text` locators are limited to reviewed parser corruption while authoritative `text` remains source truth.
- Exact page anchoring means a source fragment absent from extraction cannot be silently credited.
- This rescore measures retrieval evidence availability, not answer generation or abstention quality.
- No new dependency, external input, secret, or customer data was introduced. The corpus is the existing repository corpus.
- Incremental API cost and token consumption are zero because only stored rankings were read.

## Decision / next implication

Evaluation Contract v2 is closed. The next experiment should target the eight isolated retrieval/ranking failures (with Q034's cross-page boundary noted) under a separately approved experiment; benchmark redesign, extraction alternatives, reranking, embeddings, hybrid search, and chunk-size experiments are intentionally outside this task.
