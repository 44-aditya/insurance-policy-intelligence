# Gold evaluation dataset: schema and annotation guide

## Purpose and status

This infrastructure supports a manually reviewed, source-grounded benchmark for
the Stage 1 policy-wording RAG baseline. `evals/gold_dataset.examples.json`
contains **examples only**, not the planned 30–50 question benchmark. The
examples must not be scored. This stage uses local files only and incurred **$0
paid API cost**.

The machine-readable contract is `evals/gold_dataset.schema.json`. Validation
uses the Python standard library, the corpus manifest, and file existence checks.
It adds no parser, retrieval, scoring, or model dependency.

## Authority and annotation workflow

The authoritative PDF—not PyMuPDF text, a future chunk, or LLM output—is the
source of truth. A human reviewer follows this sequence:

1. Open an authoritative PDF in `corpus/policy_wordings/`.
2. Formulate a realistic policy-wording question.
3. Determine the expected answer, preserving material qualifications.
4. Identify each fact that a correct answer must communicate and record it in
   `answer_rubric.required_facts`. These facts support later human evaluation;
   no automated or LLM judge is implemented here.
5. Copy the exact authoritative evidence span or spans from the PDF and record
   the one-based PDF page and filename for each span. Never replace the quote
   with an LLM paraphrase.
6. Classify question type, difficulty, and evidence format.
7. Run hard structural validation.
8. Optionally inspect warnings comparing the evidence with the current PyMuPDF
   extraction. A warning prompts extraction review; it does not reject gold.
9. Have a second human review consequential or ambiguous cases before changing
   dataset status to `reviewed` or `frozen`.

Gold truth uses source filename, page, and exact quotation rather than chunk IDs.
Chunk boundaries are future experimental variables. Attaching truth to them
would couple the benchmark to one strategy and make labels stale when chunking
changes. Evidence spans may come from different pages—and the schema does not
prevent different authoritative files—without concatenated page identifiers.

## Evaluation-case schema

Every case requires:

| Field | Meaning |
| --- | --- |
| `question_id` | Stable, unique identifier. |
| `question` | User-facing policy-wording question. |
| `expected_answer` | Human-reviewed reference answer supported by the evidence. |
| `answer_rubric.required_facts` | Non-empty list of facts a correct answer must communicate. |
| `evidence_spans` | Non-empty array of exact PDF quotations and their file/page metadata. |
| `question_type` | One primary taxonomy value. |
| `difficulty` | `easy`, `medium`, or `hard` under the criteria below. |
| `evidence_format` | `prose`, `list`, `table`, or `mixed`. |
| `notes` | Review context, ambiguity, or caveats; may be empty. |

Each evidence span is an object containing a `source_file`, positive integer
`source_page`, and non-empty `text`. Explicit objects keep multi-page evidence
machine-readable. `evidence_format` enables future performance slices by source
structure without prescribing retrieval or scoring behavior.

## Small question taxonomy

- `definition`: meaning assigned to a policy term.
- `coverage_benefit`: what a named benefit covers or provides.
- `exclusion`: circumstances or items the wording excludes.
- `waiting_period`: time that must elapse before stated coverage applies.
- `limit_sublimit`: monetary, frequency, duration, or other caps.
- `condition_eligibility`: prerequisites for a person, treatment, or benefit.
- `claims_procedure`: notification, documentation, authorization, or claim steps.
- `cross_section`: an answer that must combine distinct policy provisions.

Use `cross_section` only when combining provisions is central. Add categories or
secondary labels only if annotation evidence demonstrates a need.

## Difficulty criteria

Difficulty describes retrieval and evidence characteristics, not writing style:

- `easy`: one explicit evidence span directly states the answer, with no
  materially competing clause and substantially matching terminology.
- `medium`: evidence remains local but uses a synonym/cross-reference, is in a
  list or table, or requires a numerical, conditional, or negation-sensitive
  distinction that a superficially similar clause could obscure.
- `hard`: multiple separated spans, pages, or sections must be combined;
  semantically similar competing clauses must be distinguished; or nested
  conditions/exceptions make partial evidence materially misleading.

Span count informs rather than mechanically determines difficulty. A reviewer
must record the rationale for borderline cases in `notes`.

## Hard validation

`validate-gold-dataset` fails (nonzero exit) for:

- a non-object dataset/record/span or missing/unknown required fields;
- empty questions, answers, required facts, filenames, or evidence text;
- duplicate question IDs;
- invalid dataset status, question type, difficulty, or evidence format;
- a source filename absent from the corpus manifest or filesystem;
- a non-positive page or a page beyond the manifest's recorded PDF page count;
- an empty `evidence_spans` array or structurally invalid rubric/span.

Corpus `page_count` is recorded in `corpus/metadata.json`, keeping hard validity
independent of the current extraction artifact. Validation does not prove that a
quote was copied accurately, is sufficient, or supports the expected answer;
those remain human-review responsibilities.

## Soft extraction diagnostics

By default, the CLI also conservatively collapses whitespace and attempts to
find every gold span in `artifacts/extraction/policy_pages.jsonl`. A missing page
record or unmatched quote prints `WARNING`. It does **not** add a hard error,
change `is_valid`, or fail CI: PDF typography, ligatures, reading order, and
parser behavior may legitimately differ. Preserve warnings as candidates for
future extraction-quality investigation.

Run both layers:

```bash
validate-gold-dataset evals/gold_dataset.examples.json
```

Run hard validation without loading extraction output:

```bash
validate-gold-dataset --no-extraction-diagnostics evals/gold_dataset.examples.json
```

## Human decisions before the real benchmark

The owner should approve reviewer qualifications and adjudication; allocation
across products, taxonomy, evidence formats, and difficulty; treatment of
ambiguous/unanswerable cases; whether cross-document questions are desirable;
and criteria for freezing development and held-out splits. No customer data,
credentials, or external services are introduced. Human annotation time remains
an unpriced cost.

The recommended next experiment is a small independently double-annotated pilot.
Measure agreement on required facts, evidence sufficiency, categories, and
difficulty; review extraction warnings separately; revise the guide; and only
then build the 30–50 case benchmark.
