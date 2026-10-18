"""Service-level regression tests for `ReEmbeddingService` targeted rebuilds.

Uses an AsyncMock repository and a mocked embedding adapter, no database required.
The real-SQL counterparts live in `tests/e2e_sqlite/test_updated_at_embedding_writes_sqlite.py`.
"""
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.config.settings import settings
from app.models.memory_models import Memory
from app.services.re_embedding_service import ReEmbeddingService

SECRET_DETAIL = "[SQL: INSERT INTO vec_memories ...] [parameters: ('1', b'\\x00\\x01')] key=sk-secret"


def _make_memory(memory_id: int) -> Memory:
    return Memory(
        id=memory_id,
        title=f"Memory {memory_id}",
        content="Content",
        context="test context",
        keywords=["test"],
        tags=["test"],
        importance=7,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=memory_id),
    )


def _make_repo(memories: list[Memory]) -> AsyncMock:
    repo = AsyncMock()
    repo.count_memories_for_targeted_rebuild.return_value = len(memories)

    async def get_batch(user_id, limit, after_id=None, memory_ids=None, project_id=None):
        eligible = [memory for memory in memories if after_id is None or memory.id > after_id]
        return eligible[:limit]

    async def upsert(user_id, updates, expected_updated_at=None):
        return [memory_id for memory_id, _ in updates]

    repo.get_memories_for_targeted_rebuild.side_effect = get_batch
    repo.upsert_targeted_embeddings.side_effect = upsert
    repo.find_similar_memories.return_value = []
    repo.create_links_batch.return_value = []
    repo.project_exists_for_user.return_value = True
    return repo


def _make_adapter() -> AsyncMock:
    adapter = AsyncMock()
    adapter.generate_embedding.return_value = [0.1] * 384
    return adapter


async def test_upsert_receives_the_updated_at_observed_when_the_batch_was_read():
    memories = [_make_memory(i) for i in range(1, 4)]
    repo = _make_repo(memories)

    await ReEmbeddingService(repo, _make_adapter(), batch_size=20).rebuild_targeted(user_id=uuid4())

    repo.upsert_targeted_embeddings.assert_awaited_once()
    kwargs = repo.upsert_targeted_embeddings.await_args.kwargs
    assert kwargs["expected_updated_at"] == {memory.id: memory.updated_at for memory in memories}


async def test_rows_rejected_by_the_conditional_write_are_reported_as_skipped():
    memories = [_make_memory(i) for i in range(1, 4)]
    repo = _make_repo(memories)

    async def upsert(user_id, updates, expected_updated_at=None):
        return [memory_id for memory_id, _ in updates if memory_id != 2]  # memory 2 was edited meanwhile

    repo.upsert_targeted_embeddings.side_effect = upsert

    result = await ReEmbeddingService(repo, _make_adapter(), batch_size=20).rebuild_targeted(user_id=uuid4())

    assert result.rebuilt_ids == [1, 3]
    assert result.skipped_ids == [2]
    assert result.failed == []


async def test_embedding_failure_reports_a_stable_code_not_the_exception_text():
    memories = [_make_memory(i) for i in range(1, 4)]
    repo = _make_repo(memories)
    adapter = _make_adapter()
    calls = {"n": 0}

    async def flaky(_text):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError(f"provider rejected request {SECRET_DETAIL}")
        return [0.1] * 384

    adapter.generate_embedding.side_effect = flaky

    result = await ReEmbeddingService(repo, adapter, batch_size=20).rebuild_targeted(user_id=uuid4())

    assert sorted(result.rebuilt_ids) == [1, 3]
    assert result.failed == [{"memory_id": 2, "reason": "embedding_failed"}]


async def test_persistence_failure_blames_only_the_memory_that_cannot_be_written():
    memories = [_make_memory(i) for i in range(1, 4)]
    repo = _make_repo(memories)

    async def upsert(user_id, updates, expected_updated_at=None):
        if any(memory_id == 2 for memory_id, _ in updates):
            raise RuntimeError(f"(sqlite3.OperationalError) bad vector {SECRET_DETAIL}")
        return [memory_id for memory_id, _ in updates]

    repo.upsert_targeted_embeddings.side_effect = upsert

    result = await ReEmbeddingService(repo, _make_adapter(), batch_size=20).rebuild_targeted(user_id=uuid4())

    assert sorted(result.rebuilt_ids) == [1, 3]
    assert result.skipped_ids == []
    assert result.failed == [{"memory_id": 2, "reason": "persistence_failed"}]


async def test_retry_after_batch_failure_keeps_the_per_row_version_check():
    memories = [_make_memory(i) for i in range(1, 3)]
    repo = _make_repo(memories)
    attempts = []

    async def upsert(user_id, updates, expected_updated_at=None):
        attempts.append((len(updates), expected_updated_at))
        if len(updates) > 1:
            raise RuntimeError("batch failed")
        return [updates[0][0]]

    repo.upsert_targeted_embeddings.side_effect = upsert

    result = await ReEmbeddingService(repo, _make_adapter(), batch_size=20).rebuild_targeted(user_id=uuid4())

    assert sorted(result.rebuilt_ids) == [1, 2]
    assert attempts[1:] == [
        (1, {1: memories[0].updated_at}),
        (1, {2: memories[1].updated_at}),
    ]


async def test_auto_link_failure_reports_a_stable_code(monkeypatch):
    memories = [_make_memory(1)]
    repo = _make_repo(memories)
    repo.find_similar_memories.side_effect = RuntimeError(f"link lookup failed {SECRET_DETAIL}")
    monkeypatch.setattr(settings, "MEMORY_NUM_AUTO_LINK", 1)

    result = await ReEmbeddingService(repo, _make_adapter(), batch_size=20).rebuild_targeted(user_id=uuid4())

    assert result.rebuilt_ids == [1]
    assert result.failed == [{"memory_id": 1, "phase": "auto_link", "reason": "auto_link_failed"}]


async def test_project_scope_must_exist_and_be_owned_even_without_memory_ids():
    user_id = uuid4()
    repo = _make_repo([])
    repo.project_exists_for_user.return_value = False
    service = ReEmbeddingService(repo, _make_adapter())

    with pytest.raises(ValueError, match=r"project_id=42 not found or not owned"):
        await service.validate_targeted_scope(user_id, None, 42)

    repo.project_exists_for_user.assert_awaited_once_with(user_id=user_id, project_id=42)


async def test_owned_project_scope_is_accepted_without_memory_ids():
    repo = _make_repo([])
    service = ReEmbeddingService(repo, _make_adapter())

    await service.validate_targeted_scope(uuid4(), None, 42)


async def test_global_scope_does_not_look_up_a_project():
    repo = _make_repo([])
    service = ReEmbeddingService(repo, _make_adapter())

    await service.validate_targeted_scope(uuid4(), None, None)

    repo.project_exists_for_user.assert_not_awaited()
