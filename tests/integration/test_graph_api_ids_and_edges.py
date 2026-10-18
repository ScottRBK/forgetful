"""Integration tests for graph node id parsing and bulk memory linking.

Covers, without any network access or embedding model:
- GraphService.parse_node_id: canonical ASCII ids only, an upper bound that fits
  the integer columns, and an error message that shows the real id placeholders.
- SqliteMemoryRepository.create_links_batch: ids that cannot be stored as an
  integer are skipped like unknown ids instead of aborting the batch half way.
"""
import hashlib
import random
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.config.settings import settings
from app.models.memory_models import MemoryCreate
from app.repositories.sqlite.memory_repository import SqliteMemoryRepository
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter
from app.services.graph_service import MAX_NODE_ID, GraphService

NODE_TYPES = [
    "memory",
    "entity",
    "project",
    "document",
    "code_artifact",
    "file",
    "skill",
    "plan",
    "task",
]


# ---- GraphService.parse_node_id ----

@pytest.mark.parametrize("node_type", NODE_TYPES)
def test_parse_node_id_accepts_largest_supported_id(node_type):
    assert GraphService.parse_node_id(f"{node_type}_{MAX_NODE_ID}") == (node_type, MAX_NODE_ID)


@pytest.mark.parametrize("node_type", NODE_TYPES)
@pytest.mark.parametrize(
    "number",
    [MAX_NODE_ID + 1, 2**63, 2**64, 99999999999999999999],
    ids=["max+1", "int64-overflow", "uint64-overflow", "20-digits"],
)
def test_parse_node_id_rejects_ids_beyond_the_integer_range(node_type, number):
    with pytest.raises(ValueError, match="out of range"):
        GraphService.parse_node_id(f"{node_type}_{number}")


@pytest.mark.parametrize(
    "raw",
    [
        "memory_1\n",
        "memory_1 ",
        " memory_1",
        "memory_١",  # Arabic-Indic digit one
        "memory_１",  # fullwidth digit one
        "memory_",
        "memory_-1",
        "memory_1.5",
    ],
    ids=[
        "trailing-newline",
        "trailing-space",
        "leading-space",
        "arabic-indic-digit",
        "fullwidth-digit",
        "no-digits",
        "negative",
        "decimal",
    ],
)
def test_parse_node_id_rejects_non_canonical_ids(raw):
    with pytest.raises(ValueError, match="Invalid node_id format"):
        GraphService.parse_node_id(raw)


def test_parse_node_id_normalises_leading_zeros():
    assert GraphService.parse_node_id("memory_001") == ("memory", 1)


def test_parse_node_id_error_message_shows_id_placeholders():
    with pytest.raises(ValueError) as excinfo:
        GraphService.parse_node_id("bad")

    message = str(excinfo.value)
    for node_type in NODE_TYPES:
        assert f"'{node_type}_{{id}}'" in message
    assert "{{" not in message
    assert "}}" not in message


# ---- SqliteMemoryRepository.create_links_batch ----

class _StaticEmbeddingAdapter:
    """Deterministic, offline embedding adapter for sqlite-vec."""

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
    repo = SqliteMemoryRepository(
        db_adapter=db_adapter,
        embedding_adapter=_StaticEmbeddingAdapter(dimensions=384),
        rerank_adapter=None,
    )

    try:
        yield repo, db_adapter
    finally:
        try:
            await db_adapter.dispose()
        except Exception:  # noqa: BLE001
            pass
        settings.DATABASE = original_database
        settings.SQLITE_MEMORY = original_sqlite_memory
        settings.EMBEDDING_DIMENSIONS = original_dims


async def _seed_memories(repo, db_adapter, count):
    user_id = uuid4()
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

    memories = []
    for i in range(count):
        memories.append(
            await repo.create_memory(
                user_id=user_id,
                memory=MemoryCreate(
                    title=f"M{i}",
                    content=f"content {i}",
                    context=f"ctx {i}",
                    keywords=[f"k{i}"],
                    tags=[f"t{i}"],
                    importance=5,
                ),
            ),
        )
    return user_id, [memory.id for memory in memories]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bad_id",
    [2**63, 2**70, -(2**63) - 1, 0, -5],
    ids=["int64-overflow", "2**70", "below-int64", "zero", "negative"],
)
async def test_create_links_batch_skips_unstorable_target_ids(sqlite_repo, bad_id):
    repo, db_adapter = sqlite_repo
    user_id, ids = await _seed_memories(repo, db_adapter, count=4)
    source, first, _unused, last = ids

    linked = await repo.create_links_batch(user_id, source, [last, bad_id, first])

    assert linked == [last, first]
    stored = await repo.get_memory_by_id(user_id, source)
    assert sorted(stored.linked_memory_ids) == sorted([first, last])


@pytest.mark.asyncio
async def test_create_links_batch_skips_largest_int64_target_as_not_found(sqlite_repo):
    repo, db_adapter = sqlite_repo
    user_id, ids = await _seed_memories(repo, db_adapter, count=3)

    linked = await repo.create_links_batch(user_id, ids[0], [2**63 - 1, ids[1]])

    assert linked == [ids[1]]


@pytest.mark.asyncio
async def test_create_links_batch_with_unstorable_source_links_nothing(sqlite_repo):
    repo, db_adapter = sqlite_repo
    user_id, ids = await _seed_memories(repo, db_adapter, count=2)

    assert await repo.create_links_batch(user_id, 2**70, ids) == []

    for memory_id in ids:
        stored = await repo.get_memory_by_id(user_id, memory_id)
        assert stored.linked_memory_ids == []


# ---- SqliteMemoryRepository.get_listed_memory_ids ----

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


def _memory_create(index, **extra):
    return MemoryCreate(
        title=f"M{index}",
        content=f"content {index}",
        context=f"ctx {index}",
        keywords=[f"k{index}"],
        tags=[f"t{index}"],
        importance=5,
        **extra,
    )


@pytest.mark.asyncio
async def test_get_listed_memory_ids_applies_the_listing_rules(sqlite_repo):
    repo, db_adapter = sqlite_repo
    user_id, ids = await _seed_memories(repo, db_adapter, count=4)
    other_user_id, other_ids = await _seed_memories(repo, db_adapter, count=1)
    await repo.mark_obsolete(user_id, ids[1], reason="outdated")

    candidates = [*ids, other_ids[0], 999_999]
    listed = await repo.get_listed_memory_ids(user_id, candidates)

    assert listed == {ids[0], ids[2], ids[3]}
    # Same answer as the listing itself
    page, _total = await repo.list_memories(user_id=user_id, limit=100)
    assert listed == {memory.id for memory in page}
    assert await repo.get_listed_memory_ids(other_user_id, [ids[0]]) == set()
    assert await repo.get_listed_memory_ids(user_id, []) == set()


@pytest.mark.asyncio
async def test_get_listed_memory_ids_honours_the_project_filter(sqlite_repo):
    repo, db_adapter = sqlite_repo
    user_id, _ids = await _seed_memories(repo, db_adapter, count=0)
    project_id = await _create_project(db_adapter, user_id)
    inside = await repo.create_memory(user_id=user_id, memory=_memory_create(1, project_ids=[project_id]))
    outside = await repo.create_memory(user_id=user_id, memory=_memory_create(2))

    listed = await repo.get_listed_memory_ids(
        user_id, [inside.id, outside.id], project_ids=[project_id],
    )

    assert listed == {inside.id}
    assert await repo.get_listed_memory_ids(user_id, [inside.id, outside.id]) == {inside.id, outside.id}
