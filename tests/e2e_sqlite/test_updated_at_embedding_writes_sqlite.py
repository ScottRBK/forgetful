"""Real-SQL regression tests (in-memory SQLite) for read telemetry and embedding writes.

`record_memory_access` must not advance `updated_at` (the column `onupdate` used to fire), and a
targeted rebuild must leave it alone too. Uses a deterministic offline embedding adapter.
"""
import asyncio
import hashlib
import random
from uuid import uuid4

import pytest

from app.config.settings import settings
from app.models.memory_models import MemoryCreate
from app.models.user_models import UserCreate
from app.repositories.sqlite.memory_repository import SqliteMemoryRepository
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter
from app.repositories.sqlite.user_repository import SqliteUserRepository
from app.services.re_embedding_service import ReEmbeddingService

DIMS = 384


class StaticEmbeddingAdapter:
    """Deterministic, offline embedding adapter."""

    @staticmethod
    def vector(text_: str) -> list[float]:
        rng = random.Random(int(hashlib.md5(text_.encode()).hexdigest()[:8], 16))
        vec = [rng.random() for _ in range(DIMS)]
        magnitude = sum(x * x for x in vec) ** 0.5 or 1.0
        return [x / magnitude for x in vec]

    async def generate_embedding(self, text: str) -> list[float]:
        return self.vector(text)


@pytest.fixture
async def stack():
    saved = (
        settings.DATABASE,
        settings.SQLITE_MEMORY,
        settings.EMBEDDING_DIMENSIONS,
        settings.MEMORY_NUM_AUTO_LINK,
    )
    settings.DATABASE = "SQLite"
    settings.SQLITE_MEMORY = True
    settings.EMBEDDING_DIMENSIONS = DIMS
    settings.MEMORY_NUM_AUTO_LINK = 0

    db_adapter = SqliteDatabaseAdapter()
    await db_adapter.init_db()
    embedder = StaticEmbeddingAdapter()
    repo = SqliteMemoryRepository(db_adapter=db_adapter, embedding_adapter=embedder, rerank_adapter=None)
    users = SqliteUserRepository(db_adapter=db_adapter)
    user = await users.create_user(UserCreate(external_id=f"ext-{uuid4()}", name="u", email="u@example.com"))
    try:
        yield repo, db_adapter, embedder, user.id
    finally:
        try:
            await db_adapter.dispose()
        except Exception:  # noqa: BLE001
            pass
        (
            settings.DATABASE,
            settings.SQLITE_MEMORY,
            settings.EMBEDDING_DIMENSIONS,
            settings.MEMORY_NUM_AUTO_LINK,
        ) = saved


def _memory(content: str) -> MemoryCreate:
    return MemoryCreate(
        title="T",
        content=content,
        context="c",
        keywords=["k"],
        tags=["t"],
        importance=5,
    )


# ---------------------------------------------------------------------------
# updated_at must not move on telemetry or derived-data writes
# ---------------------------------------------------------------------------


async def test_record_memory_access_does_not_change_updated_at(stack):
    repo, _db, _embedder, user_id = stack
    memory = await repo.create_memory(user_id, _memory("content"))
    before = await repo.get_memory_by_id(user_id, memory.id)
    assert before.access_count == 0

    await asyncio.sleep(0.05)
    assert await repo.record_memory_access(user_id, [memory.id]) == 1

    after = await repo.get_memory_by_id(user_id, memory.id)
    assert after.access_count == 1
    assert after.last_accessed_at is not None
    assert after.updated_at == before.updated_at


async def test_targeted_rebuild_does_not_change_updated_at(stack):
    repo, _db, embedder, user_id = stack
    memory = await repo.create_memory(user_id, _memory("content"))
    before = await repo.get_memory_by_id(user_id, memory.id)

    await asyncio.sleep(0.05)
    result = await ReEmbeddingService(repo, embedder).rebuild_targeted(user_id=user_id)

    assert result.rebuilt_ids == [memory.id]
    assert (await repo.get_memory_by_id(user_id, memory.id)).updated_at == before.updated_at
