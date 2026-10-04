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

## 2026-10-04 — Evaluation Contract v2 design (contemporaneous; pending owner approval)

**Context / Hypothesis.** Experiment 1 used a full, contiguous normalized-substring match. Root-cause review of 18 unmatched spans showed that this measurement mixed genuine retrieval misses with punctuation/spacing, list structure, discontinuous annotations, chunk/page boundaries, and extraction corruption. The hypothesis was that a better measurement contract could separate source truth from system representations without adding a subjective judge.

**What we did.** Designed—but did not implement or score—a v2 contract based on PDF-authoritative atomic evidence units, contiguous source fragments, conservative deterministic lexical canonicalization, and ordered collective coverage across Top-K chunks. Compared deterministic normalization, atomic decomposition, collective coverage, fuzzy matching, semantic matching, and LLM judging. Treated Q040 separately as an abstention/negative-space probe.

**Evidence / Result.** The proposed rules explain the heterogeneous cases without granting blanket credit: Q012 becomes a test of two-chunk collective coverage; Q002 remains a Top-10 miss after transcription review; Q034 remains incomplete because the necessary Plus page-14 evidence was not retrieved; and Q040 remains outside positive Evidence Recall. Semantic and LLM matching add cost and false-positive/audit risk not justified by current evidence. No replacement metrics were calculated and no paid calls were made.

**Aha / Learning.** A gold quotation is not necessarily a defensible scoring atom. The benchmark must model required propositions and their source fragments, while the evaluator—not gold—absorbs benign representation variation and chunk-boundary effects. Negative-space questions require a different contract from positive evidence retrieval.

**Decision / Next implication.** Recommendation pending human approval: adopt the smallest deterministic v2—atomic units/sets, conservative character-preserving normalization, and source-anchored Top-K union coverage—while retaining v1 for reproducibility. Human PDF review and a blinded/adversarial matcher calibration set should precede implementation or any separately reported v2 rescore. Experiment 1 metrics remain immutable.

## 2026-10-04 — Authoritative evidence review resolved PDF ambiguities (contemporaneous; pending owner approval)

**Context / Hypothesis.** The v2 design deliberately left Q002, Q034, and Q038
dependent on visual PDF adjudication rather than treating extraction as source
truth. A human-review package was needed before changing the benchmark or
evaluator.

**What we did.** Visually inspected the authoritative PDF pages for all 18
unmatched spans, compared them with current gold, unchanged PyMuPDF output, and
stored chunks/ranks, and proposed atomic units and contiguous source fragments in
[the owner review package](evaluation_contract_v2_review.md). Retrieval was not
rerun and no benchmark or implementation artifact changed.

**Evidence / Result.** Q002's PDF visibly says `General or Local Anesthesia` and
`24 hrs`, confirming a real transcription correction. Q034 clause i visibly
begins on page 14 and continues on page 15, confirming the locator correction and
a genuine Top-10 miss for its required opening. Q038 visibly says `maximum`; its
apparent `max` discrepancy was created by fragmented extraction, so it requires
evaluator handling rather than a wording correction. Across the 18 spans, the
proposal classifies 2 annotation corrections, 9 decompositions, 5 evaluator-only
changes, and 2 negative-space contexts. No corrected Recall@K was calculated.

**Aha / Learning.** Visual adjudication can move a case in either direction:
Q002/Q034 require gold corrections, whereas Q038 demonstrates why parser output
must not overwrite accurate gold. Page continuation without its antecedent is
not sufficient evidence merely because the later chunk is highly ranked.

**Decision / Next implication.** Owner approval remains required, especially for
Q029's eligibility boundary, Q034's required balance-claim unit, and Q040's
negative-space treatment. After approval, version the annotations and calibrate
the deterministic matcher with adversarial negatives before rescoring stored
hits under a separately reported v2 contract.

## 2026-10-04 — Evaluation Contract v2 implementation and stored-baseline rescore

**Context / Hypothesis**

Experiment 1 reported 59.3% Evidence Recall@10, but the approved human review showed that this metric mixed retrieval quality with annotation, representation, evaluator, and negative-space defects. The hypothesis was that a minimal deterministic v2 contract could separate measurement failure from genuine retrieval failure without changing retrieval outputs.

**What we did**

Implemented versioned atomic evidence units backed by authoritative fragments, conservative character-preserving canonicalization, exact source/document/page anchoring, and collective Top-K interval coverage (including Q012). Applied the owner decisions for Q029, Q034, and Q040, then rescored only the stored Experiment 1 rankings. Added adversarial tests for wrong numbers, missing negation, wrong documents, incomplete evidence, and semantic-but-non-equivalent wording.

**Evidence / Result**

The original v1 artifact remains unchanged at 32/54 (59.3%) Evidence Recall@10 and 18/39 (46.2%) Sufficient Evidence@10. V2 scores 64/72 (88.9%) Atomic Evidence Recall@10 and 31/39 (79.5%) Sufficient Evidence@10 on a decomposed denominator. Of the 18 reviewed v1-unmappable spans, 16 were measurement-contract/negative-space cases and two (Q002 and Q034) remain genuine Top-10 misses. Across the complete benchmark, eight questions each retain one unmatched required unit. Incremental API cost was $0.

**Aha / Learning**

The initial retrieval metric was partly measuring annotation and evaluator defects, not only retrieval. Exact collective coverage and authoritative atomic units recover true positives without relaxing numbers, negations, product identity, or completeness.

**Decision / Next implication**

Evaluation Contract v2 is closed. Future retrieval experiments should target the eight isolated genuine failures; Q034 also exposes a cross-page, page-bounded chunking constraint. Do not redesign the benchmark absent a concrete correctness defect.

## 2026-10-04 — V2 Top-10 failure depth investigation blocked by missing vectors

## Context / Hypothesis

Evaluation Contract v2 isolated eight genuine Top-10 failures. The next
architecture decision required their actual depth in the unchanged Voyage-4
cosine ranking: near misses would support testing reranking, systematic
representation failures would support a chunking experiment, and very low ranks
would support investigating first-stage query/chunk representation.

## What we did

Inspected the approved v2 units, all 360 saved Stage 1 chunks, extracted pages,
the original retrieval artifact, the v2 rescore, and the experiment persistence
code. Located every missing authoritative fragment by exact canonical source-page
interval, identified its evidence-bearing chunk(s), recorded the saved Top-10
cutoffs, and reviewed the text and provenance of every outranking saved result.
No retrieval component or evaluation contract was changed.

## Evidence / Result

Seven failures have a good single chunk containing the complete missing unit.
Q034's required sentence is split at a page boundary: its semantically complete
page-15 continuation is rank 2, while its syntactically incomplete page-14
opening is outside the Top 10. Q031 is not fragmented beyond recovery because the
100-token overlap creates a chunk containing its entire notice passage. Across
the cases, saved competitors are mostly cross-product near-duplicates,
same-page clauses, and chunks rich in the query's policy terminology.

The original artifact persists only Top 10. The gitignored corpus-vector cache is
absent, and the runner did not persist query vectors at all. Therefore exact
ranks and cosine scores beyond rank 10 cannot be reconstructed locally. New
Voyage calls would be required, so the investigation stopped at the explicit
cost guardrail with $0 incremental API cost. Full details are preserved in
[`docs/task_outputs/2026-10-04_008_v2-top10-failure-ranking-investigation.md`](task_outputs/2026-10-04_008_v2-top10-failure-ranking-investigation.md).

## Aha / Learning

Persisting only Top-K results is sufficient to score a fixed K, but insufficient
for post-hoc failure-depth analysis. Persisting corpus embeddings without query
embeddings would also be insufficient. The current evidence rules out extraction
corruption as the common cause and confirms one page-boundary representation
case, but it cannot distinguish reasonable-pool ranking misses from poor
first-stage semantic recall for the other seven.

## Decision / Next implication

Do not recommend or implement reranking, rechunking, or query-representation
changes from incomplete rank evidence. First obtain the original corpus and
query vectors/full rankings, or explicitly approve a separately versioned paid
rerun that persists them. Only then apply the predetermined dominant-mode
decision rule and select one optimization experiment.

## 2026-10-04 — Full-ranking diagnostic prepared; execution blocked by network policy

**Context / Hypothesis.** The separately authorized diagnostic required a fresh,
unchanged Voyage-4 embedding pass over the committed 360 chunks and all 39
positive v2 queries. Exhaustive rankings would reveal whether the eight Top-10
misses are near candidates, deep first-stage misses, or representation failures.

**What we did.** Added a dedicated diagnostic runner that reads—not regenerates—
the committed chunks, embeds documents and unchanged v2 queries with their proper
Voyage input types, ranks every query against all 360 chunks, calculates the v2
candidate-recall curve at K=1/3/5/10/20/30/50, records API usage/latency/model
metadata and cost, persists complete rankings, and deliberately omits vectors.
Added a deterministic mock test. Attempted run
`20261004T_diagnostic_v2_full360` with the configured credential.

**Evidence / Result.** All 29 tests pass. The attempted live run failed on its
first corpus batch because the execution environment's proxy returned HTTP 403
before any Voyage response. Its versioned failure record preserves input hashes,
configuration, failure stage, and the fact that actual token usage and billable
cost are unknown. It would be inaccurate to report zero billable usage without
an API usage response. No rankings, scores, metrics, or model-version response
were produced, and no prior Experiment 1/v2 artifact was changed.

**Aha / Learning.** Authorization and a configured key do not guarantee outbound
API reachability. A failed transport attempt is not retrieval evidence. Failure
provenance must not be filled with historical costs or inferred metrics.

**Decision / Next implication.** Do not select an architectural experiment until
the exact diagnostic is rerun in an environment that can reach Voyage. Then use
the measured rank distribution and K10→K30/K50 recall/sufficiency movement to
recommend exactly one experiment. The runner is ready; no optimization was
implemented.
# 2026-10-04 — Stage 2 reranking harness; measured run blocked

**Context / Hypothesis** — The frozen Stage 1 baseline leaves eight required
evidence units outside Top-10. The controlled hypothesis is that a cross-encoder
over the unchanged Top-30 can improve Recall@10 and sufficient evidence enough
to justify its overhead.

**What we did** — Selected a pinned, local Apache-2.0 MiniLM MS MARCO
cross-encoder; implemented an isolated 30-to-10 runner using Evaluation Contract
v2; added explicit rescue/loss, latency, usage, cost, and error accounting; and
tested both ranking behavior and the actual committed artifact schemas without
network access.

**Evidence / Result** — The snapshot does not contain the completed full-ranking
artifact: the committed Stage 1 results stop at rank 10 and the diagnostic folder
contains only a transport-failure record. Aggregate values and eight ranks cannot
reconstruct all 1,170 candidate pairs. A blocked-run artifact records the gap;
no reranking result or latency was fabricated.

**Aha / Learning** — Persisted candidate lists are a prerequisite for a controlled
second-stage experiment. Summary recall and failure ranks establish candidate
headroom but are not executable inputs.

**Decision / Next implication** — Run the prepared harness only after supplying
the immutable completed `full_rankings.json`. Do not conclude whether reranking
helps and do not recommend Stage 3 before that measurement.

## 2026-10-04 — Stage 2A MiniLM reranking measured; hypothesis rejected

**Context / Hypothesis** — The previously blocked harness was run locally with
the real completed `20261004_full360/full_rankings.json`. The hypothesis was that
reranking the unchanged Top-30 could promote missing evidence into Top-10 enough
to justify its latency and complexity.

**What we did** — Scored exactly 30 candidates for each of 39 positive questions
with the already selected, revision-pinned local MiniLM cross-encoder and retained
10. Stage 1 and Stage 2A were scored under the unchanged Evaluation Contract v2;
Q040 remained excluded. No other reranker or architecture change was introduced.

**Evidence / Result** — Stage 1 Top-10 was 64/72 atomic recall and 31/39 sufficient;
its Top-30 ceiling was 69/72 and 36/39. Stage 2A fell to 56/72 atomic recall and
27/39 sufficient. It rescued zero units and lost eight previously covered units.
The 1,170 pair scores took 52,562.843 ms total, or 1,347.8 ms/query. API usage and
cost were zero; local compute was not priced.

**Aha / Learning** — Candidate headroom alone does not imply a generic reranker
will exploit it. This MS MARCO MiniLM configuration reordered domain-specific
policy evidence destructively: it consumed latency while turning eight successes
into failures and rescuing none.

**Decision / Next implication** — **Stage 2A hypothesis rejected.**
`cross-encoder/ms-marco-MiniLM-L6-v2` materially degraded retrieval quality while
adding latency. This rejects this reranker/configuration, not reranking as an
architectural pattern. Preserve the negative result; do not add another reranker
to PR #16 or infer a Stage 3 recommendation from this experiment.

## 2026-10-04 — Stage 2B Voyage rerank-3 harness prepared; measurement blocked

**Context / Hypothesis** — Stage 2A rejected one MiniLM configuration, not the
reranking pattern. Stage 2B asks whether Voyage rerank-3 can exploit the five
reachable missing units in the exact frozen Stage 1 Top-30 without displacing
comparable or greater existing evidence.

**What we did** — Added an isolated official-SDK reranking harness and config.
It validates Q001–Q039 and all four frozen Top-10/Top-30 Contract v2 counts before
making paid calls, maps all 30 response indices without dropping candidates,
uses original rank for deterministic ties, and records full candidate movements,
usage, list-price estimates, latency, rescue/loss/net changes, sufficiency
transitions, known reachable outcomes, hashes, and provider metadata. No-network
unit and integration-style tests cover the actual committed schemas.

**Evidence / Result** — All 37 tests pass. The expected local
`20261004_full360/full_rankings.json` is absent in this checkout, so the attempted
run stopped before API client construction. Stage 2B quality, latency, usage, and
cost remain explicitly unmeasured; no result was fabricated. Stage 1 remains
64/72 and 31/39, while rejected Stage 2A remains 56/72 and 27/39.

**Aha / Learning** — A provider reranker can be tested under a strict controlled
contract without regenerating first-stage retrieval. Paid-call safety depends on
validating the complete candidate artifact before initializing or invoking the
client. Provider-reported token usage supports a list-price estimate but is not
the same as an invoice, and the SDK response does not expose observed retries.

**Decision / Next implication** — Stage 2B is **UNMEASURED / BLOCKED**, not failed
and not successful. Run the documented command on the owner's Mac with the
immutable local ranking artifact and `VOYAGE_API_KEY`. Make no further
architectural change until net quality, latency, and cost are measured and
reviewed together.
