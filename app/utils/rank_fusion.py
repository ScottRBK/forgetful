"""Reciprocal Rank Fusion for hybrid search."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Literal

TieBreak = Literal["dense", "keyword"]


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[int]],
    k: int,
    tie_break: TieBreak = "dense",
) -> list[tuple[int, float]]:
    """Fuse ranked ID lists with RRF. rankings[0] is the dense leg, rankings[1] the keyword leg.

    Equal scores are ordered by rank in the tie_break leg (absent ids last), then by id.
    """
    if tie_break == "dense":
        tie_leg = 0
    elif tie_break == "keyword":
        tie_leg = 1
    else:
        raise ValueError(f"Unsupported tie_break: {tie_break}")

    if not rankings:
        return []

    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, memory_id in enumerate(ranking, start=1):
            scores[memory_id] = scores.get(memory_id, 0.0) + 1.0 / (k + rank)

    if len(rankings) == 1:
        return [(memory_id, scores[memory_id]) for memory_id in rankings[0]]

    tie_rank: dict[int, float] = {}
    for rank, memory_id in enumerate(rankings[tie_leg], start=1):
        tie_rank[memory_id] = float(rank)

    sorted_ids = sorted(
        scores.keys(),
        key=lambda mid: (-scores[mid], tie_rank.get(mid, math.inf), mid),
    )
    return [(memory_id, scores[memory_id]) for memory_id in sorted_ids]
