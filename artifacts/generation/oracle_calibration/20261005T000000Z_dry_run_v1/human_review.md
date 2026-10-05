# Oracle-context generation calibration — human review

> Semantic labels are intentionally blank. A factual claim is the smallest independently supportable policy proposition. Do not split stylistic wording; split parts that could independently be true/false or require different evidence. For example, review a waiting period separately from an independently evidenced eligibility condition.

Use Generation Evaluation Contract v1 labels: correctness (`correct` / `incorrect` / `uncertain`; Q040 `not_applicable`), required facts (`present` / `absent` / `contradicted` / `uncertain`), claim grounding (`supported` / `unsupported` / `uncertain`), citation support (`supported` / `not_supported` / `uncertain`), and Q040 abstention (`appropriate` / `inappropriate` / `uncertain`).

## Q001
**Question:** How does the policy define an Accident?

**Generated answer:** Not generated (validation-only dry run).

**Expected answer:** An Accident is a sudden, unforeseen and involuntary event caused by external, visible and violent means.

**Required facts:**
- [ ] Fact 0: The event is sudden, unforeseen and involuntary. — label: ____
- [ ] Fact 1: It is caused by external, visible and violent means. — label: ____

**Supplied oracle evidence / provenance:**
- `Q001-U1-F1` — `medicare_select_policy_wording_0faeeb61c5.pdf`, p. 2 (authoritative_evidence): An Accident means sudden, unforeseen and involuntary event caused by external, visible and violent means.

**Reviewer labels:**
- Correctness: ____
- Factual claim support (label each claim): ____
- Citation support (label each claim/citation link): ____
- Q040 abstention appropriateness: ____
- Uncertainty / comments: ____

## Q002
**Question:** What minimum duration qualifies as hospitalization, and can treatment under 24 hours qualify?

**Generated answer:** Not generated (validation-only dry run).

**Expected answer:** Inpatient care requires a stay of more than 24 hours. Treatment lasting under 24 hours can qualify as Day Care Treatment when it is medically necessary, is undertaken under general or local anaesthesia in a hospital/day-care centre in less than 24 hours because of technological advancement, and would otherwise have required hospitalization of more than 24 hours; ordinary outpatient treatment does not qualify.

**Required facts:**
- [ ] Fact 0: Inpatient care requires more than 24 hours in hospital. — label: ____
- [ ] Fact 1: Qualifying day-care treatment can take less than 24 hours because of technological advancement. — label: ____
- [ ] Fact 2: It must otherwise have required hospitalization for more than 24 hours and ordinary outpatient treatment is excluded. — label: ____

**Supplied oracle evidence / provenance:**
- `Q002-U1-F1` — `medicare_select_policy_wording_0faeeb61c5.pdf`, p. 5 (authoritative_evidence): Inpatient Care means treatment for which the Insured Person has to stay in a Hospital for more than 24 hours for a covered event.
- `Q002-U2-F1` — `medicare_select_policy_wording_0faeeb61c5.pdf`, p. 4 (authoritative_evidence): Day Care Treatment means medical treatment, and/or Surgical Procedure which is: i. undertaken under General or Local Anesthesia in a Hospital/Day Care Centre in less than 24 hrs because of technological advancement, and ii. which would have otherwise required Hospitalization of more than 24 hours. Treatment normally taken on an out-patient basis is not included in the scope of this definition.

**Reviewer labels:**
- Correctness: ____
- Factual claim support (label each claim): ____
- Citation support (label each claim/citation link): ____
- Q040 abstention appropriateness: ____
- Uncertainty / comments: ____

## Q007
**Question:** What is the initial waiting period for illness and what are its exceptions?

**Generated answer:** Not generated (validation-only dry run).

**Expected answer:** Illness treatment is excluded for the first 30 days from first policy commencement. Covered accident claims are excepted, and the exclusion does not apply after more than 12 months of continuous coverage. The 30-day wait applies afresh to an enhanced Sum Insured.

**Required facts:**
- [ ] Fact 0: The initial illness waiting period is 30 days from first policy commencement. — label: ____
- [ ] Fact 1: Covered accident claims are excepted. — label: ____
- [ ] Fact 2: It does not apply where continuous coverage exceeds 12 months. — label: ____
- [ ] Fact 3: It applies to an enhanced Sum Insured. — label: ____

**Supplied oracle evidence / provenance:**
- `Q007-U1-F1` — `medicare_select_policy_wording_0faeeb61c5.pdf`, p. 22 (authoritative_evidence): Expenses related to the treatment of any Illness within 30 days from the first Policy commencement date shall be excluded except claims arising due to an Accident, provided the same are covered.
- `Q007-U2-F1` — `medicare_select_policy_wording_0faeeb61c5.pdf`, p. 22 (authoritative_evidence): This exclusion shall not, however, apply if the Insured Person has Continuous Coverage for more than twelve months.
- `Q007-U3-F1` — `medicare_select_policy_wording_0faeeb61c5.pdf`, p. 22 (authoritative_evidence): The within referred waiting period is made applicable to the enhanced Sum Insured in the event of granting higher Sum Insured subsequently.

**Reviewer labels:**
- Correctness: ____
- Factual claim support (label each claim): ____
- Citation support (label each claim/citation link): ____
- Q040 abstention appropriateness: ____
- Uncertainty / comments: ____

## Q008
**Question:** If cataract is also a pre-existing disease, which waiting period applies?

**Generated answer:** Not generated (validation-only dry run).

**Expected answer:** Cataract has a 24-month specified-disease waiting period, while a pre-existing disease has a 36-month waiting period. If the cataract is also pre-existing, the longer period applies: 36 months, subject to the policy’s continuity and disclosure terms.

**Required facts:**
- [ ] Fact 0: Cataract is a listed specified condition with a 24-month waiting period. — label: ____
- [ ] Fact 1: The PED waiting period is 36 months. — label: ____
- [ ] Fact 2: The longer waiting period applies when a specified disease is also pre-existing. — label: ____

**Supplied oracle evidence / provenance:**
- `Q008-U1-F1` — `medicare_select_policy_wording_0faeeb61c5.pdf`, p. 20 (authoritative_evidence): Expenses related to the treatment of a Pre-Existing Disease (PED) and its direct complications shall be excluded until the expiry of 36 months of continuous coverage after the date of inception of the first Policy with Us.
- `Q008-U2-F1` — `medicare_select_policy_wording_0faeeb61c5.pdf`, p. 21 (authoritative_evidence): Expenses related to the treatment of the listed conditions, surgeries/treatments shall be excluded until the expiry of 24 months of continuous coverage after the date of inception of the first Policy with Us. This exclusion shall not be applicable for claims arising due to an Accident.
- `Q008-U3-F1` — `medicare_select_policy_wording_0faeeb61c5.pdf`, p. 21 (authoritative_evidence): If any of the specified disease/procedure falls under the waiting period specified for Pre-Existing Diseases, then the longer of the two waiting periods shall apply.
- `Q008-U4-F1` — `medicare_select_policy_wording_0faeeb61c5.pdf`, p. 21 (authoritative_evidence): XVIII. Cataract (avrana Shukla), Retinal detachment, Glaucoma (abhishyandha)

**Reviewer labels:**
- Correctness: ____
- Factual claim support (label each claim): ____
- Citation support (label each claim/citation link): ____
- Q040 abstention appropriateness: ____
- Uncertainty / comments: ____

## Q014
**Question:** Is OPD dental treatment covered despite the general dental exclusion? If so, what treatments qualify?

**Generated answer:** Not generated (validation-only dry run).

**Expected answer:** Yes. After two continuous years, the OPD Dental benefit covers only root canal treatment, tooth extraction, and filling, within the applicable annual limit. The benefit expressly disapplies the general dental exclusion for this coverage.

**Required facts:**
- [ ] Fact 0: Two years of continuous coverage are required. — label: ____
- [ ] Fact 1: Qualifying treatments are root canal, extraction, and filling only. — label: ____
- [ ] Fact 2: The benefit expressly overrides the dental exclusion for this coverage. — label: ____

**Supplied oracle evidence / provenance:**
- `Q014-U1-F1` — `tata_aig_medicare_premier_policy_wordings_781aa2fd94.pdf`, p. 22 (authoritative_evidence): Once the Insured has completed two years of continuous coverage with Us, we will pay for expenses related to the following dental treatments only subject to a maximum of limit specified in the table below, per policy year annually: - Root Canal Treatment (single or multiple sittings) - Tooth extraction(s) - Filling
- `Q014-U2-F1` — `tata_aig_medicare_premier_policy_wordings_781aa2fd94.pdf`, p. 22 (authoritative_evidence): In view of this coverage getting extended, dental exclusion (General Exclusions ii. 1. ix) is not applicable for this particular coverage.
- `Q014-U3-F1` — `tata_aig_medicare_premier_policy_wordings_781aa2fd94.pdf`, p. 38 (authoritative_evidence): Dental treatment or surgery of any kind except as specified in ‘Inpatient Treatment – Dental’.

**Reviewer labels:**
- Correctness: ____
- Factual claim support (label each claim): ____
- Citation support (label each claim/citation link): ____
- Q040 abstention appropriateness: ____
- Uncertainty / comments: ____

## Q017
**Question:** What is the Emergency Air Ambulance limit?

**Generated answer:** Not generated (validation-only dry run).

**Expected answer:** For Sum Insured up to ₹50 lakh, the limit is ₹5 lakh. For ₹75 lakh to ₹3 crore, it is ₹5 lakh for a non-network provider and up to the Sum Insured for a network provider. The benefit requires an accepted B1 inpatient claim.

**Required facts:**
- [ ] Fact 0: Up to ₹50 lakh Sum Insured: ₹5 lakh limit. — label: ____
- [ ] Fact 1: ₹75 lakh–₹3 crore: ₹5 lakh non-network limit. — label: ____
- [ ] Fact 2: ₹75 lakh–₹3 crore: up to Sum Insured for a network provider. — label: ____
- [ ] Fact 3: An accepted B1 inpatient claim is required. — label: ____

**Supplied oracle evidence / provenance:**
- `Q017-U1-F1` — `tata_aig_medicare_premier_policy_wordings_781aa2fd94.pdf`, p. 22 (authoritative_evidence): We will pay for ambulance transportation of the Insured Person in an airplane or helicopter subject to maximum of limit specified in the table below, for emergency life threatening health conditions which require immediate and rapid ambulance transportation to the hospital/medical centre for further medical management.
- `Q017-U2-F1` — `tata_aig_medicare_premier_policy_wordings_781aa2fd94.pdf`, p. 23 (authoritative_evidence): This benefit shall only be payable if We have accepted an inpatient Hospitalization claim for the Insured member under section B1 of this policy. Basic Sum Insured Limit Up to Rs.50 Lacs Up to Rs. 500,000 Rs.75 Lacs to Rs. 3 Crore Up to Rs. 500,000 for Non Network; Upto Sum Insured for Network Provider

**Reviewer labels:**
- Correctness: ____
- Factual claim support (label each claim): ____
- Citation support (label each claim/citation link): ____
- Q040 abstention appropriateness: ____
- Uncertainty / comments: ____

## Q022
**Question:** When can the Aggregate Deductible be waived?

**Generated answer:** Not generated (validation-only dry run).

**Expected answer:** It may be waived at renewal after five continuous Policy Years under this policy with the insurer, including Grace Period, on payment of applicable premium; no underwriting is required up to the inception Sum Insured. Portability or migration credit does not count toward those five years, and after porting the five continuous years must be completed under this policy.

**Required facts:**
- [ ] Fact 0: Waiver is available at renewal after five continuous Policy Years under this policy, including Grace Period. — label: ____
- [ ] Fact 1: Applicable premium must be paid. — label: ____
- [ ] Fact 2: No underwriting is required up to the inception Sum Insured. — label: ____
- [ ] Fact 3: Portability/migration credit is not counted; a ported policy must complete five years under this policy. — label: ____

**Supplied oracle evidence / provenance:**
- `Q022-U1-F1` — `tata_aig_medicare_reserve_policy_wordings_2250e6352a.pdf`, p. 15 (authoritative_evidence): The Insured Person will have the option to waive off Aggregate Deductible on Renewal, upon completion of five continuous Policy Years under this policy with Us, including Grace Period, on payment of applicable premium. The Policy shall not require underwriting at the time of availing this option, up to the Sum Insured as opted by the Insured Person at inception.
- `Q022-U2-F1` — `tata_aig_medicare_reserve_policy_wordings_2250e6352a.pdf`, p. 11 (authoritative_evidence): After completion of five continuous years of coverage under this Policy with Us and payment of applicable premium, the Policyholder will have the option to opt for waiver of the Aggregate Deductible on subsequent renewal(s). Please note that no credit for portability/migration shall be considered while calculating the five continuous Policy Years of coverage.
- `Q022-U3-F1` — `tata_aig_medicare_reserve_policy_wordings_2250e6352a.pdf`, p. 28 (authoritative_evidence): However, after porting into this product, the option of Waiver of Aggregate Deductible under benefit B11 will be available after completion of 5 continuous years under this Policy.

**Reviewer labels:**
- Correctness: ____
- Factual claim support (label each claim): ____
- Citation support (label each claim/citation link): ____
- Q040 abstention appropriateness: ____
- Uncertainty / comments: ____

## Q034
**Question:** If the insured has multiple health policies, can they choose which policy to claim under?

**Generated answer:** Not generated (validation-only dry run).

**Expected answer:** Yes. The insured may require settlement under any chosen policy, and that insurer must settle within that policy’s limits and terms. If a claimed amount exceeds one policy’s Sum Insured, the insured may choose another insurer for the balance; total indemnity remains subject to the chosen policy terms.

**Required facts:**
- [ ] Fact 0: The insured may select which indemnity policy settles the claim. — label: ____
- [ ] Fact 1: The selected insurer settles only within its policy limits and terms. — label: ____
- [ ] Fact 2: The insured may choose an insurer for a balance exceeding one policy’s Sum Insured. — label: ____

**Supplied oracle evidence / provenance:**
- `Q034-U1-F1` — `Tata_AIG_Medi_Care_Plus_e8a0cf5358.pdf`, p. 14 (authoritative_evidence): In case of multiple policies taken by an insured person during a period from one or more insurers to indemnify
- `Q034-U1-F2` — `Tata_AIG_Medi_Care_Plus_e8a0cf5358.pdf`, p. 15 (authoritative_evidence): treatment costs, the insured person shall have the right to require a settlement of his/her claim in terms of any of his/her policies. In all such cases the insurer chosen by the insured person shall be obliged to settle the claim as long as the claim is within the limits of and according to the terms of the chosen policy.
- `Q034-U2-F1` — `Tata_AIG_Medi_Care_Plus_e8a0cf5358.pdf`, p. 15 (authoritative_evidence): If the amount to be claimed exceeds the Sum Insured under a single Policy, the Insured Person shall have the right to choose Insurer from whom he/she wants to claim the balance amount and we will assist the insured person in facilitating the same.

**Reviewer labels:**
- Correctness: ____
- Factual claim support (label each claim): ____
- Citation support (label each claim/citation link): ____
- Q040 abstention appropriateness: ____
- Uncertainty / comments: ____

## Q038
**Question:** When does the Health Checkup benefit become available and what is its limit?

**Generated answer:** Not generated (validation-only dry run).

**Expected answer:** The benefit is payable once after every block of two continuous claim-free policy years. Its limit is 1% of the previous Sum Insured, capped at ₹10,000 per policy; this is a policy-wide maximum usable by more than one insured.

**Required facts:**
- [ ] Fact 0: Requires a block of two continuous claim-free policy years. — label: ____
- [ ] Fact 1: Limit is 1% of previous Sum Insured. — label: ____
- [ ] Fact 2: Maximum is ₹10,000 per policy and can be shared among insured persons. — label: ____

**Supplied oracle evidence / provenance:**
- `Q038-U1-F1` — `Tata_AIG_Medi_Care_Plus_e8a0cf5358.pdf`, p. 8 (authoritative_evidence): We will cover for expenses for a Preventive Health Check-up upto 1 % of previous sum insured subject to a maximum of Rs. 10,000/- per policy. The limit is the maximum per policy and more than one insured can utilize the amount.
- `Q038-U2-F1` — `Tata_AIG_Medi_Care_Plus_e8a0cf5358.pdf`, p. 8 (authoritative_evidence): The benefit is payable once after block of every two continuous claim free policy years with us.

**Reviewer labels:**
- Correctness: ____
- Factual claim support (label each claim): ____
- Citation support (label each claim/citation link): ____
- Q040 abstention appropriateness: ____
- Uncertainty / comments: ____

## Q040
**Question:** Does the policy wording establish that a mid-year change from NRI to resident automatically terminates coverage?

**Generated answer:** Not generated (validation-only dry run).

**Expected answer:** The policy wording does not provide sufficient evidence to conclude that a mid-year change from NRI to resident automatically terminates coverage. The cited cancellation and entire-contract clauses do not address that residency-status scenario and cannot establish a document-wide absence. The correct response is to abstain from asserting automatic termination.

**Required facts:**
- [ ] Fact 0: There is insufficient policy evidence to conclude that an NRI-to-resident change automatically terminates coverage. — label: ____
- [ ] Fact 1: The cited cancellation and entire-contract clauses do not address the residency-status scenario and do not prove document-wide absence. — label: ____
- [ ] Fact 2: The answer must abstain from asserting an unsupported automatic-termination rule. — label: ____

**Supplied oracle evidence / provenance:**
- `Q040-NEARBY-1` — `Tata_AIG_Medi_Care_Plus_e8a0cf5358.pdf`, p. 15 (nearby_clause_not_positive_evidence): The Company may cancel the policy at any time on grounds of established fraud, misrepresentation or non-disclosure of material facts by the Policyholder/Insured Person by giving 15 days’ written notice.
- `Q040-NEARBY-2` — `Tata_AIG_Medi_Care_Plus_e8a0cf5358.pdf`, p. 18 (nearby_clause_not_positive_evidence): This Policy, its Schedule, endorsement(s), proposal constitutes the entire contract of insurance. No change in this policy shall be valid unless approved by Us and such approval be endorsed hereon.

**Reviewer labels:**
- Correctness: ____
- Factual claim support (label each claim): ____
- Citation support (label each claim/citation link): ____
- Q040 abstention appropriateness: ____
- Uncertainty / comments: ____
