- Date: 2026-10-04
- Task / purpose: Investigate the eight Evaluation Contract v2 Top-10 failures in the unchanged Voyage-4 ranking
- Git branch: work
- Related PR: unknown / none
- Commit SHA: 3711adb (inspected source revision before this diagnostic record)
- Output status: Raw/verbatim (repository-relative paths substituted for machine-specific paths)

---

## Outcome: stopped before any new Voyage API usage

The repository is sufficient to locate every missing unit in the existing Stage 1
chunk corpus and to inspect the saved Top-10 competitors. It is **not** sufficient
to determine any missing chunk's actual rank or cosine score below rank 10:

- `artifacts/retrieval/stage1_voyage4/retrieval_results.json` persists only ten
  results per query.
- `artifacts/retrieval/stage1_voyage4/evaluation_v2_results.json` is a deterministic
  rescore of those same stored Top-10 lists; `source_rankings` points back to the
  first artifact rather than containing a wider ranking.
- The runner wrote corpus vectors to the gitignored
  `artifacts/retrieval/stage1_voyage4/vectors.json`, but that local cache is absent.
  More importantly, the runner never persisted query vectors. A corpus-vector
  cache alone would therefore still not permit reconstruction of the original
  cosine ordering.

Re-embedding the eight queries (and, because the corpus-vector cache is absent,
the 360 chunks) would be necessary to calculate ranks 11–360. That would be new
Voyage API usage and would create a new run rather than recover the exact stored
run. Per the task's cost guardrail, I made **no API call** and stopped the causal
classification before guessing from incomplete rankings.

## Method and preserved facts

I inspected the approved v2 source fragments, canonicalized extracted page text
and all 360 saved chunks with the existing v2 canonicalizer, and computed exact
source-page interval overlap. This is evidence location, not a new evaluator or
retrieval run. A chunk marked “full” contains the entire authoritative fragment
after the approved extraction-aware canonicalization. “Partial” is reported only
where a page/chunk boundary prevents full containment.

Scores below are the original saved scores. `>10; exact unavailable` is the
strongest rank statement the artifact supports; it must not be converted into an
estimated rank. Likewise, a missing score is not zero.

| question | missing unit | best evidence chunk(s) | actual rank | cosine score | Top-10 cutoff score | diagnosis | evidence/reasoning |
| --- | --- | --- | ---: | ---: | ---: | --- | --- |
| Q002 | U2 | `chunk-48543a1ae5d223bb` (Select p.4, full) | >10; exact unavailable | not stored | 0.472776 | **Not classifiable from stored artifacts** | The single 512-token chunk fully contains the day-care definition (canonical page interval 421–747), so fragmentation is not evident. The Top 10 is dominated by definitions of day care, hospitalization, illness, and related terms from all four products; those are semantically competitive with a generic duration question. Exact depth is required to distinguish ranking from first-stage retrieval. |
| Q008 | U4 | `chunk-f1b67e1ee8532db4` (Select p.21, full) | >10; exact unavailable | not stored | 0.425808 | **Not classifiable from stored artifacts** | The 194-token final page chunk fully contains the cataract list item (2360–2422). Higher hits discuss waiting periods, pre-existing disease, and comparable condition lists; three saved hits are from the correct Select pages, but the required tail-list chunk is absent. Its depth is unknown. |
| Q014 | U2 | `chunk-0fa74941981eebc3` (Premier p.22, full) | >10; exact unavailable | not stored | 0.402004 | **Not classifiable from stored artifacts** | The evidence is wholly represented in one 239-token chunk (1016–1128). Top results include the same page's qualifying dental-treatment list, general exclusions, OPD definitions, and dental definitions. Those chunks match stronger query terms (“OPD”, “dental”, “exclusion”), while U2 is a short exception/bridge sentence. |
| Q017 | U2 | `chunk-f4c16c00167f9c18` (Premier p.23, full) | >10; exact unavailable | not stored | 0.350824 | **Not classifiable from stored artifacts** | One 512-token chunk fully contains the eligibility condition and limit table (340–580). Saved hits include a different Premier monetary-limit table at rank 1 (0.597354), ground-ambulance coverage at ranks 2–3, and other benefit-limit pages. These share “ambulance”, limits, claim conditions, and currency language. |
| Q030 | U1 | `chunk-6da5fc9f082f2111` (Reserve p.37, full) | >10; exact unavailable | not stored | 0.387491 | **Not classifiable from stored artifacts** | One 512-token chunk fully contains the three-step sequence (547–674). The Top 10 repeatedly contains “Balance Sum Insured”, “Cumulative Bonus”, “Restore”, claim-order-adjacent language, and analogous benefits from other products; this is a strong same-vocabulary competition case, but the correct chunk's depth is unavailable. |
| Q031 | U1 | `chunk-efe391ec37297c54` (Plus p.19, full); `chunk-d3f0e54bd36eba0b` (Plus p.19, partial) | >10 for the full chunk; rank 1 for the partial chunk | not stored for full chunk; 0.508737 for partial chunk | 0.423538 | **Not classifiable from stored artifacts** | Overlap works as designed: chunk 1 fully contains the 48-hour/24-hour notice passage (1431–2518 chunk range versus 1559–1958 evidence), while overlapping chunk 0 contains only its opening. The Top 10 contains analogous notification timelines from Plus p.20, Reserve p.33, and Select p.33. The partial chunk's rank 1 does not cover the full unit; the full chunk's unknown depth is decisive. |
| Q034 | U1 | `chunk-d9dde8aaa1b03951` (Plus p.14, full opening); `chunk-c38f1dfd94f27971` (Plus p.15, full continuation) | >10 for p.14; rank 2 for p.15 | not stored for p.14; 0.650411 for p.15 | 0.498112 | **Chunking/representation problem confirmed; additional ranking contribution undetermined** | Page-bounded chunking splits one sentence after “to indemnify”: the p.14 prefix is isolated from its semantic predicate on p.15. The continuation ranks highly and fully states the choice rule, while the short syntactically incomplete opening is absent. Other products' multiple-policy/claim-settlement clauses occupy ranks 1, 3–5. Exact p.14 rank is still needed before calling the case mixed. |
| Q037 | U2 | `chunk-93797da06ba04bbd` (Plus p.11, full) | >10; exact unavailable | not stored | 0.397528 | **Not classifiable from stored artifacts** | One 512-token chunk fully contains the enhanced-sum-insured waiting-period sentence (812–929). Ranks 1–3 contain near-paraphrases about increased/enhanced Sum Insured and waiting periods, including Plus p.19 and Plus p.10. They are legitimately competitive, but the correct clause's depth is unavailable. |

## What outranked the evidence

The saved Top-10 lists show coherent semantic competition rather than random
noise:

- **Cross-product near-duplicates:** Q002, Q008, Q017, Q030, Q031, Q034, and
  Q037 retrieve equivalent policy concepts from other Tata AIG products.
- **Same-page or neighboring-clause competition:** Q008, Q014, Q017, Q031, and
  Q034 retrieve another chunk from the correct page or the other half of the
  required context.
- **Query-term concentration:** Q014's treatment list and exclusion language,
  Q017's other ambulance/limit clauses, and Q030's other balance/bonus/restore
  clauses contain more repeated query vocabulary than the missing evidence.
- **Representation-specific weakness:** only Q034 is demonstrated to split a
  required grammatical sentence across pages. Q031 is not a demonstrated
  chunking failure: its overlap produces a second chunk that contains the whole
  required passage.

These observations explain why saved hits are plausible competitors, but they
cannot reveal whether each evidence chunk is at rank 11, rank 30, or rank 300.

## Pattern and decision

Seven missing units have a good, fully evidence-bearing chunk in the unchanged
corpus. Q034 has both required page fragments represented, but the page boundary
turns the opening into a weak, incomplete clause and requires collective
retrieval across two pages. The Top-10 lists also contain many close
cross-product paraphrases. This establishes that extraction corruption is not
the causal bottleneck in these eight cases and provides no basis for recommending
PyMuPDF4LLM.

However, the requested dominant-mode decision explicitly depends on the actual
below-Top-10 ranks. Those ranks are not recoverable from the committed artifacts.
It would be methodologically invalid to label the seven full-chunk cases as
“ranking problem” rather than “first-stage semantic retrieval problem” without
knowing whether their ranks are reasonably high or very poor.

**Recommended next experiment:** none yet. The task says to stop rather than incur
new API cost when new calls are required to determine ranks, so recommending
reranking, chunking, or query-representation work now would bypass the specified
decision logic. The prerequisite is for the owner to provide the original
query-vector and corpus-vector cache (or explicitly authorize a separately
versioned paid rerun that persists full rankings). Once available, the single
next experiment should be selected directly from the requested rank-distribution
rule.

## Validation, assumptions, limitations, security, and cost

- **Files changed:** this task record and `docs/timelapse.md` only. No retrieval,
  extraction, chunking, embedding, evaluator, contract, or architecture file was
  modified.
- **Checks executed:** repository status/history inspection; JSON artifact shape
  and cache-presence inspection; deterministic exact interval-to-chunk mapping;
  saved Top-10 score/provenance inspection; full test suite; diff checks.
- **Evaluation result:** all eight authoritative units were located in the saved
  corpus. Seven have a full single-chunk representation. Q034 is represented by
  two full per-page fragments whose sentence-level meaning is split across the
  page boundary. Exact missing ranks and scores remain unavailable.
- **Assumption:** the committed chunks and rankings are the authoritative outputs
  of the same recorded run, consistent with their existing provenance and v2
  rescore. No attempt was made to reconstruct floating-point embeddings.
- **Known limitation:** only ranks 1–10 and their scores were persisted. Similarity
  scores cannot be derived from text alone, and a rerun would not prove the exact
  historical ordering if the hosted model changed.
- **Security:** no credentials or environment-variable values were read or
  persisted. The analysis uses only the existing public policy corpus and derived
  repository artifacts.
- **Cost:** $0 incremental API cost and zero new embedding tokens.
