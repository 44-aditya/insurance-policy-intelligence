# Page retrieval baseline

Local TF-IDF/cosine lexical vector control; not a pretrained semantic embedding experiment.
170 unchanged pages; 10 draft pilot questions.
Draft labels are provisional and source-selected; these results are diagnostic, not a reviewed benchmark.
Examples-only records are refused. No cleanup, document filtering, reranking, fine-tuning, or generation.

Interim proxy: fraction of questions retrieving ALL distinct annotated PDF pages in top K.
This overestimates usable evidence when tables/words are damaged, and ignores alternative sufficient evidence sets.
Wrong-document counts mean pages outside the annotated source files; they are distractor diagnostics, not relevance judgments.

| Slice | n | Page sufficiency@1 | Page sufficiency@3 | Page sufficiency@5 | Page sufficiency@10 |
| --- | ---: | ---: | ---: | ---: | ---: |
| All | 10 | 30.0% | 40.0% | 60.0% | 80.0% |
| table_dependent | 4 | 75.0% | 75.0% | 100.0% | 100.0% |
| plus_problem_pages | 3 | 0.0% | 0.0% | 66.7% | 100.0% |

MRR at max K: 0.507 (first gold page only).

| Question | First gold rank | Missing gold pages at max K | Wrong-document hits at max K |
| --- | ---: | --- | ---: |
| PILOT-001 | not retrieved | medicare_select_policy_wording_0faeeb61c5.pdf p2 | 4 |
| PILOT-002 | 7 | none | 7 |
| PILOT-003 | 1 | none | 6 |
| PILOT-004 | 1 | none | 1 |
| PILOT-005 | 3 | none | 5 |
| PILOT-006 | 1 | none | 5 |
| PILOT-007 | 7 | none | 9 |
| PILOT-008 | 4 | none | 8 |
| PILOT-009 | 5 | none | 7 |
| PILOT-010 | 1 | medicare_select_policy_wording_0faeeb61c5.pdf p2 | 7 |

Version retrieval: **not testable**. Only one file per product; all explicit versions/dates are null.
Hash-based page IDs distinguish PDF bytes but do not prove currentness. Wrong-product retrieval is measured without gold-derived filtering.
MediCare Plus pages 8/21 contain spurious characters; page 20 interleaves table/prose. Retrieving these pages does not fix their fidelity.
Extraction quote warnings: 0; runtime failures: 0.

Retrieval p50 / p95: 2.722 / 3.764 ms.
Cold index build: 36.859 ms; concurrency 1, one repetition, local warm queries.
Embedding and LLM input/output tokens: 0 (no model called). Lexical term counts are separate, not model tokens.
Paid API cost per experiment: USD 0.00. Compute and human review cost: unknown/unpriced. No claim of zero total cost.
Answer correctness, faithfulness, citation entailment, and generation latency are unmeasured.

Next experiment: independently review/expand pilot labels, then compare a pinned semantic embedding model on the same pages and questions.
Keep extraction unchanged so any gain is attributable to retrieval. Inspect table fidelity before treating page hits as usable evidence.

Experiment ID: `4e37431f33369a0be92198f5c5dee4f1c906584b6b33a6c4e03635436bfe50ee`. Fingerprints and run accounting are in experiment_metrics.json.
