"""Extract policy wording PDFs into one JSON Lines record per page."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import pymupdf


@dataclass(frozen=True)
class PageRecord:
    """The unmodified plain-text representation of one PDF page."""

    source_file: str
    product_name: str | None
    page_number: int
    text: str


@dataclass(frozen=True)
class DocumentResult:
    """Extraction measurements for one document."""

    source_file: str
    product_name: str | None
    page_count: int
    pages_without_text: list[int]
    extracted_character_count: int


def load_document_metadata(metadata_path: Path) -> dict[str, dict[str, Any]]:
    """Index corpus metadata by filename and reject ambiguous duplicate entries."""
    raw = json.loads(metadata_path.read_text(encoding="utf-8"))
    documents: dict[str, dict[str, Any]] = {}
    for document in raw.get("documents", []):
        filename = document["filename"]
        if filename in documents:
            raise ValueError(f"Duplicate metadata entry for {filename}")
        documents[filename] = document
    return documents


def discover_pdfs(input_dir: Path) -> list[Path]:
    """Return PDFs in a stable, case-insensitive filename order."""
    return sorted(input_dir.glob("*.pdf"), key=lambda path: path.name.casefold())


def extract_document(
    pdf_path: Path, product_name: str | None
) -> tuple[list[PageRecord], DocumentResult]:
    """Extract plain text in PyMuPDF's default reading order, page by page."""
    records: list[PageRecord] = []
    with pymupdf.open(pdf_path) as document:
        for index, page in enumerate(document):
            # Deliberately retain PyMuPDF's output verbatim: no cleanup or layout
            # reconstruction belongs in this baseline experiment.
            text = page.get_text("text")
            records.append(
                PageRecord(
                    source_file=pdf_path.name,
                    product_name=product_name,
                    page_number=index + 1,
                    text=text,
                )
            )

    result = DocumentResult(
        source_file=pdf_path.name,
        product_name=product_name,
        page_count=len(records),
        pages_without_text=[
            record.page_number for record in records if not record.text.strip()
        ],
        extracted_character_count=sum(len(record.text) for record in records),
    )
    return records, result


def write_jsonl(records: Iterable[PageRecord], output_path: Path) -> None:
    """Write page records as deterministic UTF-8 JSON Lines."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as output:
        for record in records:
            output.write(
                json.dumps(asdict(record), ensure_ascii=False, sort_keys=True) + "\n"
            )


def run_extraction(
    input_dir: Path, metadata_path: Path, output_dir: Path
) -> dict[str, Any]:
    """Extract every discovered PDF and write page data plus run measurements."""
    metadata = load_document_metadata(metadata_path)
    pdf_paths = discover_pdfs(input_dir)
    all_records: list[PageRecord] = []
    results: list[DocumentResult] = []
    errors: list[dict[str, str]] = []

    for pdf_path in pdf_paths:
        document_metadata = metadata.get(pdf_path.name)
        if document_metadata is None:
            errors.append(
                {
                    "source_file": pdf_path.name,
                    "error": "No matching corpus metadata entry",
                }
            )
        try:
            records, result = extract_document(
                pdf_path,
                document_metadata.get("product_name") if document_metadata else None,
            )
        except (pymupdf.FileDataError, RuntimeError, ValueError) as error:
            errors.append({"source_file": pdf_path.name, "error": str(error)})
            continue
        all_records.extend(records)
        results.append(result)

    known_files = {path.name for path in pdf_paths}
    for filename in sorted(metadata.keys() - known_files, key=str.casefold):
        errors.append(
            {"source_file": filename, "error": "Metadata entry has no matching PDF"}
        )

    write_jsonl(all_records, output_dir / "policy_pages.jsonl")
    report = {
        "parser": f"PyMuPDF {pymupdf.VersionBind}",
        "pdfs_discovered": len(pdf_paths),
        "pdfs_processed": len(results),
        "page_records_written": len(all_records),
        "documents": [asdict(result) for result in results],
        "extraction_errors": errors,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "extraction_metrics.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir", type=Path, default=Path("corpus/policy_wordings")
    )
    parser.add_argument("--metadata", type=Path, default=Path("corpus/metadata.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/extraction"))
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = run_extraction(args.input_dir, args.metadata, args.output_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if report["extraction_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
