# insurance-policy-intelligence
Evaluation-driven GenAI platform for health insurance policy intelligence

## Baseline PDF text extraction

The Stage 1 baseline uses [PyMuPDF](https://pymupdf.readthedocs.io/) because it is
a small, direct PDF parser that can return plain text one page at a time without
introducing chunking, OCR, embeddings, or a document-processing framework. The
extractor preserves PyMuPDF's text exactly as returned; it does not clean policy
language or remove repeated page furniture.

Create an environment and run the extraction from the repository root:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/extract-policy-pages
```

The command discovers `*.pdf` files in `corpus/policy_wordings/` in a stable
filename order and writes generated data outside that authoritative directory:

- `artifacts/extraction/policy_pages.jsonl`: one UTF-8 JSON object per PDF page;
- `artifacts/extraction/extraction_metrics.json`: parser version, document/page
  counts, blank-page numbers, character counts, and errors.

Each JSONL line contains `source_file`, metadata-derived `product_name`, the
one-based PDF `page_number`, and unmodified `text`. Inspect a particular record
without rewriting the generated file, for example:

```bash
python - <<'PY'
import json

with open("artifacts/extraction/policy_pages.jsonl", encoding="utf-8") as lines:
    for line in lines:
        page = json.loads(line)
        if page["source_file"].startswith("medicare_select") and page["page_number"] == 1:
            print(page["text"])
PY
```

The experiment has **zero paid API cost**: parsing is local and makes no API or
LLM calls. Known baseline limitations include loss of typography and geometry,
imperfect reading order in multi-column or positioned layouts, flattened table
structure, fragmented bullets, and retained headers/footers. Image-only text
would be blank because OCR is deliberately out of scope. See
[`docs/extraction_quality_report.md`](docs/extraction_quality_report.md) for the
measured results and visual-review protocol.

## Gold evaluation dataset

The evaluation dataset is defined before retrieval or generation is built.
`evals/gold_dataset.schema.json` is the machine-readable contract, while
`evals/gold_dataset.examples.json` contains two clearly marked, non-benchmark
examples of single- and multi-page evidence. Validate it locally with:

```bash
validate-gold-dataset evals/gold_dataset.examples.json
```

Hard validation checks source files and one-based pages against the authoritative
corpus manifest. Optional diagnostics compare exact evidence with normalized
PyMuPDF extraction text, but a mismatch only warns and never invalidates gold. See `docs/gold_dataset_annotation.md` for the human
annotation workflow, taxonomy, difficulty rubric, limitations, and decisions
required before creating the real benchmark. This stage also has **zero paid
API cost**.

## Measured page retrieval control

Run the local lexical vector baseline over the unchanged extraction:

```bash
python -m policy_retrieval.baseline
# Or, after installing the updated package:
run-retrieval-baseline --dataset evals/retrieval_pilot.draft.json
python -m pytest
```

Configuration is in `evals/retrieval_baseline.config.json`; default K values are
1, 3, 5, and 10. Full pages are the retrieval units. Standard-library TF-IDF
with L2-normalized cosine scores supplies a deterministic lexical vector
control, **not** pretrained semantic embeddings. No external credentials or
services are required. Index tokenization does not modify saved page text.
There is no product filter derived from gold labels, cleanup, reranking,
fine-tuning, or LLM generation. Unknown query terms yield no positive results.

Outputs in `artifacts/retrieval/baseline/`:

- `query_results.jsonl`: hash-bound page IDs, filenames/pages, ordered cosine
  scores, document metadata, metrics, timing, token/cost fields, and failures.
- `experiment_metrics.json`: input/code hashes, configuration, aggregate and
  slice results, latency distributions, environment, usage, and cost accounting.
- `baseline_report.md`: concise results and limitations.

The 10-question pilot follows the existing gold schema but is **draft**, with
provisional quotes transcribed from extraction. It requires independent review
against authoritative PDFs. Existing `examples_only` records are refused.
The interim metric requires all distinct annotated pages within top K; it does
not establish passage fidelity, complete evidence, answer correctness, or
production quality. Repeated runs preserve IDs/rankings/scores; measured timing
and timestamps will vary. PDF hashes and exact manifest page coverage are
checked before scoring. Version errors remain untestable because alternate
versions are absent and version dates are unknown. Paid API cost is zero;
compute and human time remain unpriced.
