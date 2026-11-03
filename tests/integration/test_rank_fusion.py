"""Integration tests for reciprocal rank fusion."""

from app.utils.rank_fusion import reciprocal_rank_fusion


def test_two_list_fusion():
    fused = reciprocal_rank_fusion([[1, 2, 3], [3, 4]], k=60)
    assert [mid for mid, _ in fused] == [3, 1, 2, 4]
    id3_score = next(score for mid, score in fused if mid == 3)
    assert abs(id3_score - (1 / 63 + 1 / 61)) < 1e-9


def test_tie_break_dense_first():
    fused = reciprocal_rank_fusion([[1, 2], [2, 1]], k=60)
    assert [mid for mid, _ in fused] == [1, 2]


def test_empty_rankings():
    assert reciprocal_rank_fusion([], k=60) == []


def test_single_list_preserves_order():
    fused = reciprocal_rank_fusion([[5, 9, 2]], k=60)
    assert [mid for mid, _ in fused] == [5, 9, 2]
