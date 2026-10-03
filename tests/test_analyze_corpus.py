import json
from pathlib import Path

import pytest

from corpus_analysis.analyze import analyze, count_tokens, describe, is_heading, render_report


def test_token_count_and_nearest_rank_statistics() -> None:
    assert count_tokens("Don't split 24-hours.") == 6
    assert describe([1, 2, 3, 4]) == {
        "min": 1, "p25": 1, "p50": 2, "mean": 2.5,
        "p75": 3, "p90": 4, "p95": 4, "max": 4,
    }
    with pytest.raises(ValueError, match="empty sample"):
        describe([])


def test_heading_heuristic_accepts_clauses_and_rejects_furniture() -> None:
    assert is_heading("Section 2 – Benefits")
    assert is_heading("4. AYUSH Hospital")
    assert is_heading("GENERAL EXCLUSIONS")
    assert not is_heading("Registered Office: Somewhere")
    assert not is_heading("4 | P a g e")
    assert not is_heading("This is ordinary policy prose that should remain in its clause.")


def test_analysis_excludes_q040_and_estimates_page_bounded_chunks(tmp_path: Path) -> None:
    pages_path = tmp_path / "pages.jsonl"
    pages = [
        {"page_number": 1, "product_name": "A", "source_file": "a.pdf", "text": "SECTION ONE\n" + "word " * 300},
        {"page_number": 2, "product_name": "A", "source_file": "a.pdf", "text": "2. Next\nshort text"},
    ]
    pages_path.write_text("\n".join(json.dumps(page) for page in pages), encoding="utf-8")
    gold_path = tmp_path / "gold.json"
    gold_path.write_text(json.dumps({"records": [
        {"question_id": "Q001", "evidence_spans": [{"text": "one two"}]},
        {"question_id": "Q040", "evidence_spans": [{"text": "ignored nearby context"}]},
    ]}), encoding="utf-8")

    result = analyze(pages_path, gold_path, "2026-01-01T00:00:00+00:00")

    assert result["evidence"]["span_count"] == 1
    assert result["evidence"]["q040"]["span_token_counts"] == [3]
    assert result["candidates"]["256"]["chunks_before_overlap"] == 3
    assert result["candidates"]["256"]["heuristic_clauses_longer"] == 1
    assert "Paid model/API cost: **$0**" in render_report(result)
