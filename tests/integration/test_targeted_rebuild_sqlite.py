"""Integration tests for targeted rebuild on a real (in-memory) SQLite stack.

Unlike `tests/e2e_sqlite/test_re_embedding_sqlite.py`, this module never
downloads a FastEmbed model; it runs offline using a deterministic mock
embedding adapter so CI and offline laptops can exercise the persistence
layer of the new `rebuild_embeddings` MCP tool (issue #39).
"""
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
from app.models.user_models import User
from app.repositories.sqlite.memory_repository import SqliteMemoryRepository
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter
from app.routes.mcp.tool_adapters import MemoryToolAdapters
from app.services.re_embedding_service import ReEmbeddingService


class StaticEmbeddingAdapter:
    """Deterministic, fully offline embedding adapter for SQLite-vec tests."""

    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions

    async def generate_embedding(self, text: str) -> list[float]:
        seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)
        vec = [rng.random() for _ in range(self.dimensions)]
        magnitude = sum(x * x for x in vec) ** 0.5 or 1.0
        return [x / magnitude for x in vec]


@pytest.fixture
async def sqlite_repo():
    original_sqlite_memory = settings.SQLITE_MEMORY
    original_database = settings.DATABASE
    original_dims = settings.EMBEDDING_DIMENSIONS

    settings.DATABASE = "SQLite"
    settings.SQLITE_MEMORY = True
    settings.EMBEDDING_DIMENSIONS = 384

    db_adapter = SqliteDatabaseAdapter()
    await db_adapter.init_db()

    embedding_adapter = StaticEmbeddingAdapter(dimensions=384)
    repo = SqliteMemoryRepository(
        db_adapter=db_adapter,
        embedding_adapter=embedding_adapter,
        rerank_adapter=None,
    )

    try:
        yield repo, db_adapter, embedding_adapter
    finally:
        try:
            await db_adapter.dispose()
        except Exception:  # noqa: BLE001
            pass
        settings.DATABASE = original_database
        settings.SQLITE_MEMORY = original_sqlite_memory
        settings.EMBEDDING_DIMENSIONS = original_dims


async def _create_user(db_adapter, user_id):
    now = datetime.now(UTC).isoformat()
    async with db_adapter.system_session() as session:
        await session.execute(
            text(
                "INSERT INTO users (id, external_id, name, email, created_at, updated_at) "
                "VALUES (:id, :external_id, :name, :email, :created_at, :updated_at)",
            ),
            {
                "id": str(user_id),
                "external_id": f"ext-{user_id}",
                "name": "Test User",
                "email": "test@example.com",
                "created_at": now,
                "updated_at": now,
            },
        )


async def _create_project(db_adapter, user_id, name="Test Project"):
    now = datetime.now(UTC).isoformat()
    async with db_adapter.system_session() as session:
        result = await session.execute(
            text(
                "INSERT INTO projects (user_id, name, description, project_type, status, created_at, updated_at) "
                "VALUES (:user_id, :name, :description, :project_type, :status, :created_at, :updated_at) "
                "RETURNING id",
            ),
            {
                "user_id": str(user_id),
                "name": name,
                "description": "Test project",
                "project_type": "development",
                "status": "active",
                "created_at": now,
                "updated_at": now,
            },
        )
        return result.scalar_one()


def _make_ctx(user_id):
    class FakeUserService:
        async def get_or_create_user(self, user):
            return User(
                id=user_id,
                external_id=user.external_id,
                name=user.name,
                email=user.email,
            )

    user_service = FakeUserService()
    return SimpleNamespace(
        fastmcp=SimpleNamespace(
            auth=None,
            user_service=user_service,
        ),
    ), user_service


async def _seed_memories(repo, db_adapter, count=3):
    user_id = uuid4()
    await _create_user(db_adapter, user_id)
    memories = []
    for i in range(count):
        memory = await repo.create_memory(
            user_id=user_id,
            memory=MemoryCreate(
                title=f"M{i}",
                content=f"content {i}",
                context=f"ctx {i}",
                keywords=[f"k{i}"],
                tags=[f"t{i}"],
                importance=5,
            ),
        )
        memories.append(memory)
    return user_id, memories


async def _vec_count(db_adapter) -> int:
    async with db_adapter.system_session() as session:
        return (await session.execute(text("SELECT COUNT(*) FROM vec_memories"))).scalar() or 0


async def _vec_blob(db_adapter, memory_id: int):
    async with db_adapter.system_session() as session:
        return (
            await session.execute(
                text("SELECT embedding FROM vec_memories WHERE memory_id = :memory_id"),
                {"memory_id": str(memory_id)},
            )
        ).scalar_one_or_none()


@pytest.mark.asyncio
async def test_rebuild_targeted_is_user_scoped(sqlite_repo):
    repo, db_adapter, embedding_adapter = sqlite_repo
    user_a, memories_a = await _seed_memories(repo, db_adapter, count=2)
    user_b, _memories_b = await _seed_memories(repo, db_adapter, count=2)

    target = memories_a[0]
    async with db_adapter.system_session() as session:
        await session.execute(
            text("DELETE FROM vec_memories WHERE memory_id = :memory_id"),
            {"memory_id": str(target.id)},
        )

    service = ReEmbeddingService(
        memory_repository=repo,
        embedding_adapter=embedding_adapter,
        batch_size=10,
    )

    result_b = await service.rebuild_targeted(
        user_id=user_b,
        memory_ids=[target.id],
    )
    assert result_b.rebuilt_ids == []

    result_a = await service.rebuild_targeted(user_id=user_a)
    assert sorted(result_a.rebuilt_ids) == sorted(memory.id for memory in memories_a)


@pytest.mark.asyncio
async def test_rebuild_targeted_does_not_call_reset(sqlite_repo, monkeypatch):
    repo, db_adapter, embedding_adapter = sqlite_repo
    user_id, _memories = await _seed_memories(repo, db_adapter, count=2)

    reset_calls = {"n": 0}
    original_reset = repo.reset_embedding_storage

    async def patched_reset():
        reset_calls["n"] += 1
        await original_reset()

    monkeypatch.setattr(repo, "reset_embedding_storage", patched_reset)

    service = ReEmbeddingService(
        memory_repository=repo,
        embedding_adapter=embedding_adapter,
        batch_size=5,
    )
    await service.rebuild_targeted(user_id=user_id)

    assert reset_calls["n"] == 0
    assert await _vec_count(db_adapter) == 2


@pytest.mark.asyncio
async def test_upsert_targeted_embeddings_rejects_unowned_ids(sqlite_repo):
    repo, db_adapter, embedding_adapter = sqlite_repo
    user_a, memories_a = await _seed_memories(repo, db_adapter, count=1)
    user_b, memories_b = await _seed_memories(repo, db_adapter, count=1)

    fake_vector = await embedding_adapter.generate_embedding("anything")

    written = await repo.upsert_targeted_embeddings(
        user_id=user_a,
        updates=[(memories_b[0].id, fake_vector)],
    )
    assert written == []

    written = await repo.upsert_targeted_embeddings(
        user_id=user_a,
        updates=[(memories_a[0].id, fake_vector)],
    )
    assert written == [memories_a[0].id]


@pytest.mark.asyncio
async def test_rebuild_targeted_recomputes_auto_links(sqlite_repo, monkeypatch):
    repo, db_adapter, embedding_adapter = sqlite_repo
    user_id, memories = await _seed_memories(repo, db_adapter, count=2)
    monkeypatch.setattr(settings, "MEMORY_NUM_AUTO_LINK", 1)

    find_calls = []
    create_calls = []
    original_find = repo.find_similar_memories
    original_create = repo.create_links_batch

    async def tracked_find_similar_memories(*args, **kwargs):
        find_calls.append((args, kwargs))
        return await original_find(*args, **kwargs)

    async def tracked_create_links_batch(*args, **kwargs):
        create_calls.append((args, kwargs))
        return await original_create(*args, **kwargs)

    monkeypatch.setattr(repo, "find_similar_memories", tracked_find_similar_memories)
    monkeypatch.setattr(repo, "create_links_batch", tracked_create_links_batch)

    service = ReEmbeddingService(
        memory_repository=repo,
        embedding_adapter=embedding_adapter,
        batch_size=10,
    )
    result = await service.rebuild_targeted(user_id=user_id, memory_ids=[memories[0].id])

    assert result.rebuilt_ids == [memories[0].id]
    assert len(find_calls) == 1
    assert find_calls[0][1]["memory_id"] == memories[0].id
    assert create_calls


@pytest.mark.asyncio
async def test_rebuild_targeted_multibatch_rebuilds_all_explicit_ids(sqlite_repo):
    repo, db_adapter, embedding_adapter = sqlite_repo
    user_id, memories = await _seed_memories(repo, db_adapter, count=5)

    service = ReEmbeddingService(
        memory_repository=repo,
        embedding_adapter=embedding_adapter,
        batch_size=2,
    )
    result = await service.rebuild_targeted(
        user_id=user_id,
        memory_ids=[memory.id for memory in memories],
    )

    assert sorted(result.rebuilt_ids) == sorted(memory.id for memory in memories)
    assert result.failed == []


@pytest.mark.asyncio
async def test_upsert_targeted_embeddings_leaves_foreign_vector_unchanged(sqlite_repo):
    repo, db_adapter, embedding_adapter = sqlite_repo
    user_a, _memories_a = await _seed_memories(repo, db_adapter, count=1)
    _user_b, memories_b = await _seed_memories(repo, db_adapter, count=1)
    foreign_memory = memories_b[0]
    original_blob = await _vec_blob(db_adapter, foreign_memory.id)

    fake_vector = await embedding_adapter.generate_embedding("foreign overwrite attempt")
    written = await repo.upsert_targeted_embeddings(
        user_id=user_a,
        updates=[(foreign_memory.id, fake_vector)],
    )

    assert written == []
    assert await _vec_blob(db_adapter, foreign_memory.id) == original_blob


@pytest.mark.asyncio
async def test_rebuild_targeted_recomputes_links_after_upsert(sqlite_repo, monkeypatch):
    repo, db_adapter, embedding_adapter = sqlite_repo
    user_id, memories = await _seed_memories(repo, db_adapter, count=2)
    monkeypatch.setattr(settings, "MEMORY_NUM_AUTO_LINK", 1)

    order = []
    original_upsert = repo.upsert_targeted_embeddings
    original_find = repo.find_similar_memories

    async def tracked_upsert(*args, **kwargs):
        order.append("upsert")
        return await original_upsert(*args, **kwargs)

    async def tracked_find(*args, **kwargs):
        order.append("find")
        assert order[-2] == "upsert"
        assert await _vec_blob(db_adapter, kwargs["memory_id"]) is not None
        return await original_find(*args, **kwargs)

    monkeypatch.setattr(repo, "upsert_targeted_embeddings", tracked_upsert)
    monkeypatch.setattr(repo, "find_similar_memories", tracked_find)

    service = ReEmbeddingService(
        memory_repository=repo,
        embedding_adapter=embedding_adapter,
        batch_size=10,
    )
    result = await service.rebuild_targeted(user_id=user_id, memory_ids=[memories[0].id])

    assert result.rebuilt_ids == [memories[0].id]
    assert order == ["upsert", "find"]


@pytest.mark.asyncio
async def test_rebuild_embeddings_rejects_empty_memory_ids(sqlite_repo):
    repo, _db_adapter, _embedding_adapter = sqlite_repo
    user_id = uuid4()
    ctx, user_service = _make_ctx(user_id)
    adapters = MemoryToolAdapters(
        memory_service=SimpleNamespace(memory_repo=repo),
        user_service=user_service,
    )

    with pytest.raises(ToolError, match="memory_ids must be non-empty"):
        await adapters.rebuild_embeddings(ctx=ctx, memory_ids=[])


@pytest.mark.asyncio
async def test_rebuild_embeddings_rejects_mismatched_memory_ids_and_project_id(sqlite_repo):
    repo, db_adapter, _embedding_adapter = sqlite_repo
    user_id = uuid4()
    await _create_user(db_adapter, user_id)
    project_a = await _create_project(db_adapter, user_id, name="A")
    project_b = await _create_project(db_adapter, user_id, name="B")
    memory = await repo.create_memory(
        user_id=user_id,
        memory=MemoryCreate(
            title="Scoped memory",
            content="content",
            context="ctx",
            keywords=["k"],
            tags=["t"],
            importance=5,
            project_ids=[project_a],
        ),
    )
    ctx, user_service = _make_ctx(user_id)
    adapters = MemoryToolAdapters(
        memory_service=SimpleNamespace(memory_repo=repo),
        user_service=user_service,
    )

    with pytest.raises(ToolError, match="do not all belong"):
        await adapters.rebuild_embeddings(
            ctx=ctx,
            memory_ids=[memory.id],
            project_id=project_b,
        )


@pytest.mark.asyncio
async def test_rebuild_targeted_records_unresolved_memory_ids_in_failed(sqlite_repo):
    repo, db_adapter, embedding_adapter = sqlite_repo
    user_a, memories_a = await _seed_memories(repo, db_adapter, count=1)
    _user_b, memories_b = await _seed_memories(repo, db_adapter, count=1)

    service = ReEmbeddingService(
        memory_repository=repo,
        embedding_adapter=embedding_adapter,
        batch_size=10,
    )
    result = await service.rebuild_targeted(
        user_id=user_a,
        memory_ids=[memories_a[0].id, memories_b[0].id],
    )

    assert result.rebuilt_ids == [memories_a[0].id]
    assert result.failed == [
        {
            "memory_id": memories_b[0].id,
            "reason": "not_found_or_not_owned",
        },
    ]
