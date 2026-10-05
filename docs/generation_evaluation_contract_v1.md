# Generation Evaluation Contract v1

## Decision and scope

Retrieval evaluation establishes whether evidence is available; it does not show
whether a model reaches the right conclusion, preserves exceptions, stays within
the supplied evidence, or cites the evidence it used. Generation must therefore
be measured separately before it is added to the product.

This contract is the smallest auditable measurement layer for a future controlled
generation experiment. It does **not** select or call a model, create answers,
alter the gold dataset or Evaluation Contract v2, or change the accepted Stage 2B
retrieval path. The machine-readable contract references those sources rather
than copying their expected answers, facts, or evidence text.

## Controlled arms

Both arms must use the same model identifier, prompt version, answer schema, and
evaluator version. A run that changes one of these controls is not a paired test.

1. **Oracle context:** question → authoritative gold evidence → future LLM →
   answer. For each positive question, context must reference every required
   Evaluation Contract v2 evidence unit. This isolates generation capability when
   evidence availability is guaranteed.
2. **Stage 2B end-to-end:** question → frozen Voyage-4 Top-30 → Voyage rerank-3
   Top-10 → future LLM → answer. This measures the complete accepted RAG path.

Every context item records source file/page and, where applicable, chunk, rank,
and evidence-unit IDs. Evidence passages need not be duplicated. The two arms
remain explicit in every result record and in per-arm metrics; paired diagnostics
retain both original records.

## Dimensions and review boundary

| Dimension | Rule | Method |
|---|---|---|
| Correctness | Does the answer reach the correct policy conclusion? | Human review against the existing expected answer. `correct`, `incorrect`, or `uncertain`; fluency is not evidence. |
| Completeness | Are all material conditions, limits, exceptions, qualifiers, and overrides present? | Human marks every existing gold required fact `present`, `absent`, `contradicted`, or `uncertain`; code derives complete only when all are present. |
| Faithfulness | Is every factual policy claim supported by context actually supplied to this arm? | Human atomizes and labels claims `supported`, `unsupported`, or `uncertain`; model prior knowledge is not context. |
| Citation existence | Was a citation emitted and linked to a claim? | Deterministic schema/ID check. |
| Citation resolution | Does its source/page occur in both supplied context and authoritative evidence? | Deterministic exact source/page check. |
| Citation support | Does the resolved passage actually support its associated claim? | Human review. A decorative citation fails. |
| Abstention | On Q040, does the answer communicate insufficient evidence without asserting automatic termination? | Separate human-reviewed negative-space protocol. |

Semantic equivalence, contradiction, and entailment are intentionally not guessed
with keyword heuristics. Wrong numbers and missing negation are correctness and/or
fact-coverage failures when a reviewer labels them so. The evaluator then checks
coverage, references, invariants, and aggregation deterministically.

### Q040 negative-space protocol

Q040 remains outside positive correctness, completeness, and required-fact
coverage denominators. Nearby cancellation and entire-contract clauses do not
prove a document-wide absence and must not be treated as ordinary positive gold
evidence. A successful answer says that the supplied authoritative wording is
insufficient to establish automatic termination and does not invent that rule.
An assertion that coverage automatically terminates is an abstention failure and
an unsupported inference. Abstention correctness is reported separately.

## Output, metrics, and denominators

`evals/generation_experiment_output_v1.schema.json` defines the future run
record. `src/evaluation/generation_contract_v1.py` validates records against the
existing gold and evidence contracts and derives the following metrics **per
arm**, never as a composite score:

| Metric | Numerator | Denominator |
|---|---|---|
| Answer Correctness rate | completed positive questions labelled correct | completed positive questions |
| Complete Answer rate | completed positive questions with every required fact present | completed positive questions |
| Required Fact Coverage | required facts labelled present | all required facts on completed positive questions |
| Faithfulness / Grounded Claim rate | factual claims labelled supported by supplied context | all reviewed factual policy claims |
| Citation Resolution rate | emitted citations whose source/page is in supplied context and authoritative evidence | all emitted citations |
| Citation Support rate | resolved citations labelled supporting their associated claims | all resolved citations |
| Abstention accuracy | completed negative-space cases labelled appropriate with no unsupported-rule assertion | completed negative-space cases |
| latency/query | sum of recorded latency | all attempted records |
| input/output/total tokens per query | corresponding token sum | all attempted records |
| estimated cost/query | sum of estimated cost | all attempted records |
| experiment total estimated cost | sum of estimated cost | not a rate |
| execution failures | records with a non-null failure | all attempted records |

Zero denominators yield `null`, not a fabricated zero. Estimated cost is not an
invoice. Failed attempts remain in operational denominators and the failure count
but not semantic-quality denominators. Evaluation uncertainty is separately
counted whenever a human annotation is uncertain.

## Failure attribution

Question-level paired output applies transparent diagnostic labels while keeping
the component observations:

- Oracle correct, end-to-end incorrect, required evidence absent →
  `retrieval_context_contribution`.
- Evidence present, answer incorrect → `generation_failure`.
- Oracle and end-to-end both incorrect →
  `generation_prompt_model_or_contract_issue` (a review queue, not proof of one
  cause).
- Evidence absent but answer correct → `unsupported_prior_knowledge_risk`; claim
  review determines whether there is also a grounding failure.
- Any correct answer with an unsupported factual claim still receives a separate
  `grounding_failure` label.
- Any unresolved or non-supporting citation receives a separate
  `citation_failure` label.
- An inappropriate Q040 response receives `abstention_failure`.
- Missing arm pairs or uncertain judgments remain evaluation uncertainty rather
  than being forced into a causal category.

These are diagnostic contributions, not causal proof. In particular, retrieval
absence can explain an answer failure but cannot prove the generator would have
succeeded with the missing evidence.

## Evaluator calibration and future evolution

The evaluator is a measurement instrument and must itself be validated. Before a
full experiment, two human reviewers should independently review a small,
stratified calibration set containing both arms, easy and hard questions,
multi-fact answers, numerical/negation cases, unsupported claims, citation
failures, and Q040. Resolve disagreements with the human architect; verify that
the deterministic derivations match the adjudicated labels; record agreement and
all rubric ambiguities. Do not report model comparisons until calibration passes
a threshold chosen by the owner in advance.

No LLM judge is introduced because this dataset is small, material semantic
judgments require policy interpretation, and an unvalidated judge would merely
replace visible human uncertainty with opaque scoring error. Evidence that could
justify a later evaluator includes: a much larger run volume, measured human
review cost/latency, a stable adjudicated calibration set, and candidate judge
performance measured per dimension (including numeric, negation, exception,
grounding, citation, and abstention slices) with acceptably low false-pass rates.
Any judge would remain versioned, calibrated, and auditable rather than silently
becoming source truth.

## Assumptions and open questions

- Future answer formatting must make claim-to-citation association reviewable.
- Human claim atomization guidance and the calibration acceptance threshold are
  intentionally left for owner approval before execution.
- Pricing and tokenizer rules belong to the future selected-model experiment;
  no model is selected here.
- Stage 2B per-question Top-10 context artifacts must be available before the
  end-to-end arm runs; aggregate retrieval results are not enough to reconstruct
  them.
- No API was called and incremental API cost for this contract task is **$0**.
