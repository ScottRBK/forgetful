"""SQLite regression: recording a read must not move `updated_at`.

Access tracking updates `access_count` and `last_accessed_at` only. The
`onupdate` callback of the table would otherwise advance `updated_at` on
every read, moving a memory in an "updated" sort or filter without a
content edit.
"""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import text

from app.config.settings import settings
from app.models.memory_models import MemoryCreate
from app.repositories.sqlite.memory_repository import SqliteMemoryRepository
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter

DIMS = 384


class FakeEmbeddingAdapter:
    """Deterministic offline embedder so the repository runs without a model."""

    async def generate_embedding(self, text: str) -> list[float]:
        vec = [0.0] * DIMS
        vec[len(text) % DIMS] = 1.0
        return vec


@pytest.fixture
async def repo_and_db():
    original = (
        settings.DATABASE,
        settings.SQLITE_MEMORY,
        settings.EMBEDDING_DIMENSIONS,
    )
    settings.DATABASE = "SQLite"
    settings.SQLITE_MEMORY = True
    settings.EMBEDDING_DIMENSIONS = DIMS
    db_adapter = SqliteDatabaseAdapter()
    await db_adapter.init_db()
    repo = SqliteMemoryRepository(
        db_adapter=db_adapter,
        embedding_adapter=FakeEmbeddingAdapter(),
        rerank_adapter=None,
    )
    try:
        yield repo, db_adapter
    finally:
        await db_adapter.dispose()
        settings.DATABASE, settings.SQLITE_MEMORY, settings.EMBEDDING_DIMENSIONS = (
            original
        )


async def _create_user(db_adapter, user_id: UUID) -> None:
    async with db_adapter.system_session() as session:
        await session.execute(
            text(
                "INSERT INTO users (id, external_id, name, email, created_at, updated_at) "
                "VALUES (:id, :external_id, :name, :email, :created_at, :updated_at)",
            ),
            {
                "id": str(user_id),
                "external_id": f"ext-{user_id}",
                "name": "User",
                "email": f"{user_id}@example.test",
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
            },
        )


def _memory(title: str) -> MemoryCreate:
    return MemoryCreate(
        title=title,
        content=f"{title} content",
        context="access tracking test",
        keywords=["access-tracking"],
        tags=["access"],
        importance=5,
    )


@pytest.mark.asyncio
async def test_record_memory_access_does_not_move_updated_at(repo_and_db):
    """A read bumps access_count and last_accessed_at, never updated_at."""
    repo, db = repo_and_db
    user = uuid4()
    await _create_user(db, user)
    created = await repo.create_memory(user, _memory("Read tracked memory"))
    stored = await repo.get_memory_by_id(user, created.id)
    assert stored is not None
    assert stored.access_count == 0
    updated_at_before = stored.updated_at

    count = await repo.record_memory_access(user, [created.id])
    assert count == 1

    refreshed = await repo.get_memory_by_id(user, created.id)
    assert refreshed is not None
    assert refreshed.access_count == 1
    assert refreshed.last_accessed_at is not None
    assert refreshed.updated_at == updated_at_before, (
        "updated_at must not move on access"
    )


@pytest.mark.asyncio
async def test_record_memory_access_keeps_updated_order(repo_and_db):
    """Reading an older memory must not move it to the top of an updated sort."""
    repo, db = repo_and_db
    user = uuid4()
    await _create_user(db, user)
    older = await repo.create_memory(user, _memory("Older memory"))
    newer = await repo.create_memory(user, _memory("Newer memory"))

    await repo.record_memory_access(user, [older.id])

    memories, _ = await repo.list_memories(user, limit=10, sort_by="updated_at")
    assert [memory.id for memory in memories] == [newer.id, older.id]
