"""Integration tests for ReEmbeddingService.

Uses mocked embedding adapter and in-memory stubs — no real database required.
"""
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.config.settings import settings
from app.models.memory_models import Memory
from app.services.re_embedding_service import ReEmbeddingService


def _make_memory(memory_id: int, title: str = "Test", content: str = "Content") -> Memory:
    """Helper to create a Memory object for testing"""
    return Memory(
        id=memory_id,
        title=title,
        content=content,
        context="test context",
        keywords=["test"],
        tags=["test"],
        importance=7,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_mock_repo(memories: list[Memory]):
    """Create a mock MemoryRepository with re-embedding methods"""
    repo = AsyncMock()
    repo.count_all_memories.return_value = len(memories)

    # get_memories_for_reembedding returns slices of the memory list
    async def get_batch(limit: int, offset: int):
        return memories[offset:offset + limit]

    repo.get_memories_for_reembedding.side_effect = get_batch
    repo.reset_embedding_storage.return_value = None
    repo.bulk_update_embeddings.return_value = None
    repo.validate_embedding_count.return_value = True
    repo.validate_embedding_dimensions.return_value = True
    repo.validate_search_works.return_value = True
    return repo


def _make_mock_adapter(dimensions: int = 384):
    """Create a mock EmbeddingsAdapter"""
    adapter = AsyncMock()
    adapter.generate_embedding.return_value = [0.1] * dimensions
    return adapter


@pytest.mark.asyncio
async def test_re_embed_processes_all_memories():
    """Verify every memory gets a new embedding"""
    memories = [_make_memory(i, title=f"Memory {i}") for i in range(1, 6)]
    repo = _make_mock_repo(memories)
    adapter = _make_mock_adapter()

    service = ReEmbeddingService(repo, adapter, batch_size=20)
    result = await service.re_embed_all()

    assert result.total_processed == 5
    assert result.total_memories == 5
    assert adapter.generate_embedding.call_count == 5
    repo.bulk_update_embeddings.assert_called_once()

    # Verify all memory IDs were included in the update
    call_args = repo.bulk_update_embeddings.call_args[0][0]
    updated_ids = {mid for mid, _ in call_args}
    assert updated_ids == {1, 2, 3, 4, 5}


@pytest.mark.asyncio
async def test_re_embed_respects_batch_size():
    """Verify batching with various sizes"""
    memories = [_make_memory(i) for i in range(1, 21)]
    repo = _make_mock_repo(memories)
    adapter = _make_mock_adapter()

    service = ReEmbeddingService(repo, adapter, batch_size=5)
    result = await service.re_embed_all()

    assert result.total_processed == 20
    # Should have 4 batches of 5
    assert repo.bulk_update_embeddings.call_count == 4
    assert adapter.generate_embedding.call_count == 20


@pytest.mark.asyncio
async def test_re_embed_partial_batch():
    """7 memories with batch_size=5 -> 2 batches"""
    memories = [_make_memory(i) for i in range(1, 8)]
    repo = _make_mock_repo(memories)
    adapter = _make_mock_adapter()

    service = ReEmbeddingService(repo, adapter, batch_size=5)
    result = await service.re_embed_all()

    assert result.total_processed == 7
    assert repo.bulk_update_embeddings.call_count == 2

    # First batch: 5 items, second batch: 2 items
    first_batch = repo.bulk_update_embeddings.call_args_list[0][0][0]
    second_batch = repo.bulk_update_embeddings.call_args_list[1][0][0]
    assert len(first_batch) == 5
    assert len(second_batch) == 2


@pytest.mark.asyncio
async def test_re_embed_empty_database():
    """0 memories -> success with no work done"""
    repo = _make_mock_repo([])
    adapter = _make_mock_adapter()

    service = ReEmbeddingService(repo, adapter, batch_size=20)
    result = await service.re_embed_all()

    assert result.total_processed == 0
    assert result.total_memories == 0
    assert result.validation.all_passed
    # Should not call reset or bulk_update
    repo.reset_embedding_storage.assert_not_called()
    repo.bulk_update_embeddings.assert_not_called()
    adapter.generate_embedding.assert_not_called()


@pytest.mark.asyncio
async def test_re_embed_progress_callback():
    """Verify progress callback fires per batch"""
    memories = [_make_memory(i) for i in range(1, 8)]
    repo = _make_mock_repo(memories)
    adapter = _make_mock_adapter()

    progress_calls = []

    def progress_cb(processed, total):
        progress_calls.append((processed, total))

    service = ReEmbeddingService(repo, adapter, batch_size=3)
    result = await service.re_embed_all(progress_callback=progress_cb)

    assert result.total_processed == 7
    # batch_size=3, 7 items -> batches of 3, 3, 1
    assert len(progress_calls) == 3
    assert progress_calls[0] == (3, 7)
    assert progress_calls[1] == (6, 7)
    assert progress_calls[2] == (7, 7)


@pytest.mark.asyncio
async def test_re_embed_adapter_error_propagates():
    """Embedding adapter throws -> error raised"""
    memories = [_make_memory(1)]
    repo = _make_mock_repo(memories)
    adapter = _make_mock_adapter()
    adapter.generate_embedding.side_effect = RuntimeError("API rate limit exceeded")

    service = ReEmbeddingService(repo, adapter, batch_size=20)

    with pytest.raises(RuntimeError, match="API rate limit exceeded"):
        await service.re_embed_all()


@pytest.mark.asyncio
async def test_re_embed_calls_reset_before_embedding():
    """Verify reset_embedding_storage is called before bulk_update_embeddings"""
    memories = [_make_memory(1)]
    repo = _make_mock_repo(memories)
    adapter = _make_mock_adapter()

    call_order = []

    async def track_reset():
        call_order.append("reset")
    async def track_bulk(updates):
        call_order.append("bulk")

    repo.reset_embedding_storage.side_effect = track_reset
    repo.bulk_update_embeddings.side_effect = track_bulk

    service = ReEmbeddingService(repo, adapter, batch_size=20)
    await service.re_embed_all()

    assert call_order == ["reset", "bulk"]


@pytest.mark.asyncio
async def test_re_embed_validation_failure():
    """Verify validation result reflects failures"""
    memories = [_make_memory(1)]
    repo = _make_mock_repo(memories)
    repo.validate_embedding_count.return_value = False
    adapter = _make_mock_adapter()

    service = ReEmbeddingService(repo, adapter, batch_size=20)
    result = await service.re_embed_all()

    assert result.validation is not None
    assert not result.validation.count_ok
    assert result.validation.dimensions_ok
    assert result.validation.search_ok
    assert not result.validation.all_passed


# ---------------------------------------------------------------------------
# rebuild_targeted (issue #39) — user-scoped, non-destructive rebuild
# ---------------------------------------------------------------------------


def _make_targeted_repo(memories: list[Memory], owned_by_user: bool = True):
    """Mock repo wired for rebuild_targeted (no reset, user-scoped upsert)."""
    repo = AsyncMock()
    repo.count_memories_for_targeted_rebuild.return_value = len(memories)

    async def get_batch(user_id, limit, after_id=None, memory_ids=None,
                        project_id=None):
        eligible = memories
        if after_id is not None:
            eligible = [memory for memory in eligible if memory.id > after_id]
        return eligible[:limit]

    async def upsert_targeted(user_id, updates):
        return [mid for mid, _ in updates] if owned_by_user else []

    repo.get_memories_for_targeted_rebuild.side_effect = get_batch
    repo.upsert_targeted_embeddings.side_effect = upsert_targeted
    repo.find_similar_memories.return_value = []
    repo.create_links_batch.return_value = []
    return repo


@pytest.mark.asyncio
async def test_rebuild_targeted_does_not_reset_storage():
    """rebuild_targeted must never call reset_embedding_storage()."""
    from uuid import uuid4

    memories = [_make_memory(i) for i in range(1, 4)]
    repo = _make_targeted_repo(memories)
    adapter = _make_mock_adapter()

    service = ReEmbeddingService(repo, adapter, batch_size=20)
    result = await service.rebuild_targeted(user_id=uuid4())

    repo.reset_embedding_storage.assert_not_called()
    assert sorted(result.rebuilt_ids) == [1, 2, 3]
    assert result.skipped_ids == []
    assert result.failed == []


@pytest.mark.asyncio
async def test_rebuild_targeted_no_candidates_short_circuits():
    """Empty candidate set -> no embedding work, empty result."""
    from uuid import uuid4

    repo = _make_targeted_repo([])
    adapter = _make_mock_adapter()

    service = ReEmbeddingService(repo, adapter, batch_size=20)
    result = await service.rebuild_targeted(user_id=uuid4())

    assert result.rebuilt_ids == []
    adapter.generate_embedding.assert_not_called()
    repo.upsert_targeted_embeddings.assert_not_called()


@pytest.mark.asyncio
async def test_rebuild_targeted_skips_unowned_ids():
    """Memories rejected by upsert (not owned) land in skipped_ids."""
    from uuid import uuid4

    memories = [_make_memory(i) for i in range(1, 4)]
    repo = _make_mock_repo([])  # not used directly
    repo.count_memories_for_targeted_rebuild.return_value = len(memories)

    async def get_batch(user_id, limit, after_id=None, memory_ids=None,
                        project_id=None):
        eligible = memories
        if after_id is not None:
            eligible = [memory for memory in eligible if memory.id > after_id]
        return eligible[:limit]

    async def partial_upsert(user_id, updates):
        return [updates[0][0]]  # Only the first id is owned

    repo.get_memories_for_targeted_rebuild.side_effect = get_batch
    repo.upsert_targeted_embeddings.side_effect = partial_upsert
    repo.find_similar_memories.return_value = []
    repo.create_links_batch.return_value = []
    adapter = _make_mock_adapter()

    service = ReEmbeddingService(repo, adapter, batch_size=20)
    result = await service.rebuild_targeted(user_id=uuid4())

    assert result.rebuilt_ids == [1]
    assert sorted(result.skipped_ids) == [2, 3]
    assert result.failed == []


@pytest.mark.asyncio
async def test_rebuild_targeted_records_embedding_failures():
    """Per-memory embedding error -> entry in result.failed, others succeed."""
    from uuid import uuid4

    memories = [_make_memory(i) for i in range(1, 4)]
    repo = _make_targeted_repo(memories)
    adapter = _make_mock_adapter()

    call_count = {"n": 0}

    async def flaky_embedding(_text):
        call_count["n"] += 1
        if call_count["n"] == 2:
            raise RuntimeError("transient API failure")
        return [0.1] * 384

    adapter.generate_embedding.side_effect = flaky_embedding

    service = ReEmbeddingService(repo, adapter, batch_size=20)
    result = await service.rebuild_targeted(user_id=uuid4())

    assert sorted(result.rebuilt_ids) == [1, 3]
    assert len(result.failed) == 1
    assert result.failed[0]["memory_id"] == 2
    assert "transient API failure" in result.failed[0]["reason"]


@pytest.mark.asyncio
async def test_rebuild_targeted_recomputes_auto_links(monkeypatch):
    """After writing fresh vectors, targeted rebuild refreshes additive auto-links."""
    from uuid import uuid4

    user_id = uuid4()
    memories = [_make_memory(i) for i in range(1, 3)]
    repo = _make_targeted_repo(memories)
    repo.find_similar_memories.return_value = [memories[1]]
    repo.create_links_batch.return_value = [memories[1].id]
    adapter = _make_mock_adapter()
    monkeypatch.setattr(settings, "MEMORY_NUM_AUTO_LINK", 1)

    service = ReEmbeddingService(repo, adapter, batch_size=20)
    result = await service.rebuild_targeted(user_id=user_id)

    assert sorted(result.rebuilt_ids) == [1, 2]
    assert repo.find_similar_memories.call_count == 2
    assert repo.create_links_batch.call_count == 2
    repo.find_similar_memories.assert_any_call(
        user_id=user_id,
        memory_id=1,
        max_links=1,
    )
