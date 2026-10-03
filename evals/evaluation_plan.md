# Stage 1 Evaluation Plan

## Purpose and current status

This is a **proposed baseline methodology**. The repository now has four authoritative policy-wording PDFs, a completed extraction baseline, and gold-dataset infrastructure, but it does not yet have the real reviewed benchmark, user-study results, or a measured RAG baseline. No performance target is set here: thresholds should follow annotation, baseline runs, risk analysis, and human review rather than invented expectations.

Repository-supported constraints are the staged architecture and evaluation-first principles in `AGENTS.md`. The metric definitions, workflow, taxonomy, and rubric below are design proposals. Assumptions are that the future corpus is approved and versioned, passages have stable identifiers, and qualified reviewers can adjudicate labels.

## Evaluation questions

The first evaluation should isolate three questions:

1. **Retrieval:** did the system surface sufficient evidence from the correct document/version?
2. **Generation given evidence:** did the answer correctly and faithfully use the supplied evidence?
3. **End to end:** did the complete system produce a useful, supported, properly scoped answer within observable latency and cost?

Separating these layers prevents a good generator from hiding retrieval failures and prevents retrieval failures from being misdiagnosed as generation failures.

## Initial question taxonomy

The schema uses one primary, interpretable type: `definition`,
`coverage_benefit`, `exclusion`, `waiting_period`, `limit_sublimit`,
`condition_eligibility`, `claims_procedure`, or `cross_section`.
Definitions and annotation guidance live in `docs/gold_dataset_annotation.md`.
Revise this small taxonomy only if annotation disagreements or real-query
research demonstrate a missing or overlapping class.

## Dataset construction and governance

1. Select only authorized, non-customer policy documents and record immutable document/version identifiers.
2. Annotate exact evidence against stable PDF filenames and one-based pages before defining experimental chunks.
3. Sample questions across the provisional taxonomy, including answerable, ambiguous, conflicting, and questions unsupported by the Stage 1 architecture. Avoid constructing every question directly from an isolated chunk, which would make retrieval unrealistically easy.
4. Have a domain-qualified annotator record the expected answer, all minimally sufficient evidence sets, acceptable variants, material caveats, and why an item is unanswerable from the corpus or unsupported by Stage 1.
5. Independently review high-risk or ambiguous labels; record disagreement and adjudication rather than silently forcing consensus.
6. Separate development and held-out test sets. Group near-duplicates and, where feasible, document families/versions to reduce leakage.
7. Version the dataset, corpus, chunking configuration, prompts, model/API version, and scoring code. Freeze the held-out set before comparative experiments.
8. Do not place personal health information, customer records, credentials, or proprietary documents in the repository.

The records in `gold_dataset.examples.json` demonstrate the schema only. Although their quotations come from the authoritative corpus, they are not reviewed benchmark items and must not be scored.

## Retrieval evaluation

Evaluate retrieval without generation against passage-level relevance judgments. Because multiple passage combinations may support an answer, labels should allow multiple acceptable evidence sets rather than one privileged chunk. Report aggregate and per-slice results for several recorded values of K, without selecting a target until a baseline exists.

### Recall@K

For a question with one or more annotated minimally sufficient evidence sets, define success at K when the top K contains every passage in at least one such set. Dataset Recall@K is the fraction of questions that succeed. Optionally also report **evidence-item recall@K** (relevant retrieved passages divided by annotated relevant passages), clearly named so it is not confused with question-level sufficiency.

**Tells us:** whether the retriever gives the generator an opportunity to answer, and how that opportunity changes with K.

**Does not tell us:** whether evidence ranks early within K; how much distracting/contradictory context was returned; whether annotations are complete; whether the generator uses the evidence; or whether the final answer is correct. Recall may be underestimated when valid evidence was never labeled.

### Ranking quality and MRR

For questions where the first relevant passage is meaningful, reciprocal rank is `1 / rank` of the first relevant result (zero if none within the evaluated depth); Mean Reciprocal Rank (MRR) averages it across questions.

**Tells us:** how quickly a user or generator encounters the first relevant result. It is useful for direct lookups and ranking comparisons.

**Does not tell us:** whether all passages required for a multi-section answer were retrieved, whether the first relevant passage is sufficient, or whether later irrelevant passages add risk. MRR can reward a single early passage even when the answer needs several. For graded relevance, consider NDCG later, but only after a defensible grading scheme exists.

### Supporting diagnostics

Record precision@K or judged relevance distribution, source/version correctness, evidence-set completeness, and failure categories (wrong version, missed table, cross-reference, lexical mismatch, negation, or chunk boundary). These diagnostics provide explanations; they are not interchangeable with end-to-end quality.

## Generation evaluation

First evaluate generation in an **oracle-context** condition using the gold evidence. Then evaluate with retrieved context. The difference estimates the contribution of retrieval, though prompt/context distribution differences mean it is not a perfect causal decomposition.

Use a claim-level rubric with domain-qualified human review for consequential judgments. Automated exact-match, semantic, or LLM-based grading may assist at scale only after calibration against human labels; record grader model, prompt, version, and disagreement.

### Answer correctness

Score whether the answer reaches the expected conclusion and includes required qualifications. A proposed ordinal rubric is: fully correct; mostly correct with no material error; materially incomplete/incorrect; wholly incorrect. Add explicit labels for appropriate abstention and inappropriate refusal.

**Tells us:** alignment with the adjudicated expected answer, including completeness and material conditions.

**Does not tell us:** whether the answer was derived from supplied evidence, whether citations support it, whether the reference itself is complete, or whether the answer generalizes beyond the dataset.

### Faithfulness / groundedness

Split the answer into externally verifiable claims and label each as entailed, contradicted, or not supported by the supplied context. Report supported-claim rate and separately report whether **any material unsupported or contradicted claim** occurs. Do not penalize clearly marked uncertainty or conversational connective text as factual claims.

**Tells us:** whether answer claims remain within the provided evidence and reveals hallucination or unsafe synthesis.

**Does not tell us:** whether retrieved evidence is authoritative, current, complete, from the correct version, or sufficient to answer the user's actual question. A faithful answer can faithfully repeat a wrong document.

### Citation accuracy

Evaluate at least three components:

1. **Validity:** the cited locator resolves to the claimed document/version and passage.
2. **Entailment:** the passage supports the associated claim.
3. **Completeness:** every material evidence-dependent claim has at least one supporting citation.

Report component results rather than only a composite. Citation correctness should be checked at claim level, including whether citations attach to the right claim.

**Tells us:** whether users can audit claims and whether citations are correctly attached and supportive.

**Does not tell us:** whether uncited omissions matter, the policy is authoritative, all qualifications were retrieved, or the overall answer is correct. Merely emitting a citation is not success.

### Answer-contract checks

Label preservation of exceptions/negation/limits/dates; correct distinction between general policy language and personal determination; appropriate uncertainty; clarity; and avoidance of unsupported next steps. Safety-critical errors should remain visible individually rather than disappearing into an average score.

## End-to-end evaluation

Run the frozen questions through the complete Stage 1 pipeline. Preserve retrieved passage IDs/scores/order, final prompt or reproducible prompt identifier, output, citations, timings, model/API version, token usage, errors, and run configuration. Blind reviewers to experiment variant where practical.

Report retrieval sufficiency alongside answer correctness, groundedness, citation validity/entailment/completeness, answer-contract labels, and appropriate abstention. Produce a joint error matrix, for example:

- sufficient retrieval + good answer;
- sufficient retrieval + generation failure;
- insufficient retrieval + appropriate abstention;
- insufficient retrieval + unsupported answer;
- wrong document/version + answer appears plausible.

This is more actionable than one aggregate “quality” score. Report macro results and taxonomy slices with sample counts and uncertainty intervals when the dataset is large enough; do not over-interpret ten illustrative records.

## Operational metrics

### Latency

Measure wall-clock end-to-end latency and separately instrument retrieval and generation. Report distributions (median and tail percentiles), not only an average; record cold/warm state, concurrency, retries, timeouts, region, and document-index version.

**Tells us:** observed responsiveness and which stage dominates under the tested conditions.

**Does not tell us:** answer quality, user-perceived usefulness, scalability outside the tested load, or future provider performance.

### Token consumption

Record input and output tokens per query, and when available separate system/prompt, retrieved-context, and completion contributions. Summarize distributions by question type and K.

**Tells us:** a main driver of model cost and context size, and whether certain designs are verbose or context-heavy.

**Does not tell us:** monetary cost without the applicable price and non-token charges; latency; quality; cached-token treatment; or compute used by retrieval and ingestion.

### Cost per experiment

For each run, calculate actual or estimated variable cost from timestamped provider price/version data and measured usage: model input/output (and cached usage where applicable), embedding/index/query services, automated graders, and other metered infrastructure. Also report number of questions, repetitions, failures/retries, and cost per successfully evaluated item. Keep one-time ingestion cost and human annotation/review time as separate line items rather than hiding them.

**Tells us:** the reproducible marginal spend for a defined experiment and supports comparison of variants.

**Does not tell us:** production unit economics, fixed engineering/operations costs, or value delivered. Estimates can drift when pricing changes.

### Eventual cost per query

In a production-like test, calculate metered online retrieval plus generation and allocated variable infrastructure per attempted query, with retries/cache hits and failures visible. Report distributions and segment by question type; state whether one-time ingestion, storage, monitoring, support, human review, and fixed capacity are included or excluded.

**Tells us:** estimated serving cost under explicit workload and accounting assumptions.

**Does not tell us:** total cost of ownership, future scale discounts, unpredictable review/escalation costs, or whether the answer is worth its cost.

## Baseline experiment sequence

1. **Corpus/annotation pilot:** select a small approved corpus, test extraction and locators, and double-annotate a diverse sample.
2. **Retrieval baseline:** freeze chunking and run a minimal vector-retrieval configuration; measure Recall@K, MRR where appropriate, latency, and failure slices.
3. **Oracle-context generation baseline:** measure whether generation succeeds when retrieval is not the bottleneck.
4. **End-to-end baseline:** combine the same retriever and generator, assess claims/citations/abstention, and capture operational metrics.
5. **Error review:** prioritize the largest consequential, repeated failure supported by evidence. Change one controlled variable at a time before considering architectural expansion.

Use deterministic settings where supported, record random seeds where relevant, and repeat stochastic generation enough to expose instability. The number of repetitions should be selected after observing variance and cost, not asserted now.

## Risks and limitations of the methodology

- Annotation may encode reviewer interpretation, miss alternative evidence, or become stale when documents change.
- A synthetic, small, or taxonomy-balanced set may not represent real user traffic or rare high-severity cases.
- Passage labels depend on chunk boundaries, making retrieval comparisons unfair if identifiers change without relabeling.
- LLM graders can share biases with the evaluated system and may accept plausible insurance language; human calibration is required.
- Aggregate metrics can hide a catastrophic negation, version, or limit error.
- Oracle context can overstate real performance; end-to-end scores can obscure root cause.
- Latency and price measurements are environment- and time-dependent.
- Test-set exposure through prompt tuning or repeated inspection can invalidate held-out results.
- Offline correctness does not establish usability, accessibility, trust, or impact on real decisions.

## Unresolved decisions before a scored benchmark

- Authoritative corpus, document hierarchy, permissible use, and versioning rules.
- Primary user and real decision contexts from which questions should be sampled.
- Passage/chunk relevance unit and handling of tables, footnotes, and cross-references.
- Qualified annotator roles, adjudication process, and treatment of legitimate ambiguity.
- Answer and abstention rubric thresholds appropriate to risk.
- Which errors require zero tolerance or mandatory human escalation.
- Evaluation storage, privacy, retention, and access controls.

## Recommended next experiment

Conduct a corpus-and-annotation feasibility pilot before building RAG: choose a few authorized, representative policy documents; verify extractability and stable locators; draft a small set of real document-grounded questions across the taxonomy; and have two qualified reviewers independently annotate evidence and answerability. Measure agreement, adjudicate disagreements, and revise the schema/taxonomy. This experiment tests whether trustworthy ground truth can be produced and reveals document-structure risks without adding retrieval or generation cost.
