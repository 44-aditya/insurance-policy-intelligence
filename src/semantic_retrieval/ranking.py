"""Transparent in-memory cosine ranking."""

from __future__ import annotations

import math


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("vectors have different dimensions")
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        raise ValueError("cosine similarity is undefined for a zero vector")
    return sum(a * b for a, b in zip(left, right, strict=True)) / (
        left_norm * right_norm
    )


def rank_vectors(
    query: list[float], ids: list[str], vectors: list[list[float]], limit: int
) -> list[tuple[str, float]]:
    if len(ids) != len(vectors):
        raise ValueError("IDs and vectors have different lengths")
    scored = [
        (item_id, cosine_similarity(query, vector))
        for item_id, vector in zip(ids, vectors, strict=True)
    ]
    # ID provides a deterministic tie break.
    return sorted(scored, key=lambda item: (-item[1], item[0]))[:limit]
