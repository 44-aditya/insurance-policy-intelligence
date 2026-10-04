# Evaluation Contract v2: authoritative evidence review package

**Status:** proposed for owner review; every case remains `PENDING`
**Scope:** the 18 evidence spans reported unmatched by the Stage 1 evaluator
**Baseline:** preserved Experiment 1 artifacts only; no retrieval or embedding run was performed

## Review purpose and rules

This package asks the project owner to approve the evidence representation before
Evaluation Contract v2 changes either the benchmark or evaluator. It does **not**
amend `evals/gold_dataset.json`, publish a corrected score, or treat current
extraction as source truth.

The review follows this causal chain:

> **source truth (visual PDF) → gold representation → system extraction →
> retrieval → evaluator**

The authoritative wording below was transcribed from visual inspection of the
four PDFs in `corpus/policy_wordings/`. It was then compared with the current
gold, the unchanged page text in `artifacts/extraction/policy_pages.jsonl`, and
the stored chunks/ranks in `artifacts/retrieval/stage1_voyage4/`. “Rank” always
means the existing Experiment 1 rank; it is not a new retrieval result.

An **atomic unit** is a proposition independently required to answer the
question. A **source fragment** is contiguous PDF-authoritative wording that
supports a unit. Units are not made artificially small: conditions, exceptions,
negations, limits, and the text needed to identify what they qualify remain
together. Multiple fragments are proposed only where the PDF itself separates
independently required propositions or one proposition crosses a page boundary.

Proposed change types mean:

- **annotation correction:** the current transcription or locator disagrees with
  the PDF;
- **decomposition:** the current span fabricates contiguity across headings,
  list markers, or substantive omitted text;
- **evaluator-only:** the gold truth can stand and deterministic matching or
  collective coverage should handle the representation;
- **negative-space:** the span is context for an abstention question, not
  positive proof of a document-wide absence.

## Cases for decision

### Q002 — unmatched span 2 of 2

| Field | Required content |
| --- | --- |
| Question ID | Q002 |
| Question | What minimum duration qualifies as hospitalization, and can treatment under 24 hours qualify? |
| Current gold | `medicare_select_policy_wording_0faeeb61c5.pdf`, page 4: “Day Care Treatment means Medical Treatment, and/or Surgical Procedure which is: i. undertaken under general or local anaesthesia in a Hospital/Day Care Centre in less than 24 hours because of technological advancement, and ii. which would have otherwise required Hospitalization of more than 24 hours. Treatment normally taken on an out-patient basis is not included in the scope of this definition.” |
| Authoritative PDF evidence | Select, page 4: “**Day Care Treatment** means medical treatment, and/or **Surgical Procedure** which is: i. undertaken under **General or Local Anesthesia** in a **Hospital/Day Care Centre** in less than **24 hrs** because of technological advancement, and ii. which would have otherwise required **Hospitalization** of more than 24 hours. Treatment normally taken on an out-patient basis is not included in the scope of this definition.” The separately matched page-5 inpatient definition says “more than 24 hours”; page 5 also defines Hospitalization as a minimum of 24 consecutive inpatient-care hours with a specified-procedure exception. |
| Problem | **Source truth → gold:** visual PDF review resolves the earlier uncertainty: the PDF says American-spelled/capitalized “Anesthesia” and abbreviated “24 hrs”; gold says “anaesthesia” and “24 hours.” These are character changes that conservative matching must not guess. **Extraction:** unchanged PyMuPDF agrees with the PDF on those disputed forms. |
| Proposed atomic unit(s) | U1: qualifying day-care treatment may be under 24 hours only when performed under general/local anesthesia in a hospital/day-care centre because of technological advancement, would otherwise require over 24 hours of hospitalization, and is not ordinary outpatient treatment. Keep these conjunctive conditions and exception together. |
| Proposed source fragment(s) | U1: the complete page-4 definition quoted under “Authoritative PDF evidence.” |
| Required for sufficiency? | **Yes.** The already matched inpatient span answers the ordinary duration, but U1 is necessary to answer whether and under what conditions sub-24-hour treatment qualifies. |
| Proposed change type | **annotation correction** — correct only the transcription to PDF wording; do not copy parser artifacts beyond what the PDF visibly says. |
| Retrieval observation | The page-4 chunk containing the full definition is absent from Top 10. Same-policy page-5 chunks are ranks 6 and 7 and support the other gold span, not this day-care definition. After correction, this remains a genuine Top-10 retrieval miss. |
| Reviewer decision | `PENDING` |

### Q004 — unmatched span 1 of 1

| Field | Required content |
| --- | --- |
| Question ID | Q004 |
| Question | How many days of pre- and post-hospitalization expenses are covered? |
| Current gold | `medicare_select_policy_wording_0faeeb61c5.pdf`, page 12: “We will cover expenses for pre-hospitalization consultations, investigations and medicines incurred upto 90 days prior to the date of admission to the Hospital. Any pre-hospitalization expenses incurred prior to Policy Period shall not be covered. The benefit is payable if We have admitted a claim under B1, B4, or B6. We will cover expenses for post-hospitalization consultations, investigations and medicines incurred upto 90 days after discharge from the Hospital. The benefit is payable if We have admitted a claim under B1, B4, or B6.” |
| Authoritative PDF evidence | Select, page 12. Pre: “We will cover expenses for pre-hospitalization consultations, investigations and medicines incurred upto 90 days prior to the date of admission to the Hospital. Any pre-hospitalization expenses incurred prior to Policy Period shall not be covered. The benefit is payable if We have admitted a claim under B1, B4, or B6.” Post: “We will cover expenses for post-hospitalization consultations, investigations and medicines incurred upto 90 days after discharge from the Hospital. The benefit is payable if We have admitted a claim under B1, B4, or B6.” |
| Problem | **Gold representation:** two benefits separated by the B3 heading are represented as one contiguous quote. **Extraction:** both passages and the heading are readable and preserved. The failure is not retrieval. |
| Proposed atomic unit(s) | U1: pre-hospitalization is covered up to 90 days before admission, excludes expenses before the Policy Period, and requires an admitted B1/B4/B6 claim. U2: post-hospitalization is covered up to 90 days after discharge and requires an admitted B1/B4/B6 claim. |
| Proposed source fragment(s) | U1: contiguous page-12 pre passage quoted above. U2: contiguous page-12 post passage quoted above. |
| Required for sufficiency? | **U1 yes; U2 yes.** The question expressly asks for both durations. The qualifications remain attached rather than being discarded to make matching easier. |
| Proposed change type | **decomposition** |
| Retrieval observation | Both complete passages occur in the correct page-12 chunk at rank 2 (success only at the stored K values 3, 5, and 10 under the proposal). |
| Reviewer decision | `PENDING` |

### Q007 — unmatched span 1 of 1

| Field | Required content |
| --- | --- |
| Question ID | Q007 |
| Question | What is the initial waiting period for illness and what are its exceptions? |
| Current gold | `medicare_select_policy_wording_0faeeb61c5.pdf`, page 22: “Expenses related to the treatment of any Illness within 30 days from the first Policy commencement date shall be excluded except claims arising due to an Accident, provided the same are covered. This exclusion shall not, however, apply if the Insured Person has Continuous Coverage for more than twelve months. The within referred waiting period is made applicable to the enhanced Sum Insured in the event of granting higher Sum Insured subsequently.” |
| Authoritative PDF evidence | Select, page 22, “iii. 30 Days Waiting Period (Code- Excl 03)”: “a. Expenses related to the treatment of any Illness within 30 days from the first Policy commencement date shall be excluded except claims arising due to an Accident, provided the same are covered.” “b. This exclusion shall not, however, apply if the Insured Person has Continuous Coverage for more than twelve months.” “c. The within referred waiting period is made applicable to the enhanced Sum Insured in the event of granting higher Sum Insured subsequently.” |
| Problem | **Gold representation/evaluator:** gold retains each substantive clause but drops the visible list markers, causing contiguous matching to fail. The unchanged extraction preserves `a.`, `b.`, and `c.`. |
| Proposed atomic unit(s) | U1: 30-day illness exclusion plus covered-accident exception. U2: exception after more than twelve months’ Continuous Coverage. U3: application to a subsequently enhanced Sum Insured. |
| Proposed source fragment(s) | U1/U2/U3: the respective complete contiguous clauses a/b/c quoted above. |
| Required for sufficiency? | **U1 yes; U2 yes; U3 yes.** The benchmark rubric calls for the waiting period, accident exception, continuous-coverage exception, and enhanced-sum application. |
| Proposed change type | **decomposition** |
| Retrieval observation | One correct page-22 chunk at rank 3 contains all three complete clauses; a second same-page chunk at rank 6 is partial. |
| Reviewer decision | `PENDING` |

### Q008 — unmatched span 2 of 3

| Field | Required content |
| --- | --- |
| Question ID | Q008 |
| Question | If cataract is also a pre-existing disease, which waiting period applies? |
| Current gold | `medicare_select_policy_wording_0faeeb61c5.pdf`, page 21: “Expenses related to the treatment of the listed conditions, surgeries/treatments shall be excluded until the expiry of 24 months of continuous coverage after the date of inception of the first Policy with Us. If any of the specified disease/procedure falls under the waiting period specified for Pre-Existing Diseases, then the longer of the two waiting periods shall apply.” |
| Authoritative PDF evidence | Select, page 21: “a. Expenses related to the treatment of the listed conditions, surgeries/treatments shall be excluded until the expiry of 24 months of continuous coverage after the date of inception of the first Policy with Us. This exclusion shall not be applicable for claims arising due to an Accident.” Clause c: “If any of the specified disease/procedure falls under the waiting period specified for Pre-Existing Diseases, then the longer of the two waiting periods shall apply.” |
| Problem | **Gold representation:** noncontiguous clauses are presented as one quote and the accident exception is lost. Clause b is substantive but answers enhancement, not this question, so it should be neither silently bridged nor made a required unit here. Extraction preserves the list structure. |
| Proposed atomic unit(s) | U1: specified conditions have a 24-month continuous-coverage wait, except covered accident claims. U2: when a specified condition is also a PED, the longer waiting period applies. Existing span 1 supplies the 36-month PED period and span 3 identifies cataract as specified. |
| Proposed source fragment(s) | U1: complete page-21 clause a quoted above. U2: complete page-21 clause c quoted above. |
| Required for sufficiency? | **U1 yes; U2 yes.** Both are needed to derive 36 months for cataract-as-PED; the accident qualification is preserved with U1. |
| Proposed change type | **decomposition** |
| Retrieval observation | The correct page-21 chunk containing clauses a–c is rank 5. The separate page-20 PED span is rank 8. For the full question, stored Top 10 contains all proposed evidence; this unmatched span becomes covered at K=5. |
| Reviewer decision | `PENDING` |

### Q010 — unmatched span 1 of 1

| Field | Required content |
| --- | --- |
| Question ID | Q010 |
| Question | How is the Favorable Experience Discount calculated? |
| Current gold | `medicare_select_policy_wording_0faeeb61c5.pdf`, page 29: “At Renewal, the applicable Favorable Experience Discount will depend on below criteria: Claim Years in last 3 Policy Years Discount 3 Years 0% 2 Years 5% 1 Year 10% No Claim 20% Where ‘Claim Year’ is a Policy year in which one or more claim(s) have been paid. For the purpose of Favorable Experience Discount, a Policy year with claim only under ‘Daily Cash for choosing Twin Sharing Accommodation’, ‘Daily Cash for choosing Multi-Sharing Accommodation’ and ‘Maternity Care’ benefit will not be considered a ‘Claim Year’.” |
| Authoritative PDF evidence | Select, page 29: “At Renewal, the applicable Favorable Experience Discount will depend on below criteria:” followed by “3 Years 0% / 2 Years 5% / 1 Year 10% / No Claim 20%.” Then: “Where ‘Claim Year’ is a Policy year in which one or more claim(s) have been paid. For the purpose of Favorable Experience Discount, a Policy year with claim only under ‘Daily Cash for choosing Twin Sharing Accommodation’, ‘Daily Cash for choosing Multi-Sharing Accommodation’ and ‘Maternity Care’ benefit will not be considered a ‘Claim Year’” (no final full stop is printed). |
| Problem | **Evaluator:** only terminal punctuation defeats full-span matching. Extraction otherwise preserves the table values and prose in order. The punctuation difference does not alter source truth. |
| Proposed atomic unit(s) | U1: the four claim-year-to-discount table rows. U2: definition of Claim Year and the complete exception for the three named benefits. |
| Proposed source fragment(s) | U1: contiguous page-29 table and its introduction. U2: contiguous page-29 prose beginning “Where ‘Claim Year’…” and ending “Claim Year’”. |
| Required for sufficiency? | **U1 yes; U2 yes.** Rates alone do not explain which claims count. |
| Proposed change type | **evaluator-only** — deterministic punctuation normalization; proposed units may be encoded during v2 migration without changing source truth. |
| Retrieval observation | The correct page-29 chunk is rank 1 and contains all evidence. |
| Reviewer decision | `PENDING` |

### Q011 — unmatched span 1 of 1

| Field | Required content |
| --- | --- |
| Question ID | Q011 |
| Question | What does Global Cover for Planned Hospitalization cover? |
| Current gold | `tata_aig_medicare_premier_policy_wordings_781aa2fd94.pdf`, page 16: “We will cover for Medical Expenses of the Insured Person incurred outside India, upto the sum insured, provided that the diagnosis was made in India and the insured travels abroad for treatment. The Medical Expenses payable shall be limited to Inpatient and daycare Hospitalization. Any claim under this cover can be made only on reimbursement basis. Cashless facility may be arranged on case to case basis. Insured person can contact us for claim assistance. Only the balance basic sum insured along with No Claim Bonus can be used for this and not the restored sum insured.” |
| Authoritative PDF evidence | Premier, page 16: “We will cover for Medical Expenses of the Insured Person incurred outside India, upto the sum insured, provided that the diagnosis was made in India and the insured travels abroad for treatment. The Medical Expenses payable shall be limited to Inpatient and daycare Hospitalization. Any claim under this cover can be made only on reimbursement basis. Cashless facility may be arranged on case to case basis. Insured person can contact us for claim assistance.” Later: “Only the balance basic sum insured along with No Claim Bonus can be used for this and not the restored sum insured.” |
| Problem | **Gold representation:** the current span fabricates contiguity across a substantive currency-conversion rule. Extraction correctly includes that paragraph between the passages. |
| Proposed atomic unit(s) | U1: outside-India planned treatment is covered up to Sum Insured when diagnosed in India and travel is for treatment, limited to inpatient/day-care hospitalization, on reimbursement (cashless only case by case). U2: only remaining basic Sum Insured plus No Claim Bonus may be used, not restored Sum Insured. |
| Proposed source fragment(s) | U1: first contiguous page-16 passage quoted above. U2: later contiguous page-16 sentence quoted above. |
| Required for sufficiency? | **U1 yes; U2 yes.** U2 is a material available-limit qualification in the expected answer. The omitted exchange-rate paragraph is true source content but not required to answer the benchmark question as currently scoped. |
| Proposed change type | **decomposition** |
| Retrieval observation | The correct page-16 chunk is rank 1 and contains both fragments plus the intervening exchange-rate rule. |
| Reviewer decision | `PENDING` |

### Q012 — unmatched span 2 of 2

| Field | Required content |
| --- | --- |
| Question ID | Q012 |
| Question | What are the eligibility/status conditions for Global Cover? |
| Current gold | `tata_aig_medicare_premier_policy_wordings_781aa2fd94.pdf`, page 17: “B13. ‘Global Cover for Planned Hospitalization’ as a Benefit is: a) not available under this policy and no claim shall be admissible under this section where either the policyholder or any of the Insured Person(s) is a Foreign National or their Residence Status at the time of proposal or anytime during the policy period/ renewal is: • Non-Resident Indian (NRI); or • Overseas Citizen of India (OCI) b) not available under this Policy and no claim shall be admissible under this section, if the Policyholder or any of the Insured Person(s), as a Resident Indian National, has agreed to opt out of this Benefit at the time of proposal or at renewal. If the coverage under B13. ‘Global Cover for Planned Hospitalization’ is once opted out, then neither the policyholder nor the Insured Person can take coverage under this benefit.” |
| Authoritative PDF evidence | Premier, page 17: “Please note that, B13. ‘Global Cover for Planned Hospitalization’ as a Benefit is: a) not available under this policy and no claim shall be admissible under this section where either the policyholder or any of the Insured Person(s) is a Foreign National or their Residence Status at the time of proposal or anytime during the policy period/ renewal is: • Non-Resident Indian (NRI); or • Overseas Citizen of India (OCI) b) not available under this Policy and no claim shall be admissible under this section, if the Policyholder or any of the Insured Person(s), as a Resident Indian National, has agreed to opt out of this Benefit at the time of proposal or at renewal. If the coverage under B13. ‘Global Cover for Planned Hospitalization’ is once opted out, then neither the policyholder nor the Insured Person can take coverage under this benefit.” |
| Problem | **Chunk boundary/evaluator:** the PDF and gold meaning agree and extraction contains the complete normalized span. The source interval falls across two overlapping chunks: rank 1 ends before the final word; rank 3 contains the ending but not the beginning. A single-chunk containment rule reports a false negative even though Top-3 collectively covers the complete ordered interval. |
| Proposed atomic unit(s) | U1: exclusion for Foreign National/NRI/OCI status at proposal or during policy/renewal. U2: Resident Indian opt-out at proposal/renewal makes the benefit unavailable and, once opted out, neither policyholder nor insured can later take it. |
| Proposed source fragment(s) | U1: contiguous page-17 condition a. U2: contiguous page-17 condition b plus immediately following no-opt-back sentence. |
| Required for sufficiency? | **U1 yes; U2 yes.** They are independent status/choice restrictions asked for in the plural. |
| Proposed change type | **evaluator-only** — ordered collective Top-K coverage; no annotation correction. |
| Retrieval observation | Correct page-17 chunks are ranks 1 and 3. Rank 1 alone is incomplete; their union covers the full source evidence at K=3, 5, and 10. This is the primary recorded chunk-boundary case. |
| Reviewer decision | `PENDING` |

### Q019 — unmatched span 1 of 1

| Field | Required content |
| --- | --- |
| Question ID | Q019 |
| Question | What maternity limit applies for a girl child at ₹50 lakh Sum Insured and what is the waiting period? |
| Current gold | `tata_aig_medicare_premier_policy_wordings_781aa2fd94.pdf`, page 20: “We will cover for Maternity Expenses, upto limits as specified in the table below, per policy subject to a waiting period of 3 years of continuous coverage under this policy. Basic Sum Insured Limit Up to Rs. 50 Lacs A maximum of upto Rs 50,000/-. In case of birth of a girl child, the maximum limit under this coverage would be upto Rs 60,000/- per policy” |
| Authoritative PDF evidence | Premier, page 20: “We will cover for Maternity Expenses, upto limits as specified in the table below, per policy subject to a waiting period of 3 years of continuous coverage under this policy.” The “Up to Rs. 50 Lacs” row states “A maximum of upto Rs 50,000/-. In case of birth of a girl child, the maximum limit under this coverage would be upto Rs 60,000/- per policy”. |
| Problem | **Evaluator:** unchanged extraction places whitespace before punctuation (`policy .`), while gold/PDF read `policy.`. The facts and order are unchanged. |
| Proposed atomic unit(s) | U1: three-year continuous-coverage waiting period. U2: for Sum Insured up to Rs. 50 Lacs, ordinary cap Rs 50,000 and girl-child cap Rs 60,000 per policy. |
| Proposed source fragment(s) | U1: contiguous page-20 introductory sentence. U2: contiguous page-20 table-row text quoted above. |
| Required for sufficiency? | **U1 yes; U2 yes.** The question asks both the girl-child amount and waiting period; the base cap anchors which table row is being interpreted. |
| Proposed change type | **evaluator-only** — whitespace adjacent to punctuation. |
| Retrieval observation | The correct page-20 chunk is rank 1 and contains the complete evidence. |
| Reviewer decision | `PENDING` |

### Q026 — unmatched span 1 of 1

| Field | Required content |
| --- | --- |
| Question ID | Q026 |
| Question | How does the Cumulative Bonus increase and decrease? |
| Current gold | `tata_aig_medicare_reserve_policy_wordings_2250e6352a.pdf`, page 17: “50% Cumulative Bonus will be applied on the Sum Insured of the expiring Policy, on each Renewal after every claim free Policy Year, provided that the Policy is renewed with Us and without a break. The maximum Cumulative Bonus shall not exceed 100% of the Sum Insured in any Policy Year. If a Cumulative Bonus has been applied and a claim is made, then in the subsequent Policy Year, We will automatically decrease the Cumulative Bonus by 50% of the Sum Insured in that following Policy Year. There will be no impact on the base Sum Insured, only the accrued Cumulative Bonus will be decreased.” |
| Authoritative PDF evidence | Reserve, page 17: “i. 50% Cumulative Bonus will be applied on the Sum Insured of the expiring Policy, on each Renewal after every claim free Policy Year, provided that the Policy is renewed with Us and without a break. The maximum Cumulative Bonus shall not exceed 100% of the Sum Insured in any Policy Year.” “ii. If a Cumulative Bonus has been applied and a claim is made, then in the subsequent Policy Year, We will automatically decrease the Cumulative Bonus by 50% of the Sum Insured in that following Policy Year. There will be no impact on the base Sum Insured, only the accrued Cumulative Bonus will be decreased.” |
| Problem | **Gold representation:** list structure is omitted between two independently required rules. Extraction preserves `ii.`. |
| Proposed atomic unit(s) | U1: accrues 50% after each claim-free renewal without break, capped at 100% of Sum Insured. U2: after a claim, decreases by 50% of Sum Insured next year, affecting only accrued bonus and not base Sum Insured. |
| Proposed source fragment(s) | U1/U2: complete contiguous clauses i/ii quoted above. |
| Required for sufficiency? | **U1 yes; U2 yes.** The question explicitly asks increase and decrease; the cap and base-protection qualifications remain attached. |
| Proposed change type | **decomposition** |
| Retrieval observation | The correct page-17 chunk containing both clauses is rank 4 (covered at stored K=5 and 10). |
| Reviewer decision | `PENDING` |

### Q027 — unmatched span 1 of 1

| Field | Required content |
| --- | --- |
| Question ID | Q027 |
| Question | Does Pocket Protect remain available after the Aggregate Deductible is waived? |
| Current gold | `tata_aig_medicare_reserve_policy_wordings_2250e6352a.pdf`, page 14: “This benefit will not be applicable after the Insured Person(s) has opted Waiver of Aggregate Deductible.” |
| Authoritative PDF evidence | Reserve, page 14: “This benefit will not be applicable after the Insured Person(s) has opted Waiver of Aggregate Deductible” (the printed line has no final full stop). |
| Problem | **Evaluator:** gold adds only terminal punctuation. Extraction and retrieval preserve all letters and the negation. |
| Proposed atomic unit(s) | U1: Pocket Protect is not applicable after waiver of Aggregate Deductible. |
| Proposed source fragment(s) | U1: the complete page-14 sentence quoted above. |
| Required for sufficiency? | **Yes.** It directly and completely answers the question. |
| Proposed change type | **evaluator-only** — terminal punctuation normalization. |
| Retrieval observation | The correct page-14 chunk is rank 3 (covered at stored K=3, 5, and 10). |
| Reviewer decision | `PENDING` |

### Q028 — unmatched span 1 of 1

| Field | Required content |
| --- | --- |
| Question ID | Q028 |
| Question | How long does TransiCare Wallet coverage remain available after employer-group coverage terminates? |
| Current gold | `tata_aig_medicare_reserve_policy_wordings_2250e6352a.pdf`, page 18: “This benefit will be available for hospitalization occurring during ninety (90) consecutive days from the termination date of the Employer-Employee Group Health Insurance Policy. This cover will remain in force for ninety (90) consecutive days from the effective start date or till the insured person gets covered under a separate Employer-Employee Group Health Insurance Policy, whichever is earlier, subject to this Policy being in force.” |
| Authoritative PDF evidence | Reserve, page 18: “iv. This benefit will be available for hospitalization occurring during ninety (90) consecutive days from the termination date of the Employer-Employee Group Health Insurance Policy.” “v. This cover will remain in force for ninety (90) consecutive days from the effective start date or till the insured person gets covered under a separate Employer-Employee Group Health Insurance Policy, whichever is earlier, subject to this Policy being in force.” |
| Problem | **Gold representation:** two clauses are falsely presented as one contiguous sentence sequence. Extraction preserves the clause marker. |
| Proposed atomic unit(s) | U1: eligible hospitalization must occur during 90 consecutive days from employer-group termination. U2: the cover ends at the earlier of 90 consecutive days from effective start or separate employer-group coverage, and the Policy must remain in force. |
| Proposed source fragment(s) | U1/U2: complete contiguous clauses iv/v quoted above. |
| Required for sufficiency? | **U1 yes; U2 yes.** The second is a limiting exception to the apparent 90-day duration and cannot be dropped. |
| Proposed change type | **decomposition** |
| Retrieval observation | The correct page-18 chunk at rank 1 contains both complete clauses. |
| Reviewer decision | `PENDING` |

### Q029 — unmatched span 1 of 1

| Field | Required content |
| --- | --- |
| Question ID | Q029 |
| Question | What are the main eligibility conditions for Inbound Emergency Hospitalization? |
| Current gold | `tata_aig_medicare_reserve_policy_wordings_2250e6352a.pdf`, page 19: “C3 Inbound Emergency Hospitalization (Applicable for Non-Resident Indian (NRI) or Overseas Citizen of India (OCI) Insured Person(s)) In consideration of the additional premium paid, We will cover the Medical Expenses incurred towards an emergency arising out of an Accident of the Non-Resident Indian (NRI) or Overseas Citizen of India (OCI) Insured Person whilst on a trip to India up to the limit specified in the Policy schedule. This Cover will be available only for benefits admissible under section B1 or B4 of this Policy, subject to the conditions specified below: • This Cover will be applicable only to the Insured Person(s) as mentioned in the Policy Schedule at the inception of the Policy, up to the limit specified in the Policy Schedule. • The Medical Condition necessitating emergency Hospitalization must first be diagnosed in India, during the same trip in which the Hospitalization occurs. • We will indemnify Medical Expenses incurred towards Medically Necessary Treatment for Emergency Care until such time as the Insured Person’s medical condition is stabilized, as certified by the treating Medical Practitioner. Any planned Hospitalizations will not be covered. • We shall not be liable to make any payment under this Cover for any claim arising out of, caused by, or attributable to any Pre-Existing Disease, complication, or consequence thereof. • The Inbound Emergency Hospitalization will not be available in the Policy after the insured has opted for waiver of Aggregate Deductible.” |
| Authoritative PDF evidence | Reserve, page 19: C3 applies to NRI/OCI insured persons and covers, for additional premium, medical expenses for an emergency arising out of an Accident while on a trip to India, up to the schedule limit, only for B1/B4 benefits. The complete bullets state: named in the Schedule at inception/up to its limit; opted Aggregate Deductible does not apply; first diagnosis in India during that trip; medically necessary Emergency Care until certified stable and no planned hospitalization; no PED-related claim; separate limit above base Sum Insured/no NCB impact; unavailable after waiver of Aggregate Deductible. |
| Problem | **Gold representation:** selected noncontiguous bullets are stitched across two substantive benefits/limit bullets. **Chunks:** the long evidence is also split, so decomposition and collective coverage are both relevant. The extraction faithfully exposes the omitted bullets rather than causing the mismatch. |
| Proposed atomic unit(s) | U1: NRI/OCI, additional premium, Accident emergency during trip to India, schedule limit, B1/B4 only. U2: named in Schedule at inception/up to schedule limit. U3: Aggregate Deductible does not apply. U4: condition first diagnosed in India during same trip. U5: medically necessary Emergency Care only until practitioner-certified stabilization; planned hospitalization excluded. U6: PED/complication/consequence excluded. U7: separate above-base-Sum-Insured limit and no NCB impact. U8: unavailable after waiver of Aggregate Deductible. |
| Proposed source fragment(s) | U1: contiguous heading/opening paragraph on page 19. U2–U8: each complete contiguous page-19 bullet in printed order. |
| Required for sufficiency? | **Proposed: U1, U2, U4, U5, U6, and U8 yes** because they define who, event, trip/diagnosis, emergency-only duration, and exclusions. **U3 and U7 no for the present “eligibility conditions” wording**: they concern claim mechanics/benefit accounting, but must remain represented as source truth and not be bridged over. Owner judgment is specifically requested on this boundary. |
| Proposed change type | **decomposition** |
| Retrieval observation | Correct page-19 chunks at ranks 1 and 2 collectively preserve the currently cited facts; neither alone contains the complete current composite. Proposed sufficiency is reached at K=3 only if the owner approves U3/U7 as non-required. |
| Reviewer decision | `PENDING` |

### Q033 — unmatched span 1 of 1

| Field | Required content |
| --- | --- |
| Question ID | Q033 |
| Question | How many days of pre- and post-hospitalization expenses are covered? |
| Current gold | `Tata_AIG_Medi_Care_Plus_e8a0cf5358.pdf`, page 7: “We will cover for expenses for Pre-Hospitalization consultations, investigations and medicines incurred upto 60 days before the date of admission to the hospital. The benefit is payable if We have admitted a claim under B1 or B4 or B6. We will cover for expenses for Post-Hospitalization consultations, investigations and medicines incurred upto 90 days after discharge from the hospital. The benefit is payable if We have admitted a claim under B1 or B4 or B6.” |
| Authoritative PDF evidence | Plus, page 7. Pre: “We will cover for expenses for Pre-Hospitalization consultations, investigations and medicines incurred upto 60 days before the date of admission to the hospital. The benefit is payable if We have admitted a claim under B1 or B4 or B6.” Post: “We will cover for expenses for Post-Hospitalization consultations, investigations and medicines incurred upto 90 days after discharge from the hospital. The benefit is payable if We have admitted a claim under B1 or B4 or B6.” |
| Problem | **Gold representation:** separate B2/B3 benefits are concatenated. **Extraction representation:** fragmented words, soft hyphens, and the printed page number inserted into the pre sentence prevent ordinary normalized matching, although the text remains readable. Gold must remain the visually verified PDF wording. |
| Proposed atomic unit(s) | U1: 60 days before admission for pre-hospitalization consultations/investigations/medicines, conditional on admitted B1/B4/B6 claim. U2: 90 days after discharge for the corresponding post-hospitalization expenses, with the same condition. |
| Proposed source fragment(s) | U1/U2: the respective contiguous visual page-7 B2/B3 passages quoted above. |
| Required for sufficiency? | **U1 yes; U2 yes.** Both durations are requested; their claim-admission qualifications stay attached. |
| Proposed change type | **decomposition** — evaluator canonicalization is also required to map extraction, but gold should not adopt corruption. |
| Retrieval observation | The page-7 chunk at rank 4 contains both passages; the post passage is repeated in another chunk at rank 9. Proposed units are present at stored K=5 and 10. |
| Reviewer decision | `PENDING` |

### Q034 — unmatched span 1 of 1

| Field | Required content |
| --- | --- |
| Question ID | Q034 |
| Question | If the insured has multiple health policies, can they choose which policy to claim under? |
| Current gold | `Tata_AIG_Medi_Care_Plus_e8a0cf5358.pdf`, page 15: “In case of multiple policies taken by an insured person during a period from one or more insurers to indemnify treatment costs, the insured person shall have the right to require a settlement of his/her claim in terms of any of his/her policies. In all such cases the insurer chosen by the insured person shall be obliged to settle the claim as long as the claim is within the limits of and according to the terms of the chosen policy. If the amount to be claimed exceeds the Sum Insured under a single Policy, the Insured Person shall have the right to choose Insurer from whom he/she wants to claim the balance amount and we will assist the insured person in facilitating the same.” |
| Authoritative PDF evidence | **Plus page 14:** “i. In case of multiple policies taken by an insured person during a period from one or more insurers to indemnify” (sentence continues). **Plus page 15:** “treatment costs, the insured person shall have the right to require a settlement of his/her claim in terms of any of his/her policies. In all such cases the insurer chosen by the insured person shall be obliged to settle the claim as long as the claim is within the limits of and according to the terms of the chosen policy.” Page-15 clause iii: “If the amount to be claimed exceeds the Sum Insured under a single Policy, the Insured Person shall have the right to choose Insurer from whom he/she wants to claim the balance amount and we will assist the insured person in facilitating the same.” |
| Problem | **Source truth → gold:** visual PDF inspection confirms that clause i begins on page 14 and continues on page 15; the page-15-only locator is wrong. **Gold representation:** it also fabricates contiguity across substantive clause ii (right to prefer disallowed amounts under this policy). Extraction begins the page-15 chunk with the continuation and cannot restore the page-14 opening. |
| Proposed atomic unit(s) | U1: for multiple indemnity policies, the insured may choose any policy for settlement; chosen insurer must settle within that policy’s limits/terms. This indivisible sentence crosses pages. U2: if the amount exceeds one policy’s Sum Insured, the insured may choose the insurer for the balance, with assistance. Clause ii is retained as source truth but not required by the current question/expected answer unless the owner broadens “which policy” to include disallowed-amount preference. |
| Proposed source fragment(s) | U1-F1: page-14 sentence opening quoted above; U1-F2: immediate page-15 continuation quoted above. Both fragments jointly form U1. U2: complete contiguous page-15 clause iii quoted above. |
| Required for sufficiency? | **U1 yes. Proposed U2 yes** because the current expected answer explicitly discusses the balance claim. Owner should confirm that scope. Clause ii proposed **no**, but the quote must not bridge across it. |
| Proposed change type | **annotation correction** — correct page locators and cross-page fragmentation; decomposition of clause iii is a necessary accompanying representation change. |
| Retrieval observation | Correct page-15 continuation/clauses are in rank 2. No correct Plus page-14 chunk is in Top 10. Because U1 requires both page fragments, this remains a genuine Top-10 miss; retrieving a sentence continuation cannot establish its multiple-policy antecedent by itself. |
| Reviewer decision | `PENDING` |

### Q038 — unmatched span 1 of 1

| Field | Required content |
| --- | --- |
| Question ID | Q038 |
| Question | When does the Health Checkup benefit become available and what is its limit? |
| Current gold | `Tata_AIG_Medi_Care_Plus_e8a0cf5358.pdf`, page 8: “We will cover for expenses for a Preventive Health Check-up upto 1% of previous sum insured subject to a maximum of Rs. 10,000/- per policy. The limit is the maximum per policy and more than one insured can utilize the amount. The benefit is payable once after block of every two continuous claim free policy years with us.” |
| Authoritative PDF evidence | Visual review of Plus page 8 confirms the current substantive wording: “Preventive Health Check-up upto 1 % of previous sum insured subject to a **maximum** of Rs. 10,000/- per policy. The limit is the maximum per policy and more than one insured can utilize the amount. The benefit is payable once after block of every two continuous claim free policy years with us.” The visible PDF has a space in `1 %`; it does **not** say `max` in place of the first `maximum`. |
| Problem | **Extraction representation, not source/gold semantics:** unchanged PyMuPDF fragments words (`Prevent ive`, `Hea lth`, `max\ni mum`, `ut\nil\nize`, `cont\ninuous`). The earlier diagnostic’s apparent `max`/`maximum` uncertainty is resolved by the visual PDF: `maximum` is authoritative. Gold differs only in harmless `1%` spacing. |
| Proposed atomic unit(s) | U1: allowance equals 1% of previous Sum Insured, capped at Rs. 10,000 per policy and shared across insured persons. U2: payable once after each block of two continuous claim-free policy years. |
| Proposed source fragment(s) | U1: contiguous first three page-8 sentences through “utilize the amount.” U2: contiguous next sentence ending “years with us.” |
| Required for sufficiency? | **U1 yes; U2 yes.** The question asks limit and availability. The shared per-policy nature is an essential limit qualification. |
| Proposed change type | **evaluator-only** — character-preserving compact canonicalization for extraction fragmentation; no weakening to semantic similarity. |
| Retrieval observation | The correct page-8 chunk is rank 1 and preserves the full meaning despite parser fragmentation. |
| Reviewer decision | `PENDING` |

### Q039 — unmatched span 1 of 1

| Field | Required content |
| --- | --- |
| Question ID | Q039 |
| Question | Is CPAP equipment payable under the Consumables benefit? |
| Current gold | `Tata_AIG_Medi_Care_Plus_e8a0cf5358.pdf`, page 8: “However the following items shall be excluded from scope of this coverage: External durable devices like Bi level Positive Airway Pressure (Bl PAP) machine, Continuous Positive Airway Pressure (CPAP) machine, Peritoneal Dialysis (PD) equipment and supplies, Nimbus/water/air bed, dialyzer and other medical equipments.” |
| Authoritative PDF evidence | Plus, page 8: “However the following items shall be excluded from scope of this coverage:” After the separate personal-comfort bullet: “External durable devices like Bilevel Positive Airway Pressure (BIPAP) machine, Continuous Positive Airway Pressure (CPAP) machine, Peritoneal Dialysis (PD) equipment and supplies, Nimbus/water/air bed, dialyzer and other medical equipments.” |
| Problem | **Gold representation:** introduction and second bullet are noncontiguous. **Extraction representation:** words such as `Positive` and `dialyzer` are fragmented, but the list and CPAP exclusion remain readable. |
| Proposed atomic unit(s) | U1: CPAP is an external durable device explicitly excluded from Consumables coverage. Keep the exclusion introduction and complete device bullet together as one proposition represented by two fragments; do not require the unrelated personal-comfort item. |
| Proposed source fragment(s) | U1-F1: contiguous page-8 exclusion introduction. U1-F2: complete contiguous external-durable-device bullet quoted above. |
| Required for sufficiency? | **Yes.** Both fragments are needed to establish that the device list is excluded; the intervening independent bullet is not. |
| Proposed change type | **decomposition** |
| Retrieval observation | The correct page-8 chunk at rank 1 contains the introduction, intervening bullet, and complete device bullet. |
| Reviewer decision | `PENDING` |

### Q040 — unmatched span 1 of 2

| Field | Required content |
| --- | --- |
| Question ID | Q040 |
| Question | Does the policy wording establish that a mid-year change from NRI to resident automatically terminates coverage? |
| Current gold | `Tata_AIG_Medi_Care_Plus_e8a0cf5358.pdf`, page 15: “The Company may cancel the policy at any time on grounds of established fraud, misrepresentation or non-disclosure of material facts by the Policyholder/Insured Person by giving 15 days’ written notice.” |
| Authoritative PDF evidence | Plus, page 15, Cancellation clause ii: “The Company may cancel the policy at any time on grounds of established fraud, misrepresentation or non-disclosure of material facts by the Policyholder/Insured Person by giving 15 days’ written notice. There would be no refund of premium on cancellation on established fraud, misrepresentation or non-disclosure of material facts.” |
| Problem | **Evaluation mode:** this is relevant cancellation context but cannot prove the document-wide absence of an automatic NRI-to-resident termination rule. Extraction is heavily fragmented (`misrepresentat ion`, soft-hyphenated non-disclosure, etc.); that mapping issue must not convert contextual evidence into positive proof. |
| Proposed atomic unit(s) | N1: contextual cancellation rule—company cancellation requires an enumerated ground and 15 days’ written notice; no premium refund for those grounds. This is a negative-space review context, not a positive-evidence denominator unit. |
| Proposed source fragment(s) | N1: complete contiguous page-15 clause ii quoted above, including the refund consequence so the clause is not truncated. |
| Required for sufficiency? | **No.** It can support an abstention/entailment review but cannot alone establish that no automatic termination provision exists elsewhere. |
| Proposed change type | **negative-space** |
| Retrieval observation | No correct page-15 Plus chunk appears in Top 10 for Q040. The question was already excluded from positive Recall aggregation; retain that treatment. |
| Reviewer decision | `PENDING` |

### Q040 — unmatched span 2 of 2

| Field | Required content |
| --- | --- |
| Question ID | Q040 |
| Question | Does the policy wording establish that a mid-year change from NRI to resident automatically terminates coverage? |
| Current gold | `Tata_AIG_Medi_Care_Plus_e8a0cf5358.pdf`, page 18: “This Policy, its Schedule, endorsement(s), proposal constitutes the entire contract of insurance. No change in this policy shall be valid unless approved by Us and such approval be endorsed hereon.” |
| Authoritative PDF evidence | Plus, page 18: “This Policy, its Schedule, endorsement(s), proposal constitutes the entire contract of insurance. No change in this policy shall be valid unless approved by Us and such approval be endorsed hereon.” |
| Problem | **Evaluation mode:** the entire-contract provision is relevant context but not proof of the absence of an automatic termination rule. Extraction fragments multiple words (`Th i s Pol i cy`, `Sc he d ule`, `e ndorsement(s)`), which v2 could map deterministically only for diagnostic citation review. |
| Proposed atomic unit(s) | N2: contextual entire-contract/change-approval rule. It is not a positive evidence unit for a document-wide negative claim. |
| Proposed source fragment(s) | N2: complete contiguous page-18 two-sentence provision quoted above. |
| Required for sufficiency? | **No.** A correct answer must abstain from inventing the automatic rule; this passage alone cannot demonstrate exhaustive document search. |
| Proposed change type | **negative-space** |
| Retrieval observation | No correct page-18 Plus chunk appears in Top 10 for Q040. This remains outside positive Recall. |
| Reviewer decision | `PENDING` |

## Decision summary

### Count by proposed change type

Counts use the 18 unmatched **spans**, so Q040 contributes two separate
negative-space cases.

| Proposed change type | Count | Cases |
| --- | ---: | --- |
| Annotation correction | 2 | Q002/2, Q034/1 |
| Decomposition | 9 | Q004/1, Q007/1, Q008/2, Q011/1, Q026/1, Q028/1, Q029/1, Q033/1, Q039/1 |
| Evaluator-only | 5 | Q010/1, Q012/2, Q019/1, Q027/1, Q038/1 |
| Negative-space | 2 | Q040/1, Q040/2 |
| **Total** | **18** | |

### Cases requiring genuine gold correction

1. **Q002/2:** change `anaesthesia` → visually printed `Anesthesia` and
   `24 hours` → `24 hrs` (with faithful casing/transcription as approved).
2. **Q034/1:** record the clause-i opening on page 14 and its continuation on
   page 15; stop representing clause i and clause iii as one contiguous quote.

Q038 is **not** a genuine wording correction after visual review. The PDF says
`maximum`; the apparent discrepancy came from fragmented extraction. Its `1 %`
spacing can be handled deterministically without changing truth.

### Cases requiring only evaluator behavior changes

- **Q010/1:** terminal punctuation;
- **Q012/2:** ordered collective coverage across stored chunks at ranks 1 and 3;
- **Q019/1:** whitespace before punctuation;
- **Q027/1:** terminal punctuation; and
- **Q038/1:** character-preserving handling of extraction fragmentation and
  percent spacing.

These five do not need source-truth changes. The proposed v2 schema may still
encode reviewed units for consistent scoring, but that is migration, not a gold
correction.

### Genuine retrieval misses after proposed correction

- **Q002/2:** the authoritative day-care definition on Select page 4 is absent
  from Top 10.
- **Q034/1:** the required opening of the cross-page multiple-policy sentence on
  Plus page 14 is absent from Top 10; rank 2 contains only its page-15
  continuation and later clauses.

Q040's missing contextual chunks are not classified as positive retrieval
misses because the question is a negative-space probe and is excluded from the
positive evidence metric. No corrected Recall@K is calculated here.

### Unresolved cases requiring owner judgment

All rows require explicit approval, but three decisions are substantively open:

1. **Q029:** approve whether Aggregate Deductible non-application (U3) and the
   separate benefit-limit/no-NCB rule (U7) are outside “main eligibility
   conditions.” If they are required, the sufficient set and stored-hit
   disposition must reflect that; they must never be silently skipped.
2. **Q034:** confirm that the balance-claim rule (U2) is required because it is
   in the expected answer, and that clause ii is contextual but not required.
3. **Q040:** approve continued exclusion from positive Evidence Recall and defer
   it to a separately specified abstention/negative-space evaluation. Neither
   contextual span proves document-wide absence.

## Constraints, limitations, and next step

- **No score:** this review makes no corrected Recall@K claim.
- **No system mutation:** gold, schema, evaluator, extraction, chunks,
  embeddings, retrieval code, and recorded artifacts remain unchanged.
- **No paid calls:** inspection was local and used no Voyage or other paid API.
- **Limitation:** PDF text is visually authoritative here, but this document does
  not add coordinate-level anchors. V2 implementation should preserve reviewed
  page locators and auditable match witnesses.
- **Security/cost:** only public policy wordings and existing local artifacts
  were inspected; no secrets or customer data were used. Incremental API cost
  was zero.
- **Recommended next experiment:** after owner approval, version the approved
  annotations and implement deterministic v2 matching behind a version flag.
  First test it against a small adversarial match/non-match calibration set,
  then rescore the *stored* hits without a retrieval or embedding call and
  publish a separate v2 result rather than overwriting Experiment 1.
