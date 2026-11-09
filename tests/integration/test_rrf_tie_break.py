"""FF-61: RRF tie-break leg and identifier-query detection."""

import pytest

from app.utils.keyword_query import is_identifier_query
from app.utils.rank_fusion import reciprocal_rank_fusion


def _ids(fused: list[tuple[int, float]]) -> list[int]:
    return [memory_id for memory_id, _ in fused]


def test_default_tie_break_is_dense():
    assert _ids(reciprocal_rank_fusion([[10, 1], [20]], k=60)) == [10, 20, 1]


def test_keyword_tie_break_lets_keyword_only_hit_win():
    fused = reciprocal_rank_fusion([[10, 1], [20]], k=60, tie_break="keyword")
    assert _ids(fused) == [20, 10, 1]


def test_keyword_tie_break_keeps_score_order():
    fused = reciprocal_rank_fusion([[1, 2, 3], [3, 4]], k=60, tie_break="keyword")
    assert _ids(fused) == [3, 1, 4, 2]
    assert abs(dict(fused)[3] - (1 / 63 + 1 / 61)) < 1e-9


def test_keyword_tie_break_single_list_preserves_order():
    assert _ids(reciprocal_rank_fusion([[5, 9, 2]], k=60, tie_break="keyword")) == [5, 9, 2]


def test_keyword_tie_break_empty_rankings():
    assert reciprocal_rank_fusion([], k=60, tie_break="keyword") == []


def test_unsupported_tie_break_raises():
    with pytest.raises(ValueError, match="Unsupported tie_break"):
        reciprocal_rank_fusion([[1], [2]], k=60, tie_break="bogus")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "query",
    [
        "#2753",
        "see #2753 notes",
        "  #123  ",
        "OPS-6331",
        "FF-61 hybrid tie",
        "DH-13",
        "uvLockRelative",
        "WikiBrowse",
        "Resolve-WorkPath.ps1",
        "uvx.exe",
        "YYYY-MM-DD.md",
        "app/utils",
        "snake_case_name",
    ],
)
def test_identifier_queries_detected(query):
    assert is_identifier_query(query)


@pytest.mark.parametrize(
    "query",
    [
        "",
        "   ",
        "kanban",
        "hybrid search tie break",
        "what is #1",
        "pay-6331 regression",
        "C# tips",
        "issue 2753",
    ],
)
def test_natural_language_not_identifier(query):
    assert not is_identifier_query(query)
