"""Deterministic, page-bounded fixed-token chunking."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol


class Tokenizer(Protocol):
    """The minimal tokenizer interface needed by the chunker."""

    def offsets(self, text: str) -> list[tuple[int, int]]: ...


class VoyageTokenizer:
    """Use Voyage's published tokenizer and retain original-text offsets."""

    def __init__(self, model: str) -> None:
        import voyageai

        # Tokenization is local; this placeholder is never sent to Voyage.
        self._tokenizer = voyageai.Client(api_key="local-tokenization-only").tokenizer(
            model
        )

    def offsets(self, text: str) -> list[tuple[int, int]]:
        return [tuple(offset) for offset in self._tokenizer.encode(text).offsets]


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    source_file: str
    product_name: str | None
    page_number: int
    chunk_index: int
    token_start: int
    token_end: int
    token_count: int
    text: str


def stable_chunk_id(source_file: str, page_number: int, chunk_index: int) -> str:
    """Identify a chunk from stable provenance, independent of run order."""
    identity = f"{source_file}\0{page_number}\0{chunk_index}".encode()
    return f"chunk-{hashlib.sha256(identity).hexdigest()[:16]}"


def chunk_page(
    page: dict[str, object], tokenizer: Tokenizer, size: int, overlap: int
) -> list[Chunk]:
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError(
            "chunk size must be positive and overlap must satisfy 0 <= overlap < size"
        )
    text = str(page["text"])
    offsets = [(start, end) for start, end in tokenizer.offsets(text) if end > start]
    chunks: list[Chunk] = []
    step = size - overlap
    for index, start in enumerate(range(0, len(offsets), step)):
        window = offsets[start : start + size]
        if not window:
            break
        token_end = start + len(window)
        chunks.append(
            Chunk(
                chunk_id=stable_chunk_id(
                    str(page["source_file"]), int(page["page_number"]), index
                ),
                source_file=str(page["source_file"]),
                product_name=(
                    str(page["product_name"])
                    if page.get("product_name") is not None
                    else None
                ),
                page_number=int(page["page_number"]),
                chunk_index=index,
                token_start=start,
                token_end=token_end,
                token_count=len(window),
                # Offset slicing preserves the unchanged extracted characters.
                text=text[window[0][0] : window[-1][1]],
            )
        )
        if token_end == len(offsets):
            break
    return chunks


def chunk_jsonl(
    path: Path, tokenizer: Tokenizer, size: int, overlap: int
) -> list[Chunk]:
    chunks: list[Chunk] = []
    with path.open(encoding="utf-8") as lines:
        for line in lines:
            chunks.extend(chunk_page(json.loads(line), tokenizer, size, overlap))
    return chunks


def write_chunks(chunks: list[Chunk], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as output:
        for chunk in chunks:
            output.write(
                json.dumps(asdict(chunk), ensure_ascii=False, sort_keys=True) + "\n"
            )
