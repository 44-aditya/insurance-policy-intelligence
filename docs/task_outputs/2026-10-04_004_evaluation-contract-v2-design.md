- Date: 2026-10-04
- Task / purpose: Design Evaluation Contract v2 for Stage 1 retrieval (analysis only)
- Git branch: work
- Related PR: #10
- Commit SHA: 27e201f467c8843efc140f381bb9a5b64cac439e (source revision)
- Output status: Raw/verbatim

---

## Recommendation

Adopt a **deterministic, source-anchored Evaluation Contract v2** whose scoring unit is an **atomic evidence unit**, not today's free-form `evidence_span`. Each positive question declares independently required units. Each unit contains one or more contiguous, PDF-authoritative source fragments only when those fragments jointly express one indivisible fact (for example, a sentence crossing a page). A Top-K result covers a unit when the **union of its retrieved chunks** deterministically covers every required fragment. A question has sufficient evidence only when every unit in a declared sufficient set is covered.

The smallest defensible v2 combines:

1. **Conservative deterministic canonicalization**: Unicode NFKC/casefolding, canonical quotes/dashes, soft-hyphen removal, whitespace collapse, whitespace-insensitive punctuation, and a comparison projection that ignores punctuation/spacing while retaining every letter and digit.
2. **Human-reviewed atomic decomposition** of annotations that concatenate separate clauses, headings, bullets, or pages. Gold remains a transcription and locator for authoritative PDF truth, not PyMuPDF output.
3. **Collective Top-K coverage**, restricted to the annotated document/source location, with ordered coverage and no credit for a missing intervening source interval.

Do **not** add semantic similarity, an LLM judge, or unconstrained fuzzy matching to the primary metric. They may be later diagnostics, but current evidence does not justify their thresholds, nondeterminism, cost, or false-positive surface.

This is a contract recommendation, not a new score. Experiment 1 remains immutable. No replacement Recall@K is calculated here.

## Three distinct layers

| Layer | Role | Change rule |
|---|---|---|
| **Gold evidence** | Authoritative claims and exact PDF locations; states required conjunctions and legitimate alternatives. | Change only after human PDF review, as a versioned benchmark correction—not to fit a parser. |
| **Extraction/chunks** | System-specific representations, including parser defects and boundaries. | May change with the system; never become source truth. |
| **Evaluator** | Measurement instrument mapping retrieved representations to gold and aggregating coverage. | Change only as an explicit, validated, versioned contract. |

The evaluator must not turn extraction corruption into gold wording. Gold must not encode current chunk boundaries. Conversely, retrieval should not receive an evaluator false negative when Top-K representations collectively preserve required source evidence.

## Proposed v2 semantics

### Atomic units, fragments, and sets

An **evidence unit** is the smallest independently retrievable proposition required for a correct answer: for example, a waiting period, cap, eligibility condition, or exclusion. It is the Evidence Recall denominator. If an answer requires two independent facts, those are two units rather than one long quote.

A **source fragment** is a contiguous authoritative passage with `source_file`, `source_page`, and verbatim PDF text (and preferably stable coordinates/anchors when tooling supports them). Usually a unit has one fragment. Multiple fragments are allowed only if all express one indivisible proposition, such as a sentence broken by a page. A fragment must never silently omit an intervening substantive clause.

An **evidence set** is a sufficient combination of units. V2 should recognize this concept but avoid unnecessary machinery until review finds genuine alternatives. The observed cases primarily require conjunction. Default: one set containing all required unit IDs. If future wording supplies alternative sufficient routes, multiple sets can encode OR; sufficient evidence means any declared set is complete. Recall must use an explicit rule, never choose the easiest set after seeing retrieval.

Existing spans already atomic migrate one-to-one; composite spans decompose. Thus `evidence_span` no longer serves simultaneously as quote container and scoring atom.

### Deterministic representation matching

For each gold fragment and candidate chunk from the same document, use:

- **Readable canonical form:** NFKC, casefold, canonical quotes/dashes, remove soft hyphens, collapse whitespace, remove whitespace adjacent to punctuation.
- **Compact lexical form:** retain Unicode letters/digits in order and discard whitespace/punctuation. This equates `policy .`/`policy.`, `non­ disclosure`/`non-disclosure`, and `Prevent ive`/`Preventive` without treating synonyms as equal.

Require exact ordered coverage in one form. Compact matches must be source/document/page anchored and meet a tested minimum lexical length. They must not remove, substitute, or reorder letters/digits. Thus `24 hrs` does not silently equal `24 hours`, nor `anaesthesia` equal `anesthesia`; such differences require authoritative review.

Do not globally delete Roman numerals or marker-like tokens. If a marker is non-semantic furniture, annotations should terminate/restart fragments or define separate units. If list structure affects meaning, retain it.

### Collective Top-K coverage

Evaluate the **set** of first-K chunks. A fragment is covered if deterministic alignments from one or more retrieved chunks collectively cover its full lexical sequence in source order. This may bridge overlapping/adjacent chunks with no missing gold interval, and may cross a page only when gold explicitly identifies both page fragments.

It may not bridge an unretrieved gap, use another policy/location, match repeated boilerplate elsewhere, or assemble words out of order. Retain an auditable witness: unit/fragment IDs, matched chunk IDs/ranks, normalization path, and covered intervals. One chunk can cover several units; duplicate chunks do not duplicate credit.

### Metrics

For positive-evidence questions:

- **Atomic Evidence Recall@K** = covered required units / all required units (micro-average).
- **Sufficient Evidence@K** = proportion of questions with one complete declared sufficient set.
- Report witnesses and slices, including extraction-quality and single-chunk versus collective coverage.

Report mapping/adjudication separately. An unvalidated/unmappable unit must not silently become a retrieval miss or disappear from the denominator: fail benchmark validation or publish an explicit `not_scorable` count pending review.

## Success by observed failure class

| Class | Counts as success | Does not count |
|---|---|---|
| Harmless punctuation/spacing | Same letters/digits in order at the correct source fragment after deterministic canonicalization. | Changed/missing letters or numbers, synonyms/paraphrase, wrong location, or short accidental compact match. |
| List/bullet markers | Required atomic list content is covered; non-semantic labels between separately annotated fragments do not defeat it. | Globally deleting marker-like tokens; omitting a required item, qualifier, or meaningful structure. |
| Non-contiguous gold concatenation | After PDF review, all required decomposed units/fragments are in Top-K. | Matching only beginning/end across an unretrieved substantive clause; changing gold to mimic chunks. |
| Split across chunks | Top-K union covers the whole fragment in order with no uncovered gold interval. | Partial chunks, a missing interval, or evidence below K. |
| Cross-page evidence | Gold identifies each PDF page fragment and Top-K covers every required one. | Assigning everything to one page or crediting only one side. |
| Extraction corruption | Character-preserving canonicalization aligns retrieved representation to PDF truth. | Copying corruption into gold; accepting changed/missing characters or semantic resemblance alone. Beyond-rule corruption is `unmappable`, not a retrieval miss, pending review. |
| Genuine miss | Nothing: a mapped required unit absent from Top-K fails at K. | Credit because the page/chunk exists below K or another product has analogous wording. |

## Approach comparison

| Approach | FP risk | FN risk | Reproducibility / interpretability | Cost / complexity | V2 role |
|---|---|---|---|---|---|
| Improved deterministic normalization | Low when anchored and characters preserved; rises with unconstrained deletion. | Low for punctuation/spacing/soft hyphens/split words; remains for spelling, abbreviations, missing characters. | Excellent, inspectable, repeatable. | No API; modest rules/tests. | **Primary matcher.** |
| Atomic decomposition | Low if PDF-verbatim and not tiny/generic; poor annotation can cherry-pick easy facts. | Greatly reduces composite-quote FNs; over-splitting can lose inseparable context. | High after review; denominator is understandable. | Moderate annotation/schema effort. | **Primary gold model.** |
| Collective Top-K coverage | Low with ordered anchored interval union; high with unordered snippet bags. | Reduces boundary FNs. | High with rank/interval witnesses. | Moderate evaluator work; no API. | **Primary aggregation.** |
| Fuzzy lexical matching | Medium/high around boilerplate, numbers, negation; thresholds may overfit these cases. | Helps OCR typos but thresholds still err. | Repeatable implementation, weakly interpretable thresholds/library dependence. | Low runtime; calibration/regression burden. | Diagnostic only; require a separate labelled match/non-match calibration set before adoption. |
| Semantic/embedding match | High for legally close but distinct clauses; can blur negation/limits/products. | Helps paraphrase, but exact limits/multipart evidence may fail. | Model/version/threshold dependent; poor auditability. | Model/API, latency, calibration/versioning. Retrieval embeddings are not an independent judge. | Not primary; possible review triage. |
| LLM judge | Plausible-but-incomplete judgments, especially on qualifications/negative space. | Flexible but inconsistent about missing details. | Lowest; prompt/model drift and opaque decisions. | Highest cost, latency, complexity, failure modes. | **Not justified.** Future research only after labelled judge validation. |

## The 18 unmatched spans under v2

These are dispositions of stored hits, **not recalculated metrics**.

| Span | V2 handling and observed disposition |
|---|---|
| **Q002/2** | PDF-review transcription (`anaesthesia`/`anesthesia`, `24 hours`/`24 hrs`) and store verbatim atomic units. Conservative normalization must not guess. Once resolved, the preserving page chunk was not Top-10: **genuine failure at K≤10**. |
| **Q004/1** | Split pre/post-hospitalization units across the B3 heading. Rank-2 contains both: **success K≥3** after review. |
| **Q007/1** | Split clauses a–c/contiguous fragments; retain substantive conditions. Rank-3 contains cited meaning: **success K≥3**. |
| **Q008/2** | Split 24-month and longer-PED-wait rules; do not fabricate contiguity across omitted text. Rank-5 contains both: **success K≥5** if reviewed units are complete. |
| **Q010/1** | Atomic discount/table units; terminal punctuation ignored. Rank-1: **success all K**. |
| **Q011/1** | Split overseas eligibility/payment and restored-sum limitation around omitted exchange-rate paragraph. Rank-1 has cited facts: **success all K** if all required units covered. |
| **Q012/2** | Keep atomic proposition(s), allow ordered page-17 chunk union. Ranks 1+3 jointly cover it: **fail K=1; success K≥3**. Canonical collective-coverage test. |
| **Q019/1** | Split waiting period/limits if independently required; whitespace-before-punctuation ignored. Rank-1: **success all K**. |
| **Q026/1** | Split accrual/cap, claim reduction, and base-sum protection; label `ii.` is structure. Rank-4: **success K≥5**. |
| **Q027/1** | Atomic unit; terminal period ignored. Rank-3: **success K≥3**. |
| **Q028/1** | Split duration/termination statements; `v.` is structure. Rank-1: **success all K**. |
| **Q029/1** | Decompose eligibility, emergency/accident, stabilization, PED, and deductible facts; do not omit substantive bullets from a quote. Ranks 1+2 jointly preserve cited content: **collective success K≥3 only if PDF review declares those units sufficient**; any other required unit must also be retrieved. |
| **Q033/1** | Split pre/post-hospitalization. Compact match handles fragmentation/soft hyphens; source anchoring excludes inserted page furniture. Rank-4: **success K≥5**. |
| **Q034/1** | Correct locators to page-14/page-15 fragments and decompose multiple-policy rules after PDF review. Page-15 continuation is rank 2, but correct Plus page 14 is absent Top-10: **not sufficient K≤10** if opening is required. |
| **Q038/1** | Units for allowance/cap/frequency. Compact match handles split words, but `max`/`maximum` needs authoritative review. Rank-1 preserves meaning: **success all K only after wording resolution and deterministic alignment**; otherwise `unmappable`. |
| **Q039/1** | Split exclusion introduction/device items; compact form handles fragmented words; do not claim contiguity across omitted personal-comfort text. Rank-1: **success all K** if reviewed units are required. |
| **Q040/1** | Context for separate abstention/negative-space protocol; compact form can map cancellation corruption. **Excluded from positive Recall**, and not Top-10. |
| **Q040/2** | Context for separate abstention protocol; compact form can map contract corruption. **Excluded from positive Recall**, and not Top-10. |

V2 therefore does not automatically turn all 18 into successes. Q002 is a genuine Top-10 miss after review; Q034 is incomplete; Q012/Q029 need collective coverage; Q038 needs authoritative wording review; Q040 is a different evaluation mode.

## Q040: negative-space probe

Q040 asks whether policy wording establishes an automatic termination rule. Nearby clauses cannot prove document-wide absence, so positive Evidence Recall is wrong. Keep it excluded and later report a separate rubric:

1. Target response: the proposed conclusion is not established; do not invent automatic termination.
2. Fail an unsupported assertion of that rule.
3. Report ranks for human-reviewed relevant cancellation, eligibility/residency, renewal, and entire-contract contexts, but do not call them proof of absence.
4. Measure answer-level abstention correctness and citation entailment only in a generation experiment.

Document-wide negative-space may require corpus-search sufficiency or a rule inventory, but v2 must not smuggle that architectural issue into positive recall.

## Migration plan (proposal only)

### Gold schema

1. Version schema/benchmark as v2; do not mutate v1 semantics.
2. Add stable `evidence_units`; each records proposition/purpose and contiguous `source_fragments` with PDF-authoritative file/page/text.
3. Encode the default conjunction; add alternative `evidence_sets` only for genuine OR semantics.
4. Add `evaluation_mode` (`positive_evidence`, `abstention_negative_space`) so Q040 cannot enter positive aggregates.
5. Keep review/provenance and benchmark version. Never put parser text or chunk IDs in gold.

### Annotations

1. Re-open PDFs for all 18; prioritize Q002/Q038 transcription and Q034 pages.
2. Decompose Q004, Q007, Q008, Q011, Q026, Q028, Q029, Q033, Q034, Q039; review whether Q010/Q019/Q038 limits need separate units.
3. Mark units required for sufficiency, preserving qualifiers, negation, numbers, and substantive intervening clauses.
4. Require second-person review and rationale. Extraction is diagnostic, never transcription authority.

### Evaluator

1. Add versioned v2 while retaining v1 reproduction.
2. Implement canonical forms and source-anchored ordered alignment.
3. Union Top-K coverage with chunk/rank/interval witnesses.
4. Score unit recall/sets; fail validation or separate `not_scorable`, never conflate mapping and retrieval.
5. Exclude Q040 and emit only separate diagnostics until its rubric exists.

### Tests

Cover punctuation/spacing; soft hyphens/split words; changed digits/negation that must fail; bullets; discontinuous annotation; two-chunk union; an uncovered gap; cross-page units; wrong policy/page lookalikes; repeated boilerplate; partial multi-unit sufficiency; alternatives if implemented; Q040 exclusion; stable witnesses; and v1 regression. Include adversarial negatives, not only the known 18.

### Experiment 1 history

1. Leave `retrieval_results.json` and v1 metrics unchanged.
2. Keep the report's v1/provisional qualification.
3. After approval/implementation, score stored hits under v2 where possible without Voyage. Publish a new result with evaluator/gold versions, SHA, date, denominator, review state, and v1 reconciliation.
4. Never overwrite/relabel/backfill v1. If annotations prevent stored-hit rescoring, state that and wait for separate authorization.

## Decision record, limitations, and next experiment

- **Proposed material decision:** deterministic atomic-unit/set coverage over the Top-K union, with PDF evidence authoritative.
- **Evidence:** the 18 cases combine harmless representation differences, discontinuous quotes, chunk/page splits, parser corruption, and real misses; no single permissive matcher safely resolves all.
- **Assumptions:** prior root-cause findings stand, but PDF-authoritative edits need human review. Stored artifacts support design, not a published v2 score.
- **Limitations:** compact normalization cannot resolve synonyms, abbreviations, missing characters, or semantics safely. Atomicity needs judgment. Collective alignment needs adversarial tests. Negative space remains outside positive recall.
- **Security:** no secrets/private data or broader access are introduced.
- **Cost/latency:** primary v2 needs no model/API calls; it adds local alignment and one-time review complexity but negligible evaluation runtime relative to embeddings. This task made no paid calls.
- **Recommended next experiment:** after approval, annotate a small blinded calibration set containing true and deliberately confusable false matches, implement v2 behind a version flag, and measure deterministic matcher FP/FN behavior before separately rescoring preserved hits. Do not alter extraction, chunks, embeddings, retrieval, or architecture based on provisional v1.

## Validation performed

- Read/cross-checked gold/schema/annotation guidance, evaluator/tests, Stage 1 report, preserved root-cause analysis, chunks, and immutable results.
- Confirmed stored Q034 provenance: correct Plus page 15 is rank 2; required Plus page 14 is absent Top-10.
- No implementation, benchmark data, retrieval artifacts, extraction, chunking, embeddings, or retrieval results changed; retrieval was not rerun and no API cost incurred.
