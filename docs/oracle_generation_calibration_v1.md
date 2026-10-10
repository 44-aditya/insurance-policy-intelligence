# Oracle-context generation calibration v1

## Purpose and scope

This is the smallest calibration of Generation Evaluation Contract v1. It asks
whether GPT-5.4 can answer a deliberately varied set of existing benchmark
questions when authoritative evidence is guaranteed, and whether humans can
apply the contract consistently. It is **not** a model benchmark, a Stage 2B
retrieval run, or an end-to-end RAG experiment. It does not alter gold truth,
Evaluation Contract v2, or Generation Evaluation Contract v1.

The experiment has one arm, `oracle_context`. The frozen controls are OpenAI
`gpt-5.4`, reasoning effort `low`, default (standard) service tier,
`oracle-policy-qa-v1`, answer schema `generation-answer-v1`, and evaluator
`generation-v1`. The Responses API request supplies no tools (`tools=[]`) and
uses strict JSON Schema output. It does not enable web search, file search,
browsing, agents, or another external knowledge source.

The OpenAI Python SDK is a required project dependency because the installed
`run-oracle-generation-calibration` entry point imports it for live execution.
Installing the project therefore installs the supported `openai>=2,<3` range;
no separate, undocumented SDK installation is required.

## Fixed calibration set

Selection is deliberate and versioned in
`configs/oracle_generation_calibration_v1.json`; it is never sampled.

| ID | Inclusion rationale |
|---|---|
| Q001 | Easy single-fact definition control. |
| Q002 | Multi-unit duration rule contrasting inpatient and under-24-hour day care. |
| Q007 | Waiting-period rule with accident, continuity, and enhanced-sum-insured qualifications. |
| Q008 | Difficult multi-page interaction between two waits and the longer-period override. |
| Q014 | Specific coverage that expressly overrides a general exclusion. |
| Q017 | Numerical, branched table answer with network status and claim-admission condition. |
| Q022 | Multi-fact eligibility answer assembled from three separated policy locations. |
| Q034 | Known cross-page and fragmented MediCare Plus evidence representation case. |
| Q038 | Known MediCare Plus extraction-representation difficulty with competing temporal and numerical clauses. |
| Q040 | Required negative-space probe: abstention versus an unsupported automatic-termination inference. |

## Deterministic context and prompt construction

For Q001–Q039 selected above, the harness traverses Evaluation Contract v2
evidence units and supplies every source fragment verbatim, in contract order.
Each fragment receives a stable identifier such as `Q008-U3-F1`, together with
source file, page, unit membership, role, and text. Before any client is created,
the harness verifies that every required unit has at least one non-empty supplied
fragment. Missing evidence fails the run rather than producing a paid request.

Q040 remains separate. Evaluation Contract v2 has no positive evidence units for
it. The harness supplies only the two nearby, human-reviewed gold spans with
identifiers such as `Q040-NEARBY-1`, explicitly marked
`nearby_clause_not_positive_evidence`. These clauses do not prove document-wide
absence and must not be treated as positive evidence for automatic termination.

The rendered prompt includes the actual context text, stable IDs, and provenance;
each run persists it in `generation_records.json`. The prompt instructs the model
to use supplied evidence only, preserve qualifications and overrides, abstain
when evidence is insufficient, atomize factual claims, and cite only supplied
context IDs. It contains no expected answer or question-specific hint and is
designed to be reused unchanged for the later Stage 2B arm.

## Structured-output boundary validation

The API-facing answer schema stays strict for the structural constraints that
the OpenAI Structured Outputs subset supports. That subset does not support
JSON Schema's `uniqueItems`, so `citation_context_ids` is expressed as an array
of strings without that keyword. Immediately after parsing the response, the
harness deterministically rejects duplicate citation context IDs within each
claim, before accepting or recording the generated answer as successful. This
preserves the logical uniqueness requirement without sending an unsupported
keyword to the provider.

Offline tests inspect the exact schema nested under `text.format.schema` in the
mocked `responses.create` request, verify that it contains no `uniqueItems`, and
exercise the post-parse uniqueness check. These tests validate our request
construction and local boundary contract; they cannot perfectly reproduce or
guarantee compatibility with the provider's server-side, evolving restricted
JSON Schema dialect. A provider can still reject a request before inference.

## Outputs and human review

Every new run gets a new directory under
`artifacts/generation/oracle_calibration/<run-id>/`; an existing run ID causes a
hard failure. The run contains:

- `run_manifest.json`: controls, timestamp, selected IDs, aggregate calls,
  tokens, estimated cost, latency, failures, and review status;
- `generation_records.json`: normalized per-question execution records,
  rendered prompts, exact context/provenance, structured outputs, usage, and
  errors;
- `raw_responses/Qxxx.json`: provider response objects for successful live calls;
- `human_review.md`: expected answers, unchanged required facts, supplied
  evidence, generated claims/citations, and blank human-label fields.

The execution record deliberately does not invent Contract v1 semantic labels.
After live generation, the reviewer must label correctness, every required fact,
each atomic claim's grounding, each claim/citation link's support, and Q040
abstention. Only then should those annotations be converted to the existing
`generation_experiment_output_v1.schema.json` shape and passed to
`evaluation.generation_contract_v1`. A factual claim is the smallest
independently supportable policy proposition: do not split stylistic wording,
but split clauses that could independently be true or false or require different
evidence.

## Pricing assumption

Pricing version `openai-gpt-5.4-standard-2026-10-05` uses the documented standard
GPT-5.4 rates current at implementation: $2.50 per million uncached input tokens,
$0.25 per million cached input tokens, and $15.00 per million output tokens. The
calculator uses provider-reported usage and cached input when available. Every
reported value is an **estimated API cost**, not actual billed cost or an invoice.
The versioned config retains the official pricing source URL.

## Commands

Validation only, with zero API calls and no key required:

```bash
PYTHONPATH=src python -m evaluation.oracle_generation_calibration \
  --config configs/oracle_generation_calibration_v1.json \
  --dry-run --run-id <unique-dry-run-id>
```

Live execution of only the frozen ten-question oracle calibration:

```bash
OPENAI_API_KEY='<set-in-shell>' PYTHONPATH=src \
python -m evaluation.oracle_generation_calibration \
  --config configs/oracle_generation_calibration_v1.json \
  --run-id <unique-live-run-id>
```

Never place the key in a config, output, command history, or committed file.

## Calibration acceptance and next decision

Do not infer generation quality before human review. Before scaling to the full
generation benchmark, require all records to be structurally valid, citation IDs
to resolve, no material evaluator/schema defect to remain, reviewers to apply
required-fact/claim-support/abstention labels consistently, ambiguous cases to
be documented and adjudicated, and deterministic aggregation to reproduce the
reviewed annotations. This small calibration intentionally has no statistical
pass threshold.

The committed artifact remains the earlier dry run: construction succeeded for
all ten questions with zero API calls, tokens, estimated cost, or measured
latency. Subsequent local live attempts occurred in this order:

1. The first attempt failed because the OpenAI SDK was not installed; no API
   inference occurred.
2. The second attempt failed with `UnicodeEncodeError` because the locally
   exported API key contained non-ASCII quote characters; no API inference
   occurred.
3. The third attempt reached the API, but all ten requests were rejected with
   HTTP 400 before inference because `uniqueItems` on
   `citation_context_ids` is unsupported by the provider's Structured Outputs
   schema subset.

Across those failed attempts, GPT-5.4 inference did **not** occur, recorded token
usage was 0, and estimated API cost was $0. GPT-5.4 generation quality has still
not been evaluated, human review has not started, and no generation-quality
conclusion is warranted. The third failure is a boundary-contract integration
failure between the application schema and the external API, not a model-quality
result.
