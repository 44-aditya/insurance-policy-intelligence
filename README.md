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
