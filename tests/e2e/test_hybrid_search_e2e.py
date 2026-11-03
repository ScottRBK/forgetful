"""E2E tests for hybrid tsvector + RRF search (PostgreSQL)."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from alembic import command
from app.config.settings import settings
from app.models.memory_models import MemoryCreate, MemoryUpdate
from app.repositories.postgres.memory_repository import PostgresMemoryRepository

pytestmark = [pytest.mark.asyncio(loop_scope="session"), pytest.mark.e2e]


@pytest_asyncio.fixture
async def hybrid_repo(db_adapter, embedding_adapter, monkeypatch):
    monkeypatch.setattr(settings, "HYBRID_SEARCH_ENABLED", True)
    monkeypatch.setattr(settings, "RERANKING_ENABLED", False)
    repo = PostgresMemoryRepository(
        db_adapter=db_adapter,
        embedding_adapter=embedding_adapter,
        rerank_adapter=None,
    )
    yield repo, db_adapter


async def _create_user(db_adapter, user_id):
    now = datetime.now(UTC)
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
        "app.repositories.postgres.memory_repository.logger.warning",
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


async def test_migration_round_trip_preserves_hybrid_search(hybrid_repo):
    repo, db_adapter = hybrid_repo
    user_id = uuid4()
    await _create_user(db_adapter, user_id)
    target = await _seed_memory(
        repo,
        user_id,
        content="Delivery note: PAY-6538 survives migration round trip.",
    )
    await _seed_memory(repo, user_id, content="Second filler memory for migration test.")
    await _seed_memory(repo, user_id, content="Third filler memory for migration test.")

    config = Config(str(Path(__file__).parents[2] / "alembic.ini"))

    def migrate(connection, direction, revision):
        config.attributes["connection"] = connection
        getattr(command, direction)(config, revision)

    try:
        async with db_adapter._engine.begin() as connection:
            await connection.run_sync(migrate, "downgrade", "-1")
        async with db_adapter._engine.begin() as connection:
            await connection.run_sync(migrate, "upgrade", "head")
    except Exception:
        async with db_adapter._engine.begin() as connection:
            await connection.run_sync(migrate, "upgrade", "head")
        raise

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
