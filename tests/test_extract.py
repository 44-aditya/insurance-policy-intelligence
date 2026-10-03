import json
from pathlib import Path

import pymupdf

from policy_extraction.extract import discover_pdfs, extract_document, run_extraction


def make_pdf(path: Path, page_texts: list[str]) -> None:
    document = pymupdf.open()
    for text in page_texts:
        page = document.new_page()
        if text:
            page.insert_text((72, 72), text)
    document.save(path)
    document.close()


def test_discover_pdfs_has_stable_case_insensitive_order(tmp_path: Path) -> None:
    for filename in ("z.pdf", "A.pdf", "ignored.txt"):
        (tmp_path / filename).touch()

    assert [path.name for path in discover_pdfs(tmp_path)] == ["A.pdf", "z.pdf"]


def test_extract_document_preserves_page_boundaries_and_blank_pages(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "policy.pdf"
    make_pdf(pdf_path, ["First page", "", "Third page"])

    records, result = extract_document(pdf_path, "Example Product")

    assert [(record.page_number, record.text) for record in records] == [
        (1, "First page\n"),
        (2, ""),
        (3, "Third page\n"),
    ]
    assert all(record.source_file == "policy.pdf" for record in records)
    assert all(record.product_name == "Example Product" for record in records)
    assert result.page_count == 3
    assert result.pages_without_text == [2]
    assert result.extracted_character_count == len("First page\nThird page\n")


def test_run_extraction_writes_deterministic_jsonl_and_metrics(tmp_path: Path) -> None:
    input_dir = tmp_path / "pdfs"
    input_dir.mkdir()
    make_pdf(input_dir / "policy.pdf", ["Policy text"])
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(
        json.dumps(
            {"documents": [{"filename": "policy.pdf", "product_name": "Product"}]}
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "output"

    report = run_extraction(input_dir, metadata_path, output_dir)
    first_output = (output_dir / "policy_pages.jsonl").read_bytes()
    run_extraction(input_dir, metadata_path, output_dir)

    assert (output_dir / "policy_pages.jsonl").read_bytes() == first_output
    assert json.loads(first_output) == {
        "page_number": 1,
        "product_name": "Product",
        "source_file": "policy.pdf",
        "text": "Policy text\n",
    }
    assert report["pdfs_processed"] == 1
    assert report["extraction_errors"] == []
