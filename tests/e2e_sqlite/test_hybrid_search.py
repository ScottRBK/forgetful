"""E2E tests for hybrid FTS5 + RRF search (SQLite)."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config.settings import settings
from app.models.memory_models import MemoryCreate, MemoryUpdate
from app.repositories.embeddings.embedding_adapter import FastEmbeddingAdapter
from app.repositories.sqlite.memory_repository import SqliteMemoryRepository
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter


@pytest.fixture(scope="module")
def embedding_adapter():
    original_model = settings.EMBEDDING_MODEL
    original_dims = settings.EMBEDDING_DIMENSIONS
    settings.EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
    settings.EMBEDDING_DIMENSIONS = 384
    try:
        return FastEmbeddingAdapter()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"FastEmbed model unavailable (offline?): {exc}")
    finally:
        settings.EMBEDDING_MODEL = original_model
        settings.EMBEDDING_DIMENSIONS = original_dims


@pytest.fixture
async def hybrid_repo(embedding_adapter, monkeypatch):
    monkeypatch.setattr(settings, "HYBRID_SEARCH_ENABLED", True)
    monkeypatch.setattr(settings, "RERANKING_ENABLED", False)

    original_sqlite_memory = settings.SQLITE_MEMORY
    original_database = settings.DATABASE
    original_model = settings.EMBEDDING_MODEL
    original_dims = settings.EMBEDDING_DIMENSIONS

    settings.DATABASE = "SQLite"
    settings.SQLITE_MEMORY = True
    settings.EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
    settings.EMBEDDING_DIMENSIONS = 384

    try:
        db_adapter = SqliteDatabaseAdapter()
        await db_adapter.init_db()
        repo = SqliteMemoryRepository(
            db_adapter=db_adapter,
            embedding_adapter=embedding_adapter,
            rerank_adapter=None,
        )
        yield repo, db_adapter
        await db_adapter.dispose()
    finally:
        settings.DATABASE = original_database
        settings.SQLITE_MEMORY = original_sqlite_memory
        settings.EMBEDDING_MODEL = original_model
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
                "name": "Hybrid Test User",
                "email": "hybrid@example.com",
                "created_at": now,
                "updated_at": now,
            },
        )


async def _seed_memory(repo, user_id, **fields):
    defaults = {
        "title": "Hybrid seed",
        "content": "Generic filler content for hybrid search tests.",
        "context": "hybrid e2e",
        "keywords": ["hybrid"],
        "tags": ["test"],
        "importance": 7,
    }
    defaults.update(fields)
    return await repo.create_memory(
        user_id=user_id,
        memory=MemoryCreate(**defaults),
    )


def _score_has_no_hybrid_keys(score: dict) -> bool:
    return "keyword_rank" not in score and "fusion_score" not in score


@pytest.mark.asyncio
async def test_ticket_identifier_rank_one(hybrid_repo):
    repo, db_adapter = hybrid_repo
    user_id = uuid4()
    await _create_user(db_adapter, user_id)
    target = await _seed_memory(
        repo,
        user_id,
        content="Delivery note: PAY-6538 is the ticket key.",
    )
    await _seed_memory(repo, user_id, content="Unrelated paraphrase about payment workflows.")

    scored = await repo.search_scored(
        user_id=user_id,
        query="PAY-6538",
        query_context="",
        k=5,
        importance_threshold=None,
        project_ids=None,
        exclude_ids=None,
    )
    assert scored[0][0].id == target.id
    assert scored[0][1].keyword_rank == 1


@pytest.mark.asyncio
async def test_symbol_in_keywords_rank_one(hybrid_repo):
    repo, db_adapter = hybrid_repo
    user_id = uuid4()
    await _create_user(db_adapter, user_id)
    target = await _seed_memory(
        repo,
        user_id,
        content="Implementation notes.",
        keywords=["truncate_memories_by_budget", "search"],
    )
    scored = await repo.search_scored(
        user_id=user_id,
        query="truncate_memories_by_budget",
        query_context="",
        k=5,
        importance_threshold=None,
        project_ids=None,
        exclude_ids=None,
    )
    assert scored[0][0].id == target.id
    assert scored[0][1].keyword_rank == 1


@pytest.mark.asyncio
async def test_hash_ticket_rank_one(hybrid_repo):
    repo, db_adapter = hybrid_repo
    user_id = uuid4()
    await _create_user(db_adapter, user_id)
    target = await _seed_memory(
        repo,
        user_id,
        content="Memory reference #2753 documents the regression.",
    )
    scored = await repo.search_scored(
        user_id=user_id,
        query="#2753",
        query_context="",
        k=5,
        importance_threshold=None,
        project_ids=None,
        exclude_ids=None,
    )
    assert scored[0][0].id == target.id
    assert scored[0][1].keyword_rank == 1


@pytest.mark.asyncio
async def test_hybrid_off_no_fusion_fields(hybrid_repo, monkeypatch):
    repo, db_adapter = hybrid_repo
    monkeypatch.setattr(settings, "HYBRID_SEARCH_ENABLED", False)
    user_id = uuid4()
    await _create_user(db_adapter, user_id)
    await _seed_memory(repo, user_id, content="PAY-9999 placeholder content.")

    scored = await repo.search_scored(
        user_id=user_id,
        query="PAY-9999",
        query_context="",
        k=5,
        importance_threshold=None,
        project_ids=None,
        exclude_ids=None,
    )
    assert scored
    assert all(s.keyword_rank is None and s.fusion_score is None for _, s in scored)


@pytest.mark.asyncio
async def test_hybrid_off_mcp_and_rest_no_hybrid_score_keys(mcp_client, http_client, monkeypatch):
    monkeypatch.setattr(settings, "HYBRID_SEARCH_ENABLED", False)
    monkeypatch.setattr(settings, "RERANKING_ENABLED", False)
    content = "OPS-8888 appears in hybrid off API test content."
    await mcp_client.call_tool(
        "execute_forgetful_tool",
        {
            "tool_name": "create_memory",
            "arguments": {
                "title": "Hybrid off MCP",
                "content": content,
                "context": "hybrid off",
                "keywords": ["ops-8888"],
                "tags": ["hybrid-test"],
                "importance": 7,
            },
        },
    )
    mcp_result = await mcp_client.call_tool(
        "execute_forgetful_tool",
        {
            "tool_name": "query_memory",
            "arguments": {
                "query": "OPS-8888",
                "query_context": "hybrid off search",
                "k": 3,
                "include_links": False,
            },
        },
    )
    for score in mcp_result.data["scores"]:
        assert _score_has_no_hybrid_keys(score)

    rest_resp = await http_client.post(
        "/api/v1/memories/search",
        json={
            "query": "OPS-8888",
            "query_context": "hybrid off search",
            "k": 3,
            "include_links": 0,
        },
    )
    assert rest_resp.status_code == 200
    for score in rest_resp.json()["scores"]:
        assert _score_has_no_hybrid_keys(score)


@pytest.mark.asyncio
async def test_keyword_leg_failure_falls_back_to_dense(hybrid_repo, monkeypatch):
    repo, db_adapter = hybrid_repo
    user_id = uuid4()
    await _create_user(db_adapter, user_id)
    await _seed_memory(repo, user_id, content="Alpha dense ranking topic one.")
    await _seed_memory(repo, user_id, content="Beta dense ranking topic two.")

    monkeypatch.setattr(settings, "HYBRID_SEARCH_ENABLED", False)
    dense_only = await repo.search_scored(
        user_id=user_id,
        query="dense ranking topic",
        query_context="",
        k=5,
        importance_threshold=None,
        project_ids=None,
        exclude_ids=None,
    )
    dense_ids = [memory.id for memory, _ in dense_only]

    monkeypatch.setattr(settings, "HYBRID_SEARCH_ENABLED", True)

    async def _raise_keyword_leg(*_args, **_kwargs):
        raise SQLAlchemyError("simulated keyword leg failure")

    monkeypatch.setattr(repo, "keyword_search_scored", _raise_keyword_leg)

    warnings: list[str] = []

    def _capture_warning(message, *args, **kwargs):
        warnings.append(str(message))

    monkeypatch.setattr(
        "app.repositories.sqlite.memory_repository.logger.warning",
        _capture_warning,
    )

    hybrid = await repo.search_scored(
        user_id=user_id,
        query="dense ranking topic",
        query_context="",
        k=5,
        importance_threshold=None,
        project_ids=None,
        exclude_ids=None,
    )

    assert [memory.id for memory, _ in hybrid] == dense_ids
    assert any("keyword leg failed, falling back to dense only" in message for message in warnings)


@pytest.mark.asyncio
async def test_obsolete_excluded_from_keyword_leg(hybrid_repo):
    repo, db_adapter = hybrid_repo
    user_id = uuid4()
    await _create_user(db_adapter, user_id)
    mem = await _seed_memory(repo, user_id, content="PAY-OBSOLETE marker here.")
    await repo.mark_obsolete(user_id, mem.id, "test", None)

    keyword_hits = await repo.keyword_search_scored(
        user_id=user_id,
        query="PAY-OBSOLETE",
        k=10,
        importance_threshold=None,
        project_ids=None,
        exclude_ids=None,
    )
    assert keyword_hits == []


@pytest.mark.asyncio
async def test_update_and_delete_keyword_index(hybrid_repo):
    repo, db_adapter = hybrid_repo
    user_id = uuid4()
    await _create_user(db_adapter, user_id)
    mem = await _seed_memory(repo, user_id, content="Token OLDTOKEN visible once.")

    before = await repo.keyword_search_scored(
        user_id=user_id,
        query="OLDTOKEN",
        k=5,
        importance_threshold=None,
        project_ids=None,
        exclude_ids=None,
    )
    assert [m.id for m, _ in before] == [mem.id]

    updated = await repo.update_memory(
        user_id=user_id,
        memory_id=mem.id,
        updated_memory=MemoryUpdate(content="Token NEWTOKEN visible now."),
        existing_memory=mem,
        search_fields_changed=True,
    )
    assert updated.content.endswith("NEWTOKEN visible now.")

    after_old = await repo.keyword_search_scored(
        user_id=user_id,
        query="OLDTOKEN",
        k=5,
        importance_threshold=None,
        project_ids=None,
        exclude_ids=None,
    )
    assert after_old == []

    after_new = await repo.keyword_search_scored(
        user_id=user_id,
        query="NEWTOKEN",
        k=5,
        importance_threshold=None,
        project_ids=None,
        exclude_ids=None,
    )
    assert [m.id for m, _ in after_new] == [mem.id]


@pytest.mark.asyncio
async def test_fts_trigger_self_heal(hybrid_repo):
    _repo, db_adapter = hybrid_repo
    async with db_adapter._engine.begin() as conn:
        await conn.execute(text("DROP TRIGGER IF EXISTS memories_fts_ai"))
        first = await db_adapter.ensure_memory_fts(conn)
        assert first is True
        second = await db_adapter.ensure_memory_fts(conn)
        assert second is False
