# Stage 1 Problem Definition

## Status and evidence boundaries

This document proposes the initial product boundary for review; it is not a statement that the product or its capabilities already exist. The repository currently describes the project only as an evaluation-driven health-insurance policy intelligence platform and defines a staged architecture in `AGENTS.md`. It contains no policy corpus, user research, production data, or measured baseline. Consequently:

- **Repository-supported facts:** the domain is health-insurance policy intelligence; Stage 1 is intended to be vector retrieval followed by an LLM; evaluation should cover retrieval, answers, citations, latency, tokens, and cost.
- **Assumptions to validate:** users need help locating and understanding provisions in policy documents; the first corpus will be approved, versioned policy documents; document text and stable section/page locators can be extracted.
- **Proposed design choices:** the target user, use cases, answer contract, and scope below. Human review and user research may change them.

## Target user

The proposed primary user is a person who must inspect a health-insurance policy document and wants a faster, evidence-linked explanation: initially, an internal policy, operations, customer-support, or quality professional familiar with insurance terminology. This is deliberately narrower than serving a member making an urgent coverage decision. Internal expert users can identify unsafe interpretations while the evidence and evaluation process mature.

Possible later users include brokers, employers, clinicians, and policyholders. Their needs, permissions, vocabulary, accessibility requirements, and risk tolerances differ and require separate research rather than being assumed equivalent.

## Core user problem

Long policy documents distribute important provisions across definitions, benefits, exclusions, schedules, endorsements, and conditions. A user needs to find the passages relevant to a question and understand what those passages say without losing qualifications, exceptions, scope, or document provenance. Search alone may return a passage without synthesizing it; unconstrained generation may sound helpful while adding unsupported claims.

Stage 1 should therefore answer document-grounded questions with traceable evidence, state material qualifications, and abstain or redirect when the supplied policy evidence cannot support an answer.

## Initial use cases

Proposed Stage 1 use cases are:

1. Locate and explain a stated definition, benefit, exclusion, eligibility condition, waiting period, limit, or sub-limit.
2. Summarize a provision while retaining exceptions and cross-references.
3. Compare or combine a small number of passages **within the same identified policy version** when the answer requires multi-section reasoning.
4. Answer negation-sensitive questions such as whether a document explicitly excludes a service.
5. Identify an effective date or other temporal condition stated in the document, without calculating customer-specific eligibility.
6. Say that the document does not establish the requested fact, or that available evidence is insufficient.

These use cases describe candidate capabilities, not validated demand.

## What policy documents can and cannot reasonably answer

### Reasonably document-grounded

Provided the relevant approved document and version are available, questions about explicit policy language can reasonably be answered from documents: definitions; described benefits; general exclusions; stated eligibility rules; waiting-period language; limits and sub-limits; claim-notification requirements; effective or revision dates; and relationships among explicit clauses. An answer can report what the document says, but should not imply that the clause has been applied to a real person or claim.

### Requires more than unstructured policy retrieval

| Question class | Additional source or capability required | Stage 1 response |
| --- | --- | --- |
| “How much of my annual limit remains?” | Customer-specific claims and accumulator data | Explain any general policy limit only; say remaining balance cannot be determined. |
| “Am I covered?” or “Will this claim be paid?” | Enrollment, plan selection, dates, clinical/coding facts, claim state, endorsements, and deterministic adjudication rules | Do not make a coverage determination; identify relevant general clauses and missing inputs. |
| “What will I pay?” | Benefit configuration, network/provider data, negotiated prices, accumulators, and cost-sharing rules | Do not estimate from policy prose alone. |
| “Has the waiting period elapsed for me?” | Customer effective date, event dates, and deterministic date calculations | State the documented rule; do not calculate an individual result. |
| “Which plan is cheapest/best?” | Current product catalog, premiums, needs/preferences, and possibly regulated advice controls | Out of scope. |
| “Is this treatment medically necessary?” | Clinical evidence, clinical policy, and qualified review | Out of scope. |
| “What does current law require?” | Current jurisdiction-specific external legal/regulatory sources and legal review | Out of scope; do not treat policy wording as current law. |
| “Which nearby hospital is in network?” | Current provider directory or network API | Out of scope for document-only retrieval. |

Structured tables embedded in a document may also require reliable table extraction or a structured representation. Deterministic calculations and rule application should not be delegated to free-form generation merely because the inputs appear in the document.

## Non-goals for Stage 1

- Claim adjudication, prior-authorization decisions, medical-necessity decisions, legal advice, or guarantees of coverage or payment.
- Personalized answers using member, patient, employer, provider, or claims data.
- Live premiums, provider-network status, law, clinical guidance, or other external/current facts.
- Cross-product recommendations or automatic comparison unless a separately curated evaluation justifies it.
- Autonomous actions, agentic workflows, reranking, knowledge graphs, deterministic rules engines, or structured-data integration.
- Supporting every file format, language, jurisdiction, or inaccessible scanned document at launch.
- Treating fluent output, user satisfaction, or one successful demonstration as proof of correctness.

## Successful-answer contract

A successful answer should:

1. Directly address the question at an appropriate level of detail.
2. Use only claims supported by retrieved passages from the correct policy and version.
3. Preserve material conditions, exceptions, exclusions, time qualifiers, and defined terms.
4. Cite each material claim with a resolvable document and section/page locator, enabling a reviewer to inspect the evidence.
5. Clearly separate quoted or paraphrased policy content from interpretation.
6. State uncertainty, conflicting provisions, missing cross-references, or insufficient evidence rather than fill gaps.
7. Identify when customer data, structured data, deterministic rules, professional judgment, or external information is required.
8. Avoid a personalized coverage promise and, where appropriate, advise confirmation through the authoritative process.

## Insurance-specific failure modes

- **Policy/version mismatch:** using a similar product, obsolete edition, wrong jurisdiction, schedule, or endorsement.
- **Hierarchy failure:** ignoring that a schedule or endorsement changes the base wording.
- **Qualification loss:** omitting “subject to,” exceptions, preconditions, or cross-referenced definitions.
- **Negation reversal:** turning an exclusion into coverage, or missing an exception to an exclusion.
- **Limit distortion:** confusing per-service, per-year, per-person, family, lifetime, aggregate, and sub-limits.
- **Temporal error:** confusing publication, effective, enrollment, treatment, diagnosis, claim, or waiting-period dates.
- **Entity/scope confusion:** applying one benefit, provider type, dependent class, network, or territory to another.
- **Definition drift:** applying an everyday meaning rather than the policy's defined term.
- **False absence:** asserting that a benefit or exclusion does not exist because retrieval failed.
- **Unsafe synthesis:** combining individually accurate passages into a conclusion the policy does not support.
- **Citation mismatch:** citing a real passage that does not entail the answer, or citing an unstable locator.
- **Personalization leakage:** inferring eligibility or claim outcome without the necessary member and claim facts.
- **Document-instruction injection:** following malicious text embedded in an untrusted document rather than treating it solely as content.

## Why hallucination is especially problematic

Health-insurance answers may affect whether a person seeks care, anticipates a large expense, submits a claim, appeals a decision, or meets a deadline. A fabricated benefit, missing exclusion, altered limit, or invented authorization requirement can cause financial harm, delayed care, avoidable distress, and operational or regulatory risk. The authoritative result may also depend on a policy version, endorsement, personal enrollment facts, or adjudication rules unavailable to Stage 1. Fluent uncertainty is therefore not benign: abstention with an explanation is preferable to an unsupported conclusion, and citation presence alone is insufficient unless the cited text actually supports the claim.

## Open product questions

- Which user segment and decision context should be evaluated first?
- Which document types, jurisdictions, languages, and policy hierarchies form the initial corpus?
- What is the authoritative precedence among base policy, schedule, endorsement, and later amendment?
- Which answer classes require mandatory human review or a stronger disclaimer?
- What citation granularity and locator remain stable through ingestion?
- How should ambiguous, contradictory, superseded, or absent provisions be labeled?
- What privacy and retention controls will apply if customer-specific use is later introduced?
