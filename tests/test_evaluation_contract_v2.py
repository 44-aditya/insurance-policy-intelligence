from evaluation.contract_v2 import canonicalize, fragment_witnesses


def _result(chunk_id: str, source: str = "right.pdf", rank: int = 1) -> dict:
    return {"chunk_id": chunk_id, "source_file": source, "page_number": 7, "rank": rank}


def _fragment(text: str = "Benefit is 60 days and is not available after waiver") -> dict:
    return {"source_file": "right.pdf", "source_page": 7, "text": text}


def test_normalization_handles_reviewed_extraction_boundaries_conservatively() -> None:
    assert canonicalize("Pre-\u00adHospitalization — 1 %") == canonicalize("pre hospitalization - 1%")
    assert canonicalize("cont\ninuous") == canonicalize("continuous")
    assert canonicalize("‘Claim Year’") == canonicalize("\"claim year\"")


def test_collective_coverage_requires_complete_ordered_source_interval() -> None:
    page = "Benefit is 60 days and is not available after waiver"
    chunks = {"a": "Benefit is 60 days and is", "b": "days and is not available after waiver"}
    witness = fragment_witnesses(_fragment(), [_result("a"), _result("b", rank=3)], chunks, {("right.pdf", 7): page})
    assert witness["matched"]
    assert {item["rank"] for item in witness["witnesses"]} == {1, 3}


def test_adversarial_variants_do_not_pass() -> None:
    page = "Benefit is 60 days and is not available after waiver"
    pages = {("right.pdf", 7): page}
    cases = [
        ("wrong-number", "Benefit is 90 days and is not available after waiver", "right.pdf"),
        ("missing-negation", "Benefit is 60 days and is available after waiver", "right.pdf"),
        ("wrong-product", page, "wrong.pdf"),
        ("missing-fragment", "Benefit is 60 days", "right.pdf"),
        ("semantic-paraphrase", "Coverage lasts two months and ends after deductible waiver", "right.pdf"),
    ]
    for chunk_id, text, source in cases:
        assert not fragment_witnesses(_fragment(), [_result(chunk_id, source)], {chunk_id: text}, pages)["matched"]
