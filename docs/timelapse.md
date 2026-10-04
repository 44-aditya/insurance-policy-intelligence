# Project timelapse

This is the curated engineering, product, and learning narrative of the Insurance
Policy Intelligence Platform. It supports future reference, deep GenAI learning,
architectural decision recall, portfolio storytelling, and interview preparation.
It preserves failed assumptions, reversals, and deferred decisions rather than
turning the project into a retrospective success story.

Each material milestone records **Context / Hypothesis → What we did → Evidence /
Result → Aha / Learning → Decision / Next implication**. Entries below through
2026-10-03 are reconstructed on 2026-10-04 from the linked repository evidence
and Git history, not recovered verbatim task responses. The 2026-10-04 entries
are contemporaneous with this conversation. Dates identify recorded milestones,
not assumed deployment or approval dates.

[Raw task outputs](task_outputs/README.md) preserve complete agent responses.
Formal experiment artifacts and reports remain authoritative for reproducible
metrics; this narrative distinguishes measured outcomes from interpretations.
Never put credentials, secrets, API keys, environment-variable values, or other
sensitive information in either record.

## 2026-10-02 — Product boundary and evaluation-first architecture (reconstructed)

- **Context / Hypothesis:** document-grounded policy explanations are a plausible
  initial use case; validated user demand and personalized coverage capabilities
  were not established.
- **What we did:** defined operating principles and a proposed Stage 1 answer
  contract: preserve qualifications, provide resolvable evidence, and abstain
  when documents cannot establish the answer.
- **Evidence / Result:** [AGENTS.md](../AGENTS.md) and
  [problem definition](problem_definition.md); commits `52ab465`, `a8e6050`.
  The problem definition explicitly records assumptions and open product questions,
  not implemented capabilities or user-research results.
- **Aha / Learning:** finding policy language is different from adjudicating a
  person's claim. Customer data, deterministic rules, and current external facts
  require capabilities beyond document retrieval.
- **Decision / Next implication:** start with vector retrieval and eventual LLM
  generation; add reranking, rules, or agents only when measured failures justify
  them. Target-user validation remains open; the human architect decides changes.

## 2026-10-02 — Official corpus acquired after automated access failed (reconstructed)

- **Context / Hypothesis:** evaluation needs an authoritative, versioned source;
  similar brochures or third-party copies could create misleading evidence.
- **What we did:** narrowed the corpus to official Tata AIG Policy Wordings for
  Select, Plus, Premier, and Reserve. After cloud acquisition failed, the owner
  manually downloaded the four PDFs; identity and preserved bytes were verified.
- **Evidence / Result:** [corpus record](../corpus/README.md),
  [manifest](../corpus/metadata.json); commits `87b33e3`, `510a884`, `8d21e30`,
  PR #3. Unknown version/effective-date fields remain null; Premier's UIN was not
  guessed from its insufficiently legible representation.
- **Aha / Learning:** provenance is an experimental control, and acquisition can
  require human assistance. Missing metadata is preferable to invented precision.
- **Decision / Next implication:** keep PDFs byte-for-byte; generated derivatives
  belong outside the authoritative corpus. Additional source classes are deferred
  until their impact can be measured separately.

## 2026-10-03 — Successful extraction did not establish text fidelity (reconstructed)

- **Context / Hypothesis:** local page-level PyMuPDF extraction could provide a
  minimal Stage 1 baseline without OCR or a document framework.
- **What we did:** extracted unchanged page text and visually reviewed selected
  pages, tables, clauses, and reading order.
- **Evidence / Result:** [extraction report](extraction_quality_report.md) and
  [metrics](../artifacts/extraction/extraction_metrics.json); commits `7ae48f5`,
  `d101577`, PR #5. Four PDFs produced 170 pages and 500,188 characters, with zero
  blank pages and no parser errors; paid API cost was zero. Plus nevertheless
  contained intra-word fragmentation, table/prose interleaving on page 20, and
  spurious character blocks on pages 8 and 21. Page furniture remained on all pages.
- **Aha / Learning:** coverage and exception-free parsing are not accuracy metrics.
  The baseline is usable experimentally, not uniformly faithful or production-ready.
- **Decision / Next implication:** retain these defects for the first retrieval
  experiment and classify failures by document/page before choosing cleanup,
  layout-aware extraction, or OCR. No OCR requirement was established.

## 2026-10-03 — Gold validity separated from extraction diagnostics (reconstructed)

- **Context / Hypothesis:** a benchmark anchored to future chunks or imperfect
  parser output would entangle truth with implementation choices.
- **What we did:** separated hard schema/source/page validation from soft text
  diagnostics, then added Benchmark Specification v1 and a draft gold dataset.
- **Evidence / Result:** [annotation contract](gold_dataset_annotation.md),
  [benchmark specification](../evals/benchmark_spec_v1.csv),
  [gold dataset](../evals/gold_dataset.json); commits `f34bc96`, `476fa7f`,
  PRs #6 and #8. The draft contains 40 questions; Q001–Q039 have 54 positive
  spans, while Q040 is an insufficient-evidence probe with two contextual spans.
- **Aha / Learning:** PDF truth must survive parser changes. Hard validation cannot
  prove quote fidelity, answer support, or sufficient evidence; those need review.
- **Decision / Next implication:** extraction mismatches warn rather than invalidate
  gold. Keep status draft pending review; abstention needs a separate protocol.

## 2026-10-03 — Measured corpus structure before selecting chunks (reconstructed)

- **Context / Hypothesis:** chunk-size selection should follow corpus evidence,
  rather than a familiar default or framework preference.
- **What we did:** measured page, heuristic clause, and gold-span lengths with a
  deterministic lexical-token proxy and compared candidate sizes.
- **Evidence / Result:** [structure report](corpus_structure_report.md); commit
  `c1b2f5d`, PR #9. Across 170 pages there were 93,292 proxy tokens; the 54 positive
  spans had median 64 and maximum 275 proxy tokens. The 512-token candidate implied
  274 chunks before overlap and no overlength gold spans under that proxy. This
  did not establish an optimal configuration or evaluate retrieval. Cost was zero.
- **Aha / Learning:** proxy tokens are not model tokens; a span shorter than a
  chunk can still cross its boundary. Size exceedance is only a lower bound on
  fragmentation risk.
- **Decision / Next implication:** measure a concrete retrieval configuration with
  the eventual model tokenizer; defer claims about quality or optimal chunk size.

## 2026-10-03 — Experiment 1 implemented, initially blocked, then measured (reconstructed)

- **Context / Hypothesis:** fixed chunks and semantic embeddings could isolate the
  first retrieval baseline without generation, reranking, or a vector database.
- **What we did:** PR #10 / commit `a08481a` added page-bounded 512-token chunks,
  100-token overlap, Voyage `voyage-4` 1,024-dimensional embeddings, local cosine
  ranking, and PDF-anchored full-span evaluation. The initial implementation
  recorded `not_run_missing_api_key`; a subsequent run completed with start
  timestamp `2026-10-03T14:51:04.306298+00:00` and Python 3.12.15.
- **Evidence / Result:** [original measured artifact](../artifacts/retrieval/stage1_voyage4/retrieval_results.json)
  and [experiment report](stage1_semantic_retrieval_report.md). The recorded
  measurements are preserved below, not replaced with later interpretations.

| K | Original Evidence Recall@K | Original Sufficient Evidence@K | Coverage |
|---|---:|---:|---|
| 1 | 0.2222222222222222 | 0.07692307692307693 | 12/54 spans; 3/39 questions |
| 3 | 0.37037037037037035 | 0.28205128205128205 | 20/54 spans; 11/39 questions |
| 5 | 0.46296296296296297 | 0.358974358974359 | 25/54 spans; 14/39 questions |
| 10 | 0.5925925925925926 | 0.46153846153846156 | 32/54 spans; 18/39 questions |

- **Evidence / Result (operations):** 360 chunks; documents used 150,615 API tokens,
  six calls, 9286.665458930656 ms, and estimated USD 0.0090369. Forty queries used
  517 API tokens, 40 calls, 15093.337207799777 ms, and estimated USD 0.00003102.
  Total estimated list-price cost: USD 0.00906792. Local ranking totaled
  2607.787664514035 ms. No per-question execution failures were recorded.
  Component timings do not establish wall time; estimated cost is not an invoice.
- **Aha / Learning:** a missing credential is an execution constraint, not negative
  retrieval evidence. A completed run makes protocol-specific scores observable,
  but does not by itself validate the benchmark or matching method.
- **Decision / Next implication:** investigate mapping warnings and classified
  failures before attributing low scores to ranking or proposing architecture.

## 2026-10-04 — Evaluation limitations changed the interpretation (contemporaneous)

- **Context / Hypothesis:** low Recall might indicate retrieval weakness, but the
  completed artifact also flagged evidence-mapping failures.
- **What we did:** inspected all 18 unmatched spans against gold, raw page text,
  page chunks, nearby pages, and recorded retrieval hits without modifying inputs
  or rerunning embeddings. Preserved the complete available
  [raw task output](task_outputs/2026-10-04_001_unmatched-evidence-root-cause-analysis.md).
- **Evidence / Result:** 38/56 spans matched and 18 were unmatched; two unmatched
  spans belong to excluded Q040. Primary causes: seven annotation/page-reference,
  four extraction representation, one chunk-coverage, six evaluator-matching.
  Twelve spans have full cited meaning in a retrieved chunk but no evaluator match.
  These are qualitative potential false negatives, not officially rescored results.
- **Aha / Learning:** evidence mapping is part of the measurement system. Missing
  punctuation, list markers, stitched quotations, damaged words, and cross-page
  locators can look like retrieval misses. The original metrics are valid records
  of the implemented protocol but **provisional for architectural conclusions**.
  Sixteen unmapped scored spans cap attainable Recall at 38/54 under this protocol,
  regardless of ranking. Q012 also demonstrates the earlier boundary-risk warning:
  chunk 0 ends nine normalized characters before the evidence ends, while chunk 1
  lacks the opening. Q034's opening is on page 14 despite a page-15 annotation.
  Plus Q033/Q038/Q039 expose readable supporting content despite extraction damage
  and/or discontinuous annotation; Q040 remains outside positive Recall scoring.
- **Decision / Next implication:** preserve the measured artifact unchanged; do
  not infer a need for reranking, a parser replacement, or larger chunks yet.
  Human PDF review and an explicit evaluation-contract decision come first.
  Potential follow-up evaluation can reuse stored retrieval hits, avoiding another
  embedding charge; changed gold/protocol and any new scores need separate provenance.
  The analysis did not visually adjudicate authoritative PDF corrections.

## 2026-10-04 — Preserve raw work and curated learning (contemporaneous)

- **Context / Hypothesis:** manually copying agent responses loses detailed
  diagnostics, while response dumps alone obscure the project's learning narrative.
- **What we did:** established `docs/task_outputs/` for complete final responses,
  this timelapse for curated milestones, and permanent instructions in `AGENTS.md`.
  Updated the Stage 1 report to reflect the completed run and evaluation limitations.
  Excluded the generated vector cache from Git while retaining it locally.
- **Evidence / Result:** the first raw record preserves the full available
  root-cause response with portable links. Earlier milestones above have explicit
  repository evidence and reconstruction labels; unavailable historical responses
  were not invented. Documentation changes do not change the measured artifact,
  gold, extraction, chunking, evaluator, or retrieval implementation.
- **Aha / Learning:** raw provenance and curated reflection serve different needs.
  Keeping the original measurement and subsequent qualification visible supports
  reproducibility and an honest engineering/interview narrative.
- **Decision / Next implication:** record future material task responses and
  milestones in their respective locations; never store sensitive values. Formal
  artifacts/reports retain metric authority. Tests and the full review diff are
  recorded in this task's final output; commit/push remain deferred to owner review.
