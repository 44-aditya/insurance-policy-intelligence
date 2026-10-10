# Insurance Policy Intelligence

**Evaluation-driven GenAI platform for health insurance policy intelligence**

A production-oriented GenAI project for answering complex questions from health insurance policy wordings while making the quality, cost, latency, and failure modes of the system measurable.

The objective is not simply to build a RAG chatbot.

The objective is to understand and engineer the complete GenAI value chain:

**Policy PDFs → Extraction → Gold Evaluation Dataset → Chunking → Embeddings → Semantic Retrieval → Retrieval Evaluation → Generation → End-to-End Evaluation → Reranking / Hybrid Retrieval → Structured Rules → Production Architecture**

The system is intentionally being built in stages. Additional architectural complexity is introduced only when evaluation results demonstrate that it solves a measurable problem.

---

## Why this project exists

Health insurance policy documents are difficult inputs for a question-answering system.

Important answers may depend on:

- definitions located far from the relevant benefit;
- exceptions buried in fine print;
- waiting periods and numerical limits;
- tables;
- cross-section dependencies;
- similar terminology across multiple insurance products;
- exclusions and carve-outs;
- multiple evidence passages required to answer one question.

A system that retrieves a semantically similar paragraph can therefore still return a confidently wrong answer.

This project treats policy intelligence as an **information retrieval and grounded reasoning problem**, not merely an LLM prompting problem.

---

# Architecture Philosophy

The architecture evolves through evidence.

```text
                         ┌──────────────────────────────┐
                         │   Policy Wording PDFs        │
                         │   Authoritative Corpus       │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │     Deterministic PDF        │
                         │        Extraction            │
                         │        PyMuPDF               │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │ Page-Level Extraction        │
                         │ + Corpus Metadata            │
                         └──────────────┬───────────────┘
                                        │
                        ┌───────────────┴───────────────┐
                        │                               │
                        ▼                               ▼
          ┌────────────────────────┐       ┌─────────────────────────┐
          │ Gold Evaluation Set    │       │ Retrieval Corpus        │
          │ Questions + Evidence   │       │ Chunking                │
          │ Failure Taxonomy       │       │ Tokenization            │
          └───────────┬────────────┘       └────────────┬────────────┘
                      │                                 │
                      │                                 ▼
                      │                    ┌─────────────────────────┐
                      │                    │ Voyage Embeddings       │
                      │                    │ Bi-Encoder Retrieval    │
                      │                    └────────────┬────────────┘
                      │                                 │
                      │                                 ▼
                      │                    ┌─────────────────────────┐
                      └───────────────────►│ Cosine Similarity       │
                                           │ Top-K Retrieval         │
                                           └────────────┬────────────┘
                                                        │
                                                        ▼
                                           ┌─────────────────────────┐
                                           │ Retrieval Evaluation    │
                                           │ Recall@K                │
                                           │ Ranking / Failure       │
                                           │ Latency / Tokens / Cost │
                                           └────────────┬────────────┘
                                                        │
                                             evidence-based decision
                                                        │
                   ┌────────────────────────────────────┼──────────────────────────────────┐
                   │                                    │                                  │
                   ▼                                    ▼                                  ▼
        Stage 1                           Stage 2                              Stage 3+
 Vector Retrieval → LLM        Retrieval → Reranker → LLM        Structured / Hybrid AI
```

The project deliberately avoids introducing reranking, agents, vector databases, OCR pipelines, or complex document frameworks before the baseline is measurable.

---

# Current Corpus

The initial corpus contains policy wordings for four Tata AIG health insurance products:

- MediCare Premier
- MediCare Select
- MediCare Reserve
- MediCare Plus

The authoritative source documents are stored separately from generated artifacts.

```text
corpus/
└── policy_wordings/
```

Generated extraction, retrieval, and evaluation artifacts are never written back into the authoritative corpus directory.

Corpus metadata is versioned so retrieval experiments can be tied to the exact source documents they were evaluated against.

---

# 1. Deterministic PDF Extraction

The first engineering step was deliberately simple.

The Stage 1 baseline uses **PyMuPDF** because it provides direct page-level PDF text extraction without introducing OCR, chunking, embeddings, LLMs, or a document-processing framework.

This gives us a controlled baseline for understanding what information is actually available to downstream retrieval.

## Why page-level extraction first?

Before optimizing retrieval, we need to distinguish two very different failure modes:

```text
Information absent / corrupted during extraction
                    vs.
Information extracted correctly but not retrieved
```

Without this separation, poor retrieval performance could incorrectly be blamed on embeddings when the actual problem originated during document parsing.

The extractor therefore preserves PyMuPDF text **exactly as returned**.

No attempt is made to:

- rewrite policy language;
- reconstruct tables;
- remove headers or footers;
- repair fragmented bullets;
- reorder text heuristically;
- normalize policy clauses.

This is intentional.

---

## Running extraction

Create an environment from the repository root:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/extract-policy-pages
```

The extractor discovers `*.pdf` files in:

```text
corpus/policy_wordings/
```

using stable filename ordering.

Generated artifacts are written to:

```text
artifacts/extraction/
├── policy_pages.jsonl
└── extraction_metrics.json
```

### `policy_pages.jsonl`

Contains one UTF-8 JSON object per PDF page.

Each record includes:

```text
source_file
product_name
page_number
text
```

Page numbering is one-based so evidence references correspond directly with human-readable PDF page references.

Example inspection:

```bash
python - <<'PY'
import json

with open("artifacts/extraction/policy_pages.jsonl", encoding="utf-8") as lines:
    for line in lines:
        page = json.loads(line)

        if (
            page["source_file"].startswith("medicare_select")
            and page["page_number"] == 1
        ):
            print(page["text"])
PY
```

### `extraction_metrics.json`

Records reproducibility and extraction diagnostics including:

- parser version;
- document count;
- page count;
- blank pages;
- character counts;
- extraction errors.

---

# 2. Extraction Quality Analysis

PDF extraction is not assumed to be correct merely because text was successfully returned.

Known baseline limitations include:

- flattened table structures;
- loss of typography;
- loss of geometric relationships;
- imperfect reading order;
- multi-column layout issues;
- fragmented bullets;
- retained headers and footers;
- image-only content returning no text.

These limitations matter because retrieval models operate on the extracted representation rather than on what a human visually sees in the PDF.

A visually obvious policy table can therefore become a semantically ambiguous sequence of text after extraction.

The extraction stage currently has:

**Paid API cost: ₹0**

Parsing is entirely local and makes no LLM or external inference calls.

See:

```text
docs/extraction_quality_report.md
```

for the measured extraction results and visual-review protocol.

---

# 3. Evaluation Before Optimization

A central design decision in this project is:

> **Build the evaluation system before optimizing the retrieval system.**

Without a stable benchmark, architectural improvements become subjective.

A reranker, larger embedding model, larger chunks, prompt change, or additional retrieved context may appear better on a few examples while actually degrading overall performance.

The project therefore maintains a **gold evaluation dataset** describing what evidence is required to correctly answer each benchmark question.

---

# 4. Gold Evaluation Dataset

The evaluation layer separates:

```text
Question
   ↓
Authoritative evidence
   ↓
Expected answer
```

from whatever chunks the retrieval system happens to produce.

This distinction is critical.

**Gold evidence is not a retrieved chunk.**

Gold evidence represents the authoritative source material required to answer the question correctly.

Retrieval results are evaluated against it.

---

## Dataset contract

```text
evals/
├── gold_dataset.schema.json
└── gold_dataset.examples.json
```

`gold_dataset.schema.json` defines the machine-readable contract.

`gold_dataset.examples.json` contains clearly marked non-benchmark examples demonstrating single-page and multi-page evidence.

Validate locally with:

```bash
validate-gold-dataset evals/gold_dataset.examples.json
```

Hard validation checks:

- referenced source documents exist;
- evidence pages exist;
- page numbers are valid;
- evidence conforms to the schema.

Optional diagnostics compare evidence text with normalized PyMuPDF extraction.

Importantly:

> Extraction disagreement produces a warning, not invalid gold evidence.

The PDF policy wording remains authoritative.

This prevents an extraction defect from silently redefining ground truth.

See:

```text
docs/gold_dataset_annotation.md
```

for the annotation workflow and design decisions.

---

# 5. Evaluation Dataset as Failure-Mode Modeling

The benchmark is intentionally not designed as a collection of easy policy questions.

It is designed to expose architectural weaknesses.

Current evaluation categories include cases such as:

### Headline-only traps

The obvious clause provides a general rule, while an exception elsewhere changes the answer.

### Cross-section dependencies

The correct answer requires combining information from multiple sections.

### Competing numerical rules

Multiple policy clauses contain semantically similar but different waiting periods, limits, percentages, or durations.

### Negative-space reasoning

The question may depend on recognizing that a benefit, exception, or entitlement is **not** present.

### Table-dependent questions

The answer depends on relationships represented visually in a table that may have been degraded during PDF extraction.

### Wrong-product retrieval

Closely related products contain similar language, creating plausible but incorrect retrieval candidates.

### Multi-page evidence

No single page contains sufficient information to answer correctly.

This turns the evaluation dataset into a **failure-mode model for the architecture**, rather than a collection of demonstration questions.

---

# 6. Stage 1 Semantic Retrieval

The first retrieval architecture is deliberately minimal:

```text
Question
   │
   ▼
Query Embedding
   │
   ▼
Cosine Similarity
   │
   ▼
Top-K Chunks
```

No LLM answer generation is required to evaluate whether the retrieval layer itself works.

This is important because otherwise retrieval failures and generation failures become mixed together.

---

## Chunking

The extraction JSONL is consumed unchanged.

Pages are divided into:

```text
512-token chunks
100-token overlap
```

while preserving page boundaries.

The initial chunking strategy is intentionally straightforward.

It is not assumed to be optimal.

Instead, it establishes a reproducible baseline against which later strategies such as:

- smaller chunks;
- larger chunks;
- semantic chunking;
- section-aware chunking;
- hierarchical retrieval

can be compared.

---

# 7. Embeddings

Chunks are embedded using Voyage embeddings.

Document chunks are encoded as:

```text
document
```

inputs.

Questions are encoded as:

```text
query
```

inputs.

This reflects the asymmetric retrieval objective: the query and document serve different roles even though they ultimately exist in the same embedding space.

The resulting vectors provide compact semantic representations of the policy text and questions.

---

# 8. Vector Retrieval

Stage 1 intentionally does **not** use a vector database.

Vectors are stored locally and ranking is performed using cosine similarity.

Conceptually:

```text
similarity(query, document) =
        query · document
-------------------------------
||query|| × ||document||
```

The highest-scoring chunks become the retrieval candidates.

This choice keeps the experiment focused on the retrieval model rather than introducing infrastructure whose scalability benefits are not yet required by the corpus size.

A vector database can be introduced later when scale or production requirements justify it.

---

## Running Stage 1 retrieval

Set the Voyage API key:

```bash
export VOYAGE_API_KEY='...'
```

Run:

```bash
run-semantic-retrieval
```

The key is read only from the environment and is never persisted.

If the key is missing, execution stops before tokenizer download, chunk creation, or API access.

Artifacts are written under:

```text
artifacts/retrieval/stage1_voyage4/
```

including:

- generated chunks;
- embeddings;
- retrieved page/chunk IDs;
- cosine similarity scores;
- rank order;
- latency;
- token usage;
- failure information;
- experiment cost fields.

See:

```text
docs/stage1_semantic_retrieval_report.md
```

for experiment methodology and interpretation rules.

---

# 9. Retrieval Evaluation

The first major quality question is:

> **Did the retriever find the evidence required to answer the question?**

The primary baseline metric is therefore **Recall@K**.

Conceptually:

```text
Gold evidence required
        │
        ▼
Was it present in Top-K retrieval?
        │
   ┌────┴────┐
  Yes        No
   │          │
success    retrieval failure
```

This distinction becomes important later when evaluating an LLM.

For example:

```text
Recall@5 = 92%
Oracle-context answer accuracy = 68%
End-to-end accuracy = 64%
```

would suggest retrieval is relatively strong while generation or reasoning remains a bottleneck.

Conversely:

```text
Recall@5 = 65%
Oracle-context answer accuracy = 96%
End-to-end accuracy = 61%
```

indicates that improving prompts or changing LLMs would attack the wrong problem.

The retrieval layer is failing before the LLM receives the evidence.

---

# 10. Failure Slicing

Aggregate metrics can conceal important weaknesses.

Stage 1 therefore records performance across targeted failure slices, including:

```text
Table-dependent questions
Wrong-document / wrong-product retrieval
Multi-page evidence
Competing numerical clauses
Known extraction-problem pages
MediCare Plus extraction issues
```

This helps turn evaluation results into architectural decisions.

For example:

```text
Overall Recall@5: high
Table questions: poor
```

would suggest investigating document representation or table extraction rather than replacing the embedding model globally.

---

# 11. Cost Is a First-Class Evaluation Metric

Production GenAI systems are not optimized on accuracy alone.

Every experiment should eventually be evaluated across:

```text
Quality
Latency
Token usage
Cost
Failures
Operational complexity
```

The project therefore tracks **cost per experiment** during development.

Later stages will extend this to:

```text
cost per query
```

for the deployed system.

This allows architectural improvements to be expressed as measurable trade-offs rather than as qualitative claims.

For example:

```text
Reranker:
+6% Recall / ranking quality
+180 ms latency
+$0.002/query
```

creates a much more meaningful engineering decision than simply saying that reranking "improved results."

---

# 12. Planned Architecture Evolution

The project follows a staged architecture.

Complexity must earn its place.

## Stage 1 — Baseline RAG

```text
PDF
 ↓
Extraction
 ↓
Chunking
 ↓
Embeddings
 ↓
Vector Retrieval
 ↓
LLM
```

Goal:

Establish a measurable retrieval and answer-quality baseline.

---

## Stage 2 — Reranking

```text
Vector Retrieval
        ↓
Candidate Chunks
        ↓
Cross-Encoder / Reranker
        ↓
Best Evidence
        ↓
LLM
```

Reranking will only be introduced if Stage 1 demonstrates that:

- useful evidence frequently appears in the candidate set;
- ranking quality is insufficient;
- better ordering can materially improve downstream answers.

Evaluation will compare the benefit against:

- latency;
- inference cost;
- architectural complexity.

---

## Stage 3 — Structured Data + Rules

Certain insurance questions may not be best solved through semantic retrieval alone.

Examples include:

```text
waiting periods
coverage limits
deductibles
room-rent restrictions
co-pay percentages
eligibility conditions
```

For deterministic policy facts, the architecture may evolve toward:

```text
                 ┌── Vector Retrieval ──┐
Question ────────┤                      ├──► LLM
                 └── Structured Rules ──┘
```

The goal is not to force every problem through an LLM.

The goal is to choose the most reliable computational mechanism for each class of information.

---

## Stage 4 — Hybrid / Agentic Capabilities

Agentic behavior will only be introduced when the system has genuine multi-step decision or tool-use requirements.

Possible future capabilities include:

- selecting retrieval strategies;
- querying structured policy data;
- comparing multiple products;
- running deterministic calculators;
- validating answers against evidence;
- invoking specialized tools.

Agents are therefore an architectural option, not the starting assumption.

---

# 13. Why This Project Does Not Start With an Agent

A common GenAI architecture mistake is:

```text
Complex problem
      ↓
Add agent
```

This project follows the opposite philosophy.

Start with:

```text
the simplest architecture capable of producing a measurable baseline
```

Then introduce complexity only when a specific failure mode justifies it.

This makes it possible to answer:

> What problem did this component solve?

> How much did quality improve?

> How much latency did it add?

> How much did it cost?

> What new failure modes did it introduce?

Without these answers, architectural complexity is difficult to defend.

---

# 14. Experimentation Loop

The development methodology is:

```text
Build baseline
      ↓
Measure
      ↓
Identify failure modes
      ↓
Form hypothesis
      ↓
Change one architectural variable
      ↓
Re-run evaluation
      ↓
Compare quality / latency / cost
      ↓
Keep or reject change
```

This makes the repository an engineering record of **why the architecture evolved**, not merely what the final architecture looks like.

---

# 15. Core Metrics

As the platform evolves, experiments are expected to track metrics across four dimensions.

| Dimension | Example Metrics |
|---|---|
| Retrieval | Recall@K, Precision@K, MRR, NDCG |
| Generation | Correctness, faithfulness, citation accuracy |
| System | Latency, failures, throughput |
| Economics | Tokens, cost per experiment, cost per query |

Not every metric is required at every stage.

Metrics are introduced when they help answer a real architectural question.

---

# 16. Repository Structure

The repository is organized so source documents, evaluation assets, generated artifacts, code, and documentation remain clearly separated.

```text
insurance-policy-intelligence/
│
├── corpus/
│   └── policy_wordings/
│       └── authoritative policy PDFs
│
├── evals/
│   ├── gold_dataset.schema.json
│   └── gold_dataset.examples.json
│
├── artifacts/
│   ├── extraction/
│   │   ├── policy_pages.jsonl
│   │   └── extraction_metrics.json
│   │
│   └── retrieval/
│       └── stage1_voyage4/
│
├── docs/
│   ├── extraction_quality_report.md
│   ├── gold_dataset_annotation.md
│   └── stage1_semantic_retrieval_report.md
│
├── tests/
│
└── README.md
```

Generated artifacts are separated from authoritative source material so experiments remain reproducible and do not mutate the underlying corpus.

---

# 17. Engineering Principles

Several principles guide the project.

### Evaluation before optimization

Do not improve a system that has not been measured.

### Separate retrieval failures from generation failures

An LLM cannot reason over evidence it never receives.

### Preserve authoritative evidence

Extraction output is not ground truth.

The policy wording is.

### Prefer deterministic components where possible

Use LLM reasoning where ambiguity requires it, not where deterministic logic is more reliable.

### Introduce complexity only when justified

Rerankers, vector databases, OCR pipelines, agents, and hybrid architectures must solve measurable problems.

### Track economics alongside quality

An architecture that improves quality while making every query economically impractical is not necessarily an improvement.

### Preserve reproducibility

Experiments should record their configuration, artifacts, metrics, and costs so results can be independently inspected.

---

# 18. Current Status

The project currently has the foundations required for controlled GenAI experimentation:

```text
✓ Versioned health insurance corpus
✓ Deterministic page-level PDF extraction
✓ Extraction-quality analysis
✓ Machine-readable gold dataset schema
✓ Evidence annotation methodology
✓ Failure-mode taxonomy
✓ Token-aware page-bounded chunking
✓ Voyage embedding integration
✓ Query/document embedding separation
✓ Local cosine-similarity retrieval
✓ Reproducible Stage 1 retrieval artifacts
✓ Retrieval evaluation framework
✓ Latency / token / failure instrumentation
✓ Cost-per-experiment tracking
```

The next architectural decisions are intentionally dependent on measured baseline results.

---

# 19. What Comes Next

Near-term development focuses on completing the measurable Stage 1 pipeline:

```text
Retrieval baseline
        ↓
Retrieval failure analysis
        ↓
LLM answer generation
        ↓
Oracle-context evaluation
        ↓
End-to-end evaluation
```

This will let the system distinguish:

```text
Did retrieval fail?
        vs.
Did the LLM fail despite receiving the correct evidence?
```

Only after that diagnosis will the project evaluate whether components such as reranking, improved chunking, structured policy representations, or hybrid retrieval are justified.

---

# 20. The Larger Goal

This repository is both a working insurance intelligence platform and an exploration of how production GenAI systems should be engineered.

The central question is not:

> **Can an LLM answer questions about an insurance PDF?**

Modern LLMs can often do that in a demo.

The harder question is:

> **Can we build a system whose answers are reliably grounded in authoritative policy language, whose failures can be diagnosed, whose improvements can be measured, and whose latency and cost remain acceptable as the corpus and query volume grow?**

That is the problem this project is designed to solve.
