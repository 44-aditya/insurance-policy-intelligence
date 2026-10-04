- Date: 2026-10-04
- Task / purpose: Read-only root-cause analysis of all 18 unmatched Stage 1 gold evidence spans
- Git branch: codex/implement-stage-1-semantic-vector-retrieval
- Related PR: #10 — https://github.com/44-aditya/insurance-policy-intelligence/pull/10
- Commit SHA: a08481a3a0f21c3bb219ffe169acd3ca047098a8 (source revision; completed experiment artifacts were uncommitted)
- Output status: Raw/verbatim; only machine-specific absolute file links replaced with repository-relative links. Former file-link line references identify question records; follow the question ID in the linked JSON.

---

**All 18 spans have identifiable supporting content in the extraction, although Q034 crosses pages.** Twelve have their full meaning preserved in a retrieved chunk but fail the evaluator’s contiguous-text match: these are **potential Recall@K false negatives**, not evidence of retrieval failure.

The table abbreviates gold text to stay compact; each question link opens the complete verbatim annotation. Chunk indices are zero-based. “Rank” refers to that question’s recorded retrieval results.

PDF/product key:

- **Select:** `medicare_select_policy_wording_0faeeb61c5.pdf`
- **Premier:** `tata_aig_medicare_premier_policy_wordings_781aa2fd94.pdf`
- **Reserve:** `tata_aig_medicare_reserve_policy_wordings_2250e6352a.pdf`
- **Plus:** `Tata_AIG_Medi_Care_Plus_e8a0cf5358.pdf`

| Question / span¹ | Product / gold page | Gold evidence text, abbreviated | Raw page finding | Chunk finding | Primary failure | Potential Recall false negative |
|---|---|---|---|---|---|---|
| [Q002 / 2](../../evals/gold_dataset.json) | Select / 4 | “Day Care Treatment means Medical Treatment… general or local anaesthesia… less than 24 hours…” | Approximately present. Extraction says **“General or Local Anesthesia”** and **“24 hrs”**. Gold changes spelling and expands the abbreviation. | Full meaning in chunk 0; not retrieved in top 10. | **Gold annotation issue**: transcription differs from extracted wording. | No demonstrated retrieval false negative at K≤10. |
| [Q004 / 1](../../evals/gold_dataset.json) | Select / 12 | “We will cover expenses for pre-hospitalization… upto 90 days… B1, B4, or B6. We will cover… post-hospitalization… upto 90 days…” | Both passages present, but gold joins them while omitting the intervening **B3 / Post-Hospitalization expenses** heading. | Both passages in chunk 1, rank **2**. | **Gold annotation issue**: noncontiguous passages represented as one contiguous span. | **Yes, K=3,5,10.** |
| [Q007 / 1](../../evals/gold_dataset.json) | Select / 22 | “Expenses related… within 30 days… Continuous Coverage for more than twelve months… enhanced Sum Insured…” | All text present in clauses a–c; intervening **b.** and **c.** prevent matching. | Full meaning in chunk 1, rank **3**; chunk 0 ends during clause c. | **Evaluator matching issue**: list markers interrupt otherwise equivalent text. | **Yes, K=3,5,10.** |
| [Q008 / 2](../../evals/gold_dataset.json) | Select / 21 | “Expenses related… excluded until… 24 months… If any… falls under… Pre-Existing Diseases… longer… shall apply.” | Gold stitches clause a’s first sentence to clause c, omitting the accident exception and clause b. | Both cited passages in chunk 0, rank **5**. | **Gold annotation issue**: discontinuous evidence. | **Yes, K=5,10.** |
| [Q010 / 1](../../evals/gold_dataset.json) | Select / 29 | “At Renewal… Favorable Experience Discount… 3 Years 0%… No Claim 20%… will not be considered a ‘Claim Year’.” | Table values and prose preserved in order. Gold adds a **final period** absent from extraction. Removing only that period yields a normalized match. | Entire evidence in chunk 1, rank **1**. | **Evaluator matching issue**: terminal punctuation sensitivity. | **Yes, all K.** |
| [Q011 / 1](../../evals/gold_dataset.json) | Premier / 16 | “Medical Expenses… outside India… diagnosis… in India… reimbursement… Only the balance basic sum insured… not the restored sum insured.” | Supporting passages present. Gold omits the intervening paragraph about RBI exchange rates. | All cited facts in chunk 1, rank **1**. | **Gold annotation issue**: discontinuous evidence. | **Yes, all K.** |
| [Q012 / 2](../../evals/gold_dataset.json) | Premier / 17 | “B13. ‘Global Cover…’… not available… Foreign National… NRI… OCI… opted out… neither… can take coverage under this benefit.” | **Full normalized span present once**, on the correct page. | Split: chunk 0, rank **1**, lacks the final **“benefit.”**; chunk 1, rank **3**, contains the ending but lacks the beginning. | **Chunk-boundary/coverage issue.** | No full-span single-chunk false negative. Collective coverage exists at K≥3. |
| [Q019 / 1](../../evals/gold_dataset.json) | Premier / 20 | “Maternity Expenses… waiting period of 3 years… Up to Rs. 50 Lacs… Rs 50,000/-… girl child… Rs 60,000/-…” | Text and table row present. Extraction has **“policy .”**, gold **“policy.”** Removing whitespace before punctuation yields a match. | Entire evidence in chunk 0, rank **1**. | **Evaluator matching issue**: whitespace before punctuation. | **Yes, all K.** |
| [Q026 / 1](../../evals/gold_dataset.json) | Reserve / 17 | “50% Cumulative Bonus… maximum… 100%… If… a claim is made… decrease… by 50%… no impact on… base Sum Insured…” | All wording present; **ii.** separates the two gold passages. | Entire meaning in chunk 0, rank **4**. | **Evaluator matching issue**: list marker. | **Yes, K=5,10.** |
| [Q027 / 1](../../evals/gold_dataset.json) | Reserve / 14 | “This benefit will not be applicable after the Insured Person(s) has opted Waiver of Aggregate Deductible.” | Present without gold’s **final period**. Removing it yields a normalized match. | Entire evidence in chunk 1, rank **3**. | **Evaluator matching issue**: terminal punctuation sensitivity. | **Yes, K=3,5,10.** |
| [Q028 / 1](../../evals/gold_dataset.json) | Reserve / 18 | “This benefit… ninety (90) consecutive days from… termination… This cover… ninety (90)… or till… separate Employer-Employee Group Health Insurance Policy…” | Both sentences present; **v.** intervenes. | Entire meaning in chunk 1, rank **1**. | **Evaluator matching issue**: list marker. | **Yes, all K.** |
| [Q029 / 1](../../evals/gold_dataset.json) | Reserve / 19 | “C3 Inbound Emergency Hospitalization… NRI… OCI… emergency… Accident… diagnosed in India… stabilized… Pre-Existing Disease… waiver of Aggregate Deductible.” | Cited facts present, but gold omits intervening bullets about deductible exemption and a separate benefit limit. | Also split: chunk 0, rank **2**, ends during stabilization wording; chunk 1, rank **1**, contains later conditions but lacks the opening. | **Gold annotation issue**; secondary chunk-coverage issue. | No complete single-chunk case. Collective semantic coverage at K≥3. |
| [Q033 / 1](../../evals/gold_dataset.json) | Plus / 7 | “Pre-Hospitalization… upto 60 days… B1 or B4 or B6… Post-Hospitalization… upto 90 days… B1 or B4 or B6.” | **Structurally damaged but readable**: fragmented words, soft hyphens, and page number **7** inserted before “to the hospital.” Gold also omits the B3 heading. | Both benefits preserved in chunk 0, rank **4**; post-hospitalization also in chunk 1, rank 9. | **Extraction representation issue**; secondary discontinuous annotation. | **Yes, K=5,10.** |
| [Q034 / 1](../../evals/gold_dataset.json) | Plus / 15 | “In case of multiple policies… one or more insurers to indemnify treatment costs… If the amount… exceeds the Sum Insured… choose Insurer…” | **Cross-page:** opening through “to indemnify” is on **page 14**; page 15 starts “treatment costs…”. Gold additionally skips clause ii before clause iii. | Page-15 chunk 0, rank **2**, preserves the continuation and balance-claim provision; no page-15 chunk can contain the missing opening. | **Gold annotation/page-reference issue.** | Partial evidence retrieved; no complete single-chunk false negative. |
| [Q038 / 1](../../evals/gold_dataset.json) | Plus / 8 | “Preventive Health Check-up upto 1%… maximum… Rs. 10,000/-… more than one insured… every two continuous claim free policy years…” | **Structurally damaged:** “Prevent ive”, “Hea lth”, “max i mum”, “ut il ize”, “cont inuous”; also “1 %”. Gold uses “maximum” where extraction says “max” in the first limit sentence. | All meaning preserved in chunk 0, rank **1**. | **Extraction representation issue**; secondary gold wording difference. | **Yes, all K.** |
| [Q039 / 1](../../evals/gold_dataset.json) | Plus / 8 | “However… excluded… External durable devices… Bl PAP… CPAP… Peritoneal Dialysis… Nimbus/water/air bed, dialyzer…” | Gold joins the introduction to the device item while omitting the intervening personal-comfort exclusion. Extraction additionally has **“Posit ive”** and **“dia lyzer”**. | Introduction and full device list in chunk 1, rank **1**. | **Gold annotation issue**; secondary extraction representation issue. | **Yes, all K.** |
| [Q040 / 1](../../evals/gold_dataset.json) | Plus / 15 | “The Company may cancel… established fraud, misrepresentation or non-disclosure… giving 15 days’ written notice.” | **Structurally damaged:** “misrepresentat ion”, soft-hyphenated “non­ disclosure”, “Insu red”, “g iv i ng”, “wr itten”. | Full meaning preserved in chunk 1; not retrieved in top 10. | **Extraction representation issue.** | **Not applicable:** Q040 excluded from Recall aggregation. |
| [Q040 / 2](../../evals/gold_dataset.json) | Plus / 18 | “This Policy, its Schedule, endorsement(s), proposal constitutes the entire contract… No change… unless approved by Us…” | **Structurally damaged:** “Th i s Pol i cy”, “Sc he d ule”, “e ndorsement(s)”. Contract provision remains readable. | Full meaning preserved in chunk 1; not retrieved in top 10. | **Extraction representation issue.** | **Not applicable:** Q040 excluded from Recall aggregation. |

¹ Span numbers above are one-based; artifact `evidence_index` values are zero-based.

| Primary failure category | Spans |
|---|---:|
| Gold annotation/page-reference issue | **7** |
| Extraction representation issue | **4** |
| Chunk-boundary/coverage issue | **1** |
| Evaluator matching issue | **6** |
| Unresolved / requires human PDF review | **0** |
| **Total** | **18** |

These categories identify the primary cause; several spans have secondary causes. “Evaluator matching issue” denotes sensitivity to semantically harmless formatting, **not necessarily an implementation bug**: the current evaluator deliberately requires full normalized contiguous text.

**Q012 is the clearest chunking limitation.** Its normalized span occupies page-text offsets `[1010,1839)`, while chunk 0 ends at `1830`; the overlap supplies the ending in another chunk but cannot provide full-span coverage in either chunk. **Q034 is the clearest page-reference issue.** The Plus cases otherwise primarily expose fragmented extraction text, with Q039 also containing a discontinuous annotation.

The 12 flagged false negatives are qualitative findings against the stored retrieved text. I have **not recalculated or replaced the official metrics**. This analysis establishes representation and coverage causes from the artifacts; visual PDF review would still be appropriate before changing authoritative gold wording.

No files were modified, embeddings rerun, or paid API calls made.
