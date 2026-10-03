"""Measure page, gold-evidence, and approximate clause lengths without retrieval."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

TOKEN_PATTERN = re.compile(r"\w+(?:[\u2019']\w+)*|[^\w\s]", re.UNICODE)
NUMBERED_HEADING = re.compile(
    r"^(?:section\s+\d+|(?:\d+(?:\.\d+)*|[ivxlcdm]+|[A-Z])[.)])\s*[\u2013\u2014:\-]?\s*\S+",
    re.IGNORECASE,
)
STAT_KEYS = ("min", "p25", "p50", "mean", "p75", "p90", "p95", "max")
CANDIDATE_CHUNK_SIZES = (256, 512, 768, 1024)


def count_tokens(text: str) -> int:
    """Count deterministic lexical tokens (words/numbers and punctuation)."""
    return len(TOKEN_PATTERN.findall(text))


def nearest_rank(values: Iterable[int], percentile: int) -> int:
    """Return the nearest-rank percentile, suitable for small discrete samples."""
    ordered = sorted(values)
    if not ordered:
        raise ValueError("Cannot calculate a percentile of an empty sample")
    return ordered[max(0, math.ceil(percentile / 100 * len(ordered)) - 1)]


def describe(values: Iterable[int]) -> dict[str, int | float]:
    sample = list(values)
    if not sample:
        raise ValueError("Cannot describe an empty sample")
    return {
        "min": min(sample),
        "p25": nearest_rank(sample, 25),
        "p50": nearest_rank(sample, 50),
        "mean": round(mean(sample), 1),
        "p75": nearest_rank(sample, 75),
        "p90": nearest_rank(sample, 90),
        "p95": nearest_rank(sample, 95),
        "max": max(sample),
    }


def is_heading(line: str) -> bool:
    """Identify short heading-like lines; deliberately not a document parser."""
    text = " ".join(line.split())
    tokens = TOKEN_PATTERN.findall(text)
    if not text or len(text) > 120 or not (1 <= len(tokens) <= 18):
        return False
    lower = text.lower()
    if "page" in lower and re.search(r"\d\s*\|?\s*p\s*a\s*g\s*e", lower):
        return False
    if lower.startswith(("registered office:", "email:", "cin:", "uin:")):
        return False
    if NUMBERED_HEADING.match(text):
        return True
    letters = [char for char in text if char.isalpha()]
    return len(letters) >= 4 and text == text.upper()


def section_lengths(page_records: list[dict[str, Any]]) -> list[int]:
    """Split each document at detected headings and count non-empty text blocks."""
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for page in page_records:
        by_source[page["source_file"]].append(page)
    lengths: list[int] = []
    for pages in by_source.values():
        lines: list[str] = []
        for page in sorted(pages, key=lambda item: item["page_number"]):
            lines.extend(line.strip() for line in page["text"].splitlines() if line.strip())
        starts = [index for index, line in enumerate(lines) if is_heading(line)]
        boundaries = starts + [len(lines)]
        for index, start in enumerate(starts):
            token_count = count_tokens("\n".join(lines[start:boundaries[index + 1]]))
            if token_count:
                lengths.append(token_count)
    if not lengths:
        raise ValueError("Heading heuristic found no sections")
    return lengths


def load_pages(path: Path) -> list[dict[str, Any]]:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    required = {"page_number", "product_name", "source_file", "text"}
    if not records or any(not required <= record.keys() for record in records):
        raise ValueError("Extracted page artifact is empty or malformed")
    return records


def fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze(pages_path: Path, gold_path: Path, timestamp: str) -> dict[str, Any]:
    pages = load_pages(pages_path)
    gold = json.loads(gold_path.read_text(encoding="utf-8"))
    page_counts = [count_tokens(page["text"]) for page in pages]
    products: dict[str, list[int]] = defaultdict(list)
    for page, token_count in zip(pages, page_counts, strict=True):
        products[page["product_name"]].append(token_count)

    conventional = [record for record in gold["records"] if record["question_id"] != "Q040"]
    evidence_counts = [count_tokens(span["text"]) for record in conventional for span in record["evidence_spans"]]
    spans_per_question = Counter(len(record["evidence_spans"]) for record in conventional)
    q040 = next((record for record in gold["records"] if record["question_id"] == "Q040"), None)
    clauses = section_lengths(pages)
    total_tokens = sum(page_counts)

    return {
        "execution": {
            "timestamp_utc": timestamp,
            "tokenizer": "Unicode regex lexical tokens: words/numbers (internal apostrophes retained) and each punctuation mark",
            "percentiles": "nearest-rank",
            "inputs": {
                str(pages_path): {"sha256": fingerprint(pages_path), "records": len(pages)},
                str(gold_path): {"sha256": fingerprint(gold_path), "records": len(gold["records"])},
            },
        },
        "pages": {
            "corpus": {"count": len(page_counts), "tokens": total_tokens, **describe(page_counts)},
            "products": {name: {"count": len(vals), "tokens": sum(vals), **describe(vals)} for name, vals in sorted(products.items())},
        },
        "evidence": {
            "scope": "Q001-Q039 conventional positive evidence; Q040 excluded",
            "span_count": len(evidence_counts),
            "statistics": describe(evidence_counts),
            "questions_one_span": spans_per_question[1],
            "questions_multiple_spans": sum(count for spans, count in spans_per_question.items() if spans > 1),
            "spans_per_question": dict(sorted(spans_per_question.items())),
            "q040": {
                "classification": "abstention/insufficient-evidence probe; not conventional positive evidence",
                "span_count": len(q040["evidence_spans"]) if q040 else 0,
                "span_token_counts": [count_tokens(span["text"]) for span in q040["evidence_spans"]] if q040 else [],
            },
        },
        "sections": {
            "count": len(clauses),
            "heuristic": "Short (<=120 characters, <=18 tokens) numbered/Section lines or all-uppercase lines start a clause; page text is joined per source.",
            "statistics": {key: value for key, value in describe(clauses).items() if key in {"p50", "p75", "p90", "p95", "max"}},
        },
        "candidates": {
            str(size): {
                "evidence_spans_longer": sum(value > size for value in evidence_counts),
                "evidence_spans_longer_pct": round(100 * sum(value > size for value in evidence_counts) / len(evidence_counts), 1),
                "heuristic_clauses_longer": sum(value > size for value in clauses),
                "heuristic_clauses_longer_pct": round(100 * sum(value > size for value in clauses) / len(clauses), 1),
                "chunks_before_overlap": sum(math.ceil(value / size) for value in page_counts),
            }
            for size in CANDIDATE_CHUNK_SIZES
        },
    }


def _table(stats_by_name: dict[str, dict[str, Any]], include_count: bool = True) -> str:
    columns = (["count", "tokens"] if include_count else []) + list(STAT_KEYS)
    header = "| Scope | " + " | ".join(columns) + " |"
    rows = [header, "|---|" + "---:|" * len(columns)]
    for name, stats in stats_by_name.items():
        rows.append("| " + name + " | " + " | ".join(str(stats[key]) for key in columns) + " |")
    return "\n".join(rows)


def render_report(result: dict[str, Any]) -> str:
    execution, evidence = result["execution"], result["evidence"]
    page_rows = {"Entire corpus": result["pages"]["corpus"], **result["pages"]["products"]}
    section_stats = result["sections"]["statistics"]
    candidate_rows = []
    for size_text, values in result["candidates"].items():
        size = int(size_text)
        candidate_rows.append(
            f"| {size} | {values['evidence_spans_longer']} ({values['evidence_spans_longer_pct']}%) | "
            f"{values['heuristic_clauses_longer']} ({values['heuristic_clauses_longer_pct']}%) | "
            f"{values['chunks_before_overlap']} |"
        )
    inputs = "\n".join(f"- `{path}`: SHA-256 `{data['sha256']}` ({data['records']} records)" for path, data in execution["inputs"].items())
    return f"""# Corpus structure measurements

Generated at **{execution['timestamp_utc']}**. This is measurement only; it does not select or implement a chunking configuration.

## Method and reproducibility

- Token counting: {execution['tokenizer']}. This dependency-free proxy is deterministic but is **not** a model tokenizer.
- Percentiles: {execution['percentiles']}; means are rounded to one decimal.
- Inputs:
{inputs}
- Reproduce from a checkout without installing the package: `PYTHONPATH=src python -m corpus_analysis.analyze --output docs/corpus_structure_report.md`
- Paid model/API cost: **$0** (local Python analysis only).

## Page length (tokens)

{_table(page_rows)}

## Gold evidence spans

Q001-Q039 contain **{evidence['span_count']}** conventional positive-evidence spans.

| Scope | count | min | P25 | P50 | mean | P75 | P90 | P95 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Evidence spans | {evidence['span_count']} | {evidence['statistics']['min']} | {evidence['statistics']['p25']} | {evidence['statistics']['p50']} | {evidence['statistics']['mean']} | {evidence['statistics']['p75']} | {evidence['statistics']['p90']} | {evidence['statistics']['p95']} | {evidence['statistics']['max']} |

- Questions with one span: **{evidence['questions_one_span']}**
- Questions with multiple spans: **{evidence['questions_multiple_spans']}**
- Span-count distribution (`spans: questions`): **{evidence['spans_per_question']}**
- Q040 is kept separate: {evidence['q040']['classification']}. It has {evidence['q040']['span_count']} nearby/context spans of {evidence['q040']['span_token_counts']} tokens; they are excluded from positive-evidence statistics and chunk exceedance rates.

## Approximate section/clause length

The heuristic joins extracted pages per source, then starts a clause at a short line (at most 120 characters and 18 lexical tokens) that either begins with `Section`, a numeric/Roman/alphabetic marker, or is all uppercase. It found **{result['sections']['count']}** blocks.

| P50 | P75 | P90 | P95 | max |
|---:|---:|---:|---:|---:|
| {section_stats['p50']} | {section_stats['p75']} | {section_stats['p90']} | {section_stats['p95']} | {section_stats['max']} |

## Candidate fixed-size implications

Chunk counts split each extracted page independently as `ceil(page tokens / size)` and therefore estimate fixed chunks **before overlap**. This is an arithmetic comparison, not an implemented chunker.

| Size | Gold spans longer | Heuristic clauses longer | Approx. chunks |
|---:|---:|---:|---:|
{chr(10).join(candidate_rows)}

The clause-exceedance column provides a corpus-based fragmentation indicator; the gold-span exceedance column is a lower bound because even a shorter span can cross a fixed boundary. Smaller candidates also create more boundaries and therefore more opportunities to split content. These measurements do not evaluate retrieval precision, ranking dilution, latency, or downstream token cost. No candidate is declared optimal.

## Limitations and assumptions

- Lexical-token counts differ from embedding-model tokens; rerun with the eventual model tokenizer before locking configuration.
- Headers, footers, and extraction artifacts remain in page counts because the existing page-level output is measured as-is.
- Heading detection is intentionally shallow. It can mistake numbered list items or repeated uppercase furniture for clauses, miss wrapped/stylized headings, and count repeated page furniture inside a block. The maximum is especially sensitive to missed headings.
- Evidence spans measure individually annotated spans, not the distance between multiple spans or the context needed to interpret them. Fixed chunks can split spans shorter than the chunk due to boundary position, so exceedance is a lower bound on fragmentation risk.
- The chunk-count estimate preserves page boundaries and assumes no overlap, header removal, section-aware splitting, or cross-page chunks.
- The gold dataset is draft and small; Q040 requires a separate abstention protocol.

## Recommended next experiment

Have the architect select one or more candidate configurations, then measure retrieval Recall@K, ranking quality, citation accuracy, latency, and token/cost effects against this gold set. That experiment—not this descriptive analysis—should drive configuration choice.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pages", type=Path, default=Path("artifacts/extraction/policy_pages.jsonl"))
    parser.add_argument("--gold", type=Path, default=Path("evals/gold_dataset.json"))
    parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    report = render_report(analyze(args.pages, args.gold, timestamp))
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
