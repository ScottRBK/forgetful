"""Real-SQL regression tests (in-memory SQLite) for read telemetry and targeted embedding rebuilds.

`record_memory_access` must not advance `updated_at` (the column `onupdate` used to fire), a targeted
rebuild must leave it alone too, and `rebuild_embeddings(project_id=...)` must reject unknown or
foreign projects. Uses a deterministic offline embedding adapter.
"""
import asyncio
import hashlib
import random
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastmcp.exceptions import ToolError
from sqlalchemy import text

from app.config.settings import settings
from app.models.memory_models import MemoryCreate
from app.models.user_models import User, UserCreate
from app.repositories.sqlite.memory_repository import SqliteMemoryRepository
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter
from app.repositories.sqlite.user_repository import SqliteUserRepository
from app.routes.mcp.tool_adapters import MemoryToolAdapters
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


def _memory(content: str, project_id: int | None = None) -> MemoryCreate:
    return MemoryCreate(
        title="T",
        content=content,
        context="c",
        keywords=["k"],
        tags=["t"],
        importance=5,
        project_ids=[project_id] if project_id else [],
    )


async def _vec_blob(db_adapter, memory_id: int):
    async with db_adapter.system_session() as session:
        return (
            await session.execute(
                text("SELECT embedding FROM vec_memories WHERE memory_id = :memory_id"),
                {"memory_id": str(memory_id)},
            )
        ).scalar_one_or_none()


async def _create_project(db_adapter, user_id, name="P"):
    now = datetime.now(UTC).isoformat()
    async with db_adapter.system_session() as session:
        result = await session.execute(
            text(
                "INSERT INTO projects (user_id, name, description, project_type, status, created_at, updated_at) "
                "VALUES (:user_id, :name, 'd', 'development', 'active', :now, :now) RETURNING id",
            ),
            {"user_id": str(user_id), "name": name, "now": now},
        )
        return result.scalar_one()


async def _create_other_user(db_adapter):
    users = SqliteUserRepository(db_adapter=db_adapter)
    user = await users.create_user(UserCreate(external_id=f"ext-{uuid4()}", name="o", email="o@example.com"))
    return user.id


def _tool_adapters(repo, embedder, user_id):
    class FakeUserService:
        async def get_or_create_user(self, user):
            return User(id=user_id, external_id=user.external_id, name=user.name, email=user.email)

    user_service = FakeUserService()
    ctx = SimpleNamespace(fastmcp=SimpleNamespace(auth=None, user_service=user_service))
    adapters = MemoryToolAdapters(
        memory_service=SimpleNamespace(),
        user_service=user_service,
        re_embedding_service=ReEmbeddingService(repo, embedder),
    )
    return ctx, adapters


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


# ---------------------------------------------------------------------------
# project scope validation
# ---------------------------------------------------------------------------


async def test_rebuild_embeddings_rejects_nonexistent_project(stack):
    repo, db_adapter, embedder, user_id = stack
    project_id = await _create_project(db_adapter, user_id)
    await repo.create_memory(user_id, _memory("content", project_id))
    ctx, adapters = _tool_adapters(repo, embedder, user_id)

    with pytest.raises(ToolError, match=r"VALIDATION_ERROR: project_id=999 not found or not owned"):
        await adapters.rebuild_embeddings(ctx, project_id=999)


async def test_rebuild_embeddings_rejects_foreign_project_without_rebuilding(stack):
    repo, db_adapter, embedder, user_id = stack
    owner_id = await _create_other_user(db_adapter)
    project_id = await _create_project(db_adapter, owner_id, name="owner project")
    owner_memory = await repo.create_memory(owner_id, _memory("owner content", project_id))
    before = await _vec_blob(db_adapter, owner_memory.id)
    ctx, adapters = _tool_adapters(repo, embedder, user_id)

    with pytest.raises(ToolError, match=rf"project_id={project_id} not found or not owned"):
        await adapters.rebuild_embeddings(ctx, project_id=project_id)

    assert await _vec_blob(db_adapter, owner_memory.id) == before


async def test_rebuild_embeddings_accepts_owned_project_with_and_without_memories(stack):
    repo, db_adapter, embedder, user_id = stack
    empty_project = await _create_project(db_adapter, user_id, name="empty")
    used_project = await _create_project(db_adapter, user_id, name="used")
    memory = await repo.create_memory(user_id, _memory("content", used_project))
    ctx, adapters = _tool_adapters(repo, embedder, user_id)

    empty = await adapters.rebuild_embeddings(ctx, project_id=empty_project)
    used = await adapters.rebuild_embeddings(ctx, project_id=used_project)

    assert empty == {"rebuilt_ids": [], "skipped_ids": [], "failed": []}
    assert used == {"rebuilt_ids": [memory.id], "skipped_ids": [], "failed": []}
