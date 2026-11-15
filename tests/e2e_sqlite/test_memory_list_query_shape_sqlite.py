"""SQLite E2E tests: the memories list must page and filter in SQL.

`GET /api/v1/memories` used to load every matching memory into Python and
slice there, so `limit`/`offset` never reached SQL. One page dragged the
eager-loaded relations of the whole result set with it, and `total` was the
length of the materialised list.

These tests pin the query shape: the page is limited in SQL, the tag filter
runs in SQL, and `total` comes from a COUNT over the same conditions. The
assertions read the emitted statements, because the response body is correct
either way - only the work done to build it changes.
"""
from contextlib import contextmanager
from uuid import UUID, uuid4

import pytest
from sqlalchemy import event, text

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


@contextmanager
def capture_statements(db_adapter):
    """Collect (statement, parameters) for every query the engine emits."""
    captured = []

    def listener(connection, cursor, statement, parameters, context, executemany):
        captured.append((statement, parameters))

    engine = db_adapter._engine.sync_engine
    event.listen(engine, "before_cursor_execute", listener)
    try:
        yield captured
    finally:
        event.remove(engine, "before_cursor_execute", listener)


def memory_selects(captured):
    """Statements that read the memories table."""
    return [
        statement for statement, _ in captured
        if "FROM memories" in statement and statement.lstrip().upper().startswith("SELECT")
    ]


def page_selects(captured):
    """The paging query: selects whole memory rows, not a count."""
    return [
        statement for statement, _ in captured
        if statement.lstrip().startswith("SELECT memories.id")
    ]


def count_selects(captured):
    return [
        statement for statement, _ in captured
        if statement.lstrip().upper().startswith("SELECT COUNT(")
    ]


@pytest.fixture
async def repo_and_db():
    original = (settings.DATABASE, settings.SQLITE_MEMORY, settings.EMBEDDING_DIMENSIONS)
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
        settings.DATABASE, settings.SQLITE_MEMORY, settings.EMBEDDING_DIMENSIONS = original


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


def _memory(title: str, tags: list[str]) -> MemoryCreate:
    return MemoryCreate(
        title=title,
        content=f"{title} content",
        context="query shape test",
        keywords=["query-shape"],
        tags=tags,
        importance=7,
    )


@pytest.mark.asyncio
async def test_limit_and_offset_reach_sql(repo_and_db):
    """A page request must carry LIMIT/OFFSET, not slice a full result set."""
    repo, db = repo_and_db
    user = uuid4()
    await _create_user(db, user)
    for index in range(3):
        await repo.create_memory(user, _memory(f"Paged memory {index}", ["page"]))

    with capture_statements(db) as captured:
        memories, total = await repo.list_memories(user, limit=1, offset=2)

    # Newest first, so offset 2 lands on the oldest row: proves the skip count
    # is applied by the database, not by slicing after the fact.
    assert [m.title for m in memories] == ["Paged memory 0"]
    assert total == 3
    pages = page_selects(captured)
    assert pages, "expected a paging query over memories"
    assert any("LIMIT" in s.upper() and "OFFSET" in s.upper() for s in pages), (
        "list_memories must push LIMIT/OFFSET into SQL; emitted page statements were:\n"
        + "\n---\n".join(pages)
    )


@pytest.mark.asyncio
async def test_relations_load_only_for_the_page(repo_and_db):
    """Eager loading must fetch relations for the page, not for every match."""
    repo, db = repo_and_db
    user = uuid4()
    await _create_user(db, user)
    for index in range(4):
        await repo.create_memory(user, _memory(f"Relation memory {index}", ["rel"]))

    with capture_statements(db) as captured:
        memories, total = await repo.list_memories(user, limit=1)

    assert len(memories) == 1
    assert total == 4
    relation_loads = [
        params for statement, params in captured
        if "memories_1.id IN (" in statement
    ]
    assert relation_loads, "expected eager-load statements over the page rows"
    assert all(len(params) == 1 for params in relation_loads), (
        "eager loads must cover the page only, got parameter counts: "
        f"{[len(params) for params in relation_loads]}"
    )


@pytest.mark.asyncio
async def test_tag_filter_reaches_sql(repo_and_db):
    """Tag filtering must run in SQL, not after loading every row."""
    repo, db = repo_and_db
    user = uuid4()
    await _create_user(db, user)
    await repo.create_memory(user, _memory("Alpha memory", ["alpha"]))
    await repo.create_memory(user, _memory("Beta memory", ["beta"]))

    with capture_statements(db) as captured:
        memories, total = await repo.list_memories(user, limit=10, tags=["alpha"])

    assert [m.title for m in memories] == ["Alpha memory"]
    assert total == 1
    pages = page_selects(captured)
    counts = count_selects(captured)
    assert pages, "expected a paging query over memories"
    assert any("json_each" in s for s in pages), (
        "the tag filter must be in the paging query, not applied after loading; "
        "emitted page statements were:\n" + "\n---\n".join(pages)
    )
    assert any("json_each" in s for s in counts), (
        "the tag filter must also be in the count query so total matches the page"
    )


@pytest.mark.asyncio
async def test_total_comes_from_a_count_query(repo_and_db):
    """`total` must be counted in SQL over the same conditions as the page."""
    repo, db = repo_and_db
    user = uuid4()
    await _create_user(db, user)
    for index in range(3):
        await repo.create_memory(user, _memory(f"Counted memory {index}", ["counted"]))

    with capture_statements(db) as captured:
        memories, total = await repo.list_memories(user, limit=2, tags=["counted"])

    assert len(memories) == 2
    assert total == 3
    counts = count_selects(captured)
    assert counts, (
        "total must come from a COUNT query; emitted statements were:\n"
        + "\n---\n".join(statement for statement, _ in captured)
    )


@pytest.mark.asyncio
async def test_tag_filter_applies_before_pagination(repo_and_db):
    """A small page must be filled with matches, not filtered after slicing.

    Rows alternate between matching and non-matching tags, so filtering the
    newest page after it is sliced returns fewer rows than asked for.
    """
    repo, db = repo_and_db
    user = uuid4()
    await _create_user(db, user)
    await repo.create_memory(user, _memory("Alpha one", ["alpha"]))
    await repo.create_memory(user, _memory("Beta one", ["beta"]))
    await repo.create_memory(user, _memory("Alpha two", ["alpha"]))
    await repo.create_memory(user, _memory("Beta two", ["beta"]))

    memories, total = await repo.list_memories(user, limit=2, tags=["alpha"])

    assert {m.title for m in memories} == {"Alpha one", "Alpha two"}
    assert total == 2


@pytest.mark.asyncio
async def test_tag_filter_is_exact_match(repo_and_db):
    """Pushing the filter into SQL must not turn it into a substring match."""
    repo, db = repo_and_db
    user = uuid4()
    await _create_user(db, user)
    await repo.create_memory(user, _memory("Alphabet memory", ["alphabet"]))
    await repo.create_memory(user, _memory("Alpha memory", ["alpha"]))

    memories, total = await repo.list_memories(user, limit=10, tags=["alpha"])

    assert [m.title for m in memories] == ["Alpha memory"]
    assert total == 1


@pytest.mark.asyncio
async def test_tag_filter_uses_or_logic(repo_and_db):
    """Several tags match a memory that has ANY of them."""
    repo, db = repo_and_db
    user = uuid4()
    await _create_user(db, user)
    await repo.create_memory(user, _memory("TagA memory", ["tag-a"]))
    await repo.create_memory(user, _memory("TagB memory", ["tag-b"]))
    await repo.create_memory(user, _memory("TagC memory", ["tag-c"]))
    await repo.create_memory(user, _memory("No tag memory", []))

    memories, total = await repo.list_memories(user, limit=10, tags=["tag-a", "tag-b"])

    assert {m.title for m in memories} == {"TagA memory", "TagB memory"}
    assert total == 2


@pytest.mark.asyncio
async def test_tags_with_offset_and_importance_sort(repo_and_db):
    """Tags, offset and the importance ordering branch agree with each other.

    The importance branch uses a different tiebreak from the other sort fields,
    so combining it with a tag filter and an offset is where a filter applied
    outside the paging query shows up as a wrong row or a wrong total.
    """
    repo, db = repo_and_db
    user = uuid4()
    await _create_user(db, user)

    def memory(title: str, tags: list[str], importance: int) -> MemoryCreate:
        return MemoryCreate(
            title=title,
            content=f"{title} content",
            context="query shape test",
            keywords=["query-shape"],
            tags=tags,
            importance=importance,
        )

    await repo.create_memory(user, memory("Match low", ["mixed"], 3))
    await repo.create_memory(user, memory("No match high", ["other"], 9))
    await repo.create_memory(user, memory("Match high", ["mixed"], 8))
    await repo.create_memory(user, memory("No match low", ["other"], 2))
    await repo.create_memory(user, memory("Match mid", ["mixed"], 5))
    await repo.create_memory(user, memory("Obsolete match", ["mixed"], 7))

    listed, _ = await repo.list_memories(user, limit=10, tags=["mixed"])
    obsolete_id = next(m.id for m in listed if m.title == "Obsolete match")
    await repo.mark_obsolete(user, obsolete_id, reason="superseded in a test")

    memories, total = await repo.list_memories(
        user, limit=1, offset=1, sort_by="importance", sort_order="desc", tags=["mixed"],
    )

    assert [m.title for m in memories] == ["Match mid"]
    assert total == 3
