"""MemoryScore JSON serialization omits hybrid fields when unset."""

import json

from app.models.memory_models import MemoryScore


def test_memory_score_omits_hybrid_fields_when_none():
    dumped = MemoryScore(memory_id=1, similarity=0.5, rerank_score=None).model_dump()
    assert set(dumped.keys()) == {"memory_id", "similarity", "rerank_score"}


def test_memory_score_includes_hybrid_fields_when_set():
    dumped = MemoryScore(
        memory_id=1,
        similarity=0.5,
        rerank_score=None,
        keyword_rank=2,
        fusion_score=0.03,
    ).model_dump()
    assert dumped["keyword_rank"] == 2
    assert dumped["fusion_score"] == 0.03


def test_memory_score_json_mode_matches_dump():
    score = MemoryScore(memory_id=1, similarity=0.5, rerank_score=None)
    assert score.model_dump(mode="json") == score.model_dump()

    hybrid = MemoryScore(
        memory_id=1,
        similarity=0.5,
        rerank_score=None,
        keyword_rank=2,
        fusion_score=0.03,
    )
    assert hybrid.model_dump(mode="json") == hybrid.model_dump()


def test_memory_score_model_dump_json_omits_hybrid_when_none():
    score = MemoryScore(memory_id=1, similarity=0.5, rerank_score=None)
    parsed = json.loads(score.model_dump_json())
    assert set(parsed.keys()) == {"memory_id", "similarity", "rerank_score"}


def test_memory_score_model_dump_json_includes_hybrid_when_set():
    score = MemoryScore(
        memory_id=1,
        similarity=0.5,
        rerank_score=None,
        keyword_rank=2,
        fusion_score=0.03,
    )
    parsed = json.loads(score.model_dump_json())
    assert parsed["keyword_rank"] == 2
    assert parsed["fusion_score"] == 0.03
