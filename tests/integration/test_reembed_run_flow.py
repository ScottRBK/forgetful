"""Integration tests for the full re-embed run: storage reset, constraints and skills.

Uses mocked repositories and embedding adapter, so no real database is required.
"""
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.models.memory_models import Memory
from app.services.re_embedding_service import ReEmbeddingService


def _memory(memory_id: int) -> Memory:
    return Memory(
        id=memory_id,
        title=f"Memory {memory_id}",
        content="Content",
        context="context",
        keywords=["k"],
        tags=["t"],
        importance=7,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _memory_repo(memories: list[Memory]):
    repo = AsyncMock()
    repo.count_all_memories.return_value = len(memories)

    async def batch(limit: int, offset: int):
        return memories[offset:offset + limit]

    repo.get_memories_for_reembedding.side_effect = batch
    repo.validate_embedding_count.return_value = True
    repo.validate_embedding_dimensions.return_value = True
    repo.validate_search_works.return_value = True
    return repo


def _embedder():
    adapter = AsyncMock()
    adapter.generate_embedding.return_value = [0.1] * 8
    return adapter


async def test_empty_database_still_resets_vector_storage():
    """A dimension change on a database without memories must still resize the vector storage."""
    memory_repo = _memory_repo([])
    embedder = _embedder()

    result = await ReEmbeddingService(memory_repo, embedder).re_embed_all()

    memory_repo.reset_embedding_storage.assert_awaited_once()
    memory_repo.bulk_update_embeddings.assert_not_called()
    embedder.generate_embedding.assert_not_called()
    assert (result.total_memories, result.total_processed) == (0, 0)
    assert result.validation is not None
    assert result.validation.all_passed


async def test_constraints_are_restored_only_after_validation_passes():
    memory_repo = _memory_repo([_memory(1)])
    calls: list[str] = []

    async def validate():
        calls.append("validate")
        return True

    async def finalize():
        calls.append("finalize")

    memory_repo.validate_search_works.side_effect = validate
    memory_repo.finalize_embedding_storage.side_effect = finalize

    await ReEmbeddingService(memory_repo, _embedder()).re_embed_all()

    assert calls == ["validate", "finalize"]


async def test_failed_validation_keeps_constraints_relaxed():
    memory_repo = _memory_repo([_memory(1)])
    memory_repo.validate_embedding_count.return_value = False

    result = await ReEmbeddingService(memory_repo, _embedder()).re_embed_all()

    assert not result.validation.all_passed
    memory_repo.finalize_embedding_storage.assert_not_called()


async def test_failed_run_never_restores_constraints():
    memory_repo = _memory_repo([_memory(1), _memory(2)])
    embedder = _embedder()
    embedder.generate_embedding.side_effect = [[0.1] * 8, RuntimeError("provider down")]

    with pytest.raises(RuntimeError, match="provider down"):
        await ReEmbeddingService(memory_repo, embedder, batch_size=1).re_embed_all()

    memory_repo.finalize_embedding_storage.assert_not_called()
