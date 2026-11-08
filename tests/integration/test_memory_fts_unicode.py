"""SQLite FTS5 Unicode JSON keywords/tags: rebuild vs decoded view backfill."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.config.settings import settings
from app.repositories.sqlite.memory_repository import SqliteMemoryRepository
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter

_UNICODE_WORD = "résumé"
_ESCAPE_FRAGMENT = "u00e9sum"
_ESCAPED_KEYWORDS = '["r\\u00e9sum\\u00e9"]'
_ESCAPED_TAGS = '["r\\u00e9sum\\u00e9"]'


class _NoEmbed:
    dimensions = 384

    async def generate_embedding(self, text: str) -> list[float]:
        raise AssertionError("keyword FTS tests must not generate embeddings")


@pytest.fixture
async def fts_repo():
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
        embedding_adapter=_NoEmbed(),
        rerank_adapter=None,
    )
    try:
        yield repo, db_adapter
    finally:
        await db_adapter.dispose()
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
                "name": "FTS Unicode User",
                "email": "fts-unicode@example.com",
                "created_at": now,
                "updated_at": now,
            },
        )


async def _drop_fts(conn):
    await conn.execute(text("DROP TRIGGER IF EXISTS memories_fts_ai"))
    await conn.execute(text("DROP TRIGGER IF EXISTS memories_fts_ad"))
    await conn.execute(text("DROP TRIGGER IF EXISTS memories_fts_bu"))
    await conn.execute(text("DROP TRIGGER IF EXISTS memories_fts_au"))
    await conn.execute(text("DROP TABLE IF EXISTS memories_fts"))
    await conn.execute(text("DROP VIEW IF EXISTS memories_fts_src"))


async def _insert_unicode_memory(db_adapter, user_id) -> int:
    now = datetime.now(UTC).isoformat()
    async with db_adapter.system_session() as session:
        result = await session.execute(
            text(
                """
                INSERT INTO memories (
                    user_id, title, content, context, keywords, tags,
                    importance, is_obsolete, access_count, created_at, updated_at
                ) VALUES (
                    :user_id, :title, :content, :context, :keywords, :tags,
                    7, 0, 0, :now, :now
                )
                RETURNING id
                """,
            ),
            {
                "user_id": str(user_id),
                "title": "Plain title",
                "content": "Plain body without the unicode token.",
                "context": "plain context",
                "keywords": _ESCAPED_KEYWORDS,
                "tags": _ESCAPED_TAGS,
                "now": now,
            },
        )
        return result.scalar_one()


async def _keyword_ids(repo, user_id, query):
    hits = await repo.keyword_search_scored(
        user_id=user_id,
        query=query,
        k=10,
        importance_threshold=None,
        project_ids=None,
        exclude_ids=None,
    )
    return [memory.id for memory, _rank in hits]


def test_fts5_rebuild_on_raw_json_indexes_escape_fragments():
    """Maintainer SQL repro: FTS5 rebuild reads JSON escapes; json_each does not."""
    import json
    import sqlite3

    escaped = json.dumps([_UNICODE_WORD], ensure_ascii=True)
    assert "\\u00e9" in escaped

    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE memories (
          id INTEGER PRIMARY KEY,
          title TEXT, content TEXT, context TEXT, keywords TEXT, tags TEXT
        )
        """,
    )
    conn.execute(
        "INSERT INTO memories VALUES (1, 'Note', 'plain body', 'ctx', ?, ?)",
        (escaped, escaped),
    )
    conn.execute(
        """
        CREATE VIRTUAL TABLE memories_fts USING fts5(
          title, content, context, keywords, tags,
          content='memories', content_rowid='id', tokenize='unicode61'
        )
        """,
    )
    conn.execute("INSERT INTO memories_fts(memories_fts) VALUES('rebuild')")
    resume = conn.execute(
        "SELECT COUNT(*) FROM memories_fts WHERE memories_fts MATCH 'résumé'",
    ).fetchone()[0]
    escape = conn.execute(
        "SELECT COUNT(*) FROM memories_fts WHERE memories_fts MATCH 'u00e9sum'",
    ).fetchone()[0]
    assert resume == 0
    assert escape == 1


@pytest.mark.asyncio
async def test_ensure_memory_fts_indexes_unicode_json_keywords_and_tags(fts_repo):
    repo, db_adapter = fts_repo
    user_id = uuid4()
    await _create_user(db_adapter, user_id)

    async with db_adapter._engine.begin() as conn:
        await _drop_fts(conn)

    memory_id = await _insert_unicode_memory(db_adapter, user_id)

    async with db_adapter._engine.begin() as conn:
        rebuilt = await db_adapter.ensure_memory_fts(conn)
        assert rebuilt is True

    assert await _keyword_ids(repo, user_id, _UNICODE_WORD) == [memory_id]
    assert await _keyword_ids(repo, user_id, _ESCAPE_FRAGMENT) == []

    async with db_adapter.system_session() as session:
        await session.execute(
            text("UPDATE memories SET keywords = :kw, tags = :tags WHERE id = :id"),
            {"kw": '["dossier"]', "tags": '["classeur"]', "id": memory_id},
        )

    assert await _keyword_ids(repo, user_id, _UNICODE_WORD) == []
    assert await _keyword_ids(repo, user_id, _ESCAPE_FRAGMENT) == []
    assert await _keyword_ids(repo, user_id, "dossier") == [memory_id]
    assert await _keyword_ids(repo, user_id, "classeur") == [memory_id]

    async with db_adapter.system_session() as session:
        await session.execute(text("DELETE FROM memories WHERE id = :id"), {"id": memory_id})

    assert await _keyword_ids(repo, user_id, "dossier") == []
    assert await _keyword_ids(repo, user_id, "classeur") == []

    memory_id = await _insert_unicode_memory(db_adapter, user_id)
    assert await _keyword_ids(repo, user_id, _UNICODE_WORD) == [memory_id]

    async with db_adapter._engine.begin() as conn:
        await conn.execute(text("DROP TRIGGER IF EXISTS memories_fts_ai"))
        repaired = await db_adapter.ensure_memory_fts(conn)
        assert repaired is True

    assert await _keyword_ids(repo, user_id, _UNICODE_WORD) == [memory_id]
    assert await _keyword_ids(repo, user_id, _ESCAPE_FRAGMENT) == []


@pytest.mark.asyncio
async def test_ensure_memory_fts_migrates_content_memories_table(fts_repo):
    repo, db_adapter = fts_repo
    user_id = uuid4()
    await _create_user(db_adapter, user_id)

    async with db_adapter._engine.begin() as conn:
        await _drop_fts(conn)
        await conn.execute(
            text(
                """
                CREATE VIRTUAL TABLE memories_fts USING fts5(
                    title, content, context, keywords, tags,
                    content='memories', content_rowid='id', tokenize='unicode61'
                )
                """,
            ),
        )

    memory_id = await _insert_unicode_memory(db_adapter, user_id)

    async with db_adapter._engine.begin() as conn:
        await conn.execute(text("INSERT INTO memories_fts(memories_fts) VALUES('rebuild')"))

    assert await _keyword_ids(repo, user_id, _UNICODE_WORD) == []
    assert await _keyword_ids(repo, user_id, _ESCAPE_FRAGMENT) == [memory_id]

    async with db_adapter._engine.begin() as conn:
        migrated = await db_adapter.ensure_memory_fts(conn)
        assert migrated is True

    assert await _keyword_ids(repo, user_id, _UNICODE_WORD) == [memory_id]
    assert await _keyword_ids(repo, user_id, _ESCAPE_FRAGMENT) == []
