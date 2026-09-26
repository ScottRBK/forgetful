"""E2E tests for re-embedding with real PostgreSQL and real embedding adapters.

Tests the full stack: ReEmbeddingService -> PostgresMemoryRepository -> pgvector

Uses the configured embedding provider (e.g. OpenAI, FastEmbed). Migration tests
seed storage with old dimensions while keeping the ORM at the target dimensions,
matching a fresh process started after changing the embedding configuration.
"""
from datetime import UTC
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.config.settings import settings
from app.models.memory_models import MemoryCreate
from app.repositories.postgres.memory_repository import PostgresMemoryRepository
from app.services.re_embedding_service import ReEmbeddingService

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest_asyncio.fixture(loop_scope="session")
async def memory_repo(db_adapter, embedding_adapter):
    """Repo using the configured embedding adapter (matches DB schema)."""
    repo = PostgresMemoryRepository(
        db_adapter=db_adapter,
        embedding_adapter=embedding_adapter,
        rerank_adapter=None,
    )
    try:
        yield repo
    finally:
        # Restore the configured dimensions even if a migration test fails before resetting storage.
        await repo.reset_embedding_storage()


async def _create_user(db_adapter, user_id):
    """Create a user row in the database (required for FK constraints)."""
    from datetime import datetime
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
                "name": "Test User",
                "email": "test@example.com",
                "created_at": now,
                "updated_at": now,
            },
        )


async def _create_test_memories(repo, db_adapter, count=5):
    """Helper to create test memories via the repository."""
    user_id = uuid4()
    await _create_user(db_adapter, user_id)

    memories = []
    for i in range(count):
        memory = await repo.create_memory(
            user_id=user_id,
            memory=MemoryCreate(
                title=f"Test Memory {i}",
                content=f"This is test memory content number {i} about topic {i}",
                context=f"Testing context for memory {i}",
                keywords=[f"keyword{i}", "test"],
                tags=[f"tag{i}", "test"],
                importance=7,
            ),
        )
        memories.append(memory)
    return user_id, memories


@pytest.mark.e2e
async def test_re_embed_search_works_after(memory_repo, db_adapter, embedding_adapter):
    """Create memories, re-embed, run semantic search, verify results returned."""
    user_id, memories = await _create_test_memories(memory_repo, db_adapter, count=3)

    service = ReEmbeddingService(
        memory_repository=memory_repo,
        embedding_adapter=embedding_adapter,
        batch_size=10,
    )
    result = await service.re_embed_all()

    assert result.total_processed == 3
    assert result.validation.all_passed

    search_results = await memory_repo.search(
        user_id=user_id,
        query="test memory content",
        query_context="verifying search after re-embed",
        k=3,
        importance_threshold=None,
        project_ids=None,
        exclude_ids=None,
    )
    assert len(search_results) > 0


@pytest.mark.e2e
async def test_re_embed_count_integrity(memory_repo, db_adapter, embedding_adapter):
    """After re-embed, verify embedding count matches memory count."""
    user_id, memories = await _create_test_memories(memory_repo, db_adapter, count=5)

    service = ReEmbeddingService(
        memory_repository=memory_repo,
        embedding_adapter=embedding_adapter,
        batch_size=3,
    )
    result = await service.re_embed_all()

    assert result.total_processed == 5
    assert result.validation.count_ok


@pytest.mark.e2e
async def test_re_embed_preserves_memory_data(memory_repo, db_adapter, embedding_adapter):
    """After re-embed, verify all memory fields unchanged."""
    user_id, original_memories = await _create_test_memories(memory_repo, db_adapter, count=3)

    service = ReEmbeddingService(
        memory_repository=memory_repo,
        embedding_adapter=embedding_adapter,
        batch_size=10,
    )
    await service.re_embed_all()

    for original in original_memories:
        refreshed = await memory_repo.get_memory_by_id(user_id=user_id, memory_id=original.id)
        assert refreshed.title == original.title
        assert refreshed.content == original.content
        assert refreshed.context == original.context
        assert refreshed.keywords == original.keywords
        assert refreshed.tags == original.tags
        assert refreshed.importance == original.importance


@pytest.mark.e2e
@pytest.mark.parametrize("obsolete_only", [False, True], ids=["mixed", "all-obsolete"])
@pytest.mark.parametrize("previous_storage", ["missing_vector", "old_dimensions"])
async def test_re_embed_recovers_obsolete_vectors(
    memory_repo, db_adapter, embedding_adapter, obsolete_only, previous_storage,
):
    user_id, memories = await _create_test_memories(memory_repo, db_adapter, count=3)
    old = memories[-1]
    await memory_repo.mark_obsolete(user_id, old.id, "superseded", memories[0].id)
    if obsolete_only:
        for memory in memories[:-1]:
            await memory_repo.mark_obsolete(user_id, memory.id, "outdated")
    original = await memory_repo.get_memory_by_id(user_id, old.id)

    async with db_adapter.system_session() as session:
        await session.execute(text("ALTER TABLE memories ALTER COLUMN embedding DROP NOT NULL"))
        if previous_storage == "missing_vector":
            # Reproduce the obsolete vector loss caused by older full rebuilds.
            await session.execute(
                text("UPDATE memories SET embedding = NULL WHERE id = :id"), {"id": old.id},
            )
        else:
            # Keep the ORM at the new dimensions, as in a fresh migration process.
            await session.execute(text(
                "ALTER TABLE memories ALTER COLUMN embedding TYPE vector(8) USING NULL",
            ))
            await session.execute(text(
                "UPDATE memories SET embedding = '[1,0,0,0,0,0,0,0]'::vector",
            ))

    progress = []
    result = await ReEmbeddingService(memory_repo, embedding_adapter, batch_size=2).re_embed_all(
        progress_callback=lambda done, total: progress.append((done, total)),
    )

    assert result.total_memories == result.total_processed == 3
    assert progress == [(2, 3), (3, 3)]
    assert result.validation.all_passed
    refreshed = await memory_repo.get_memory_by_id(user_id, old.id)
    preserved_fields = {
        "title", "content", "context", "keywords", "tags", "importance", "created_at",
        "is_obsolete", "obsolete_reason", "superseded_by", "obsoleted_at",
    }
    assert refreshed.model_dump(include=preserved_fields) == original.model_dump(
        include=preserved_fields,
    )
    recreated = await memory_repo.create_memory(
        user_id, MemoryCreate.model_validate(old.model_dump()),
    )
    matches = await memory_repo.find_obsolete_matches(
        user_id, recreated.id, limit=3, min_similarity=0.99,
    )
    assert old.id in {memory.id for memory, _ in matches}


@pytest.mark.e2e
async def test_re_embed_empty_database(memory_repo, db_adapter, embedding_adapter):
    """Re-embedding an empty database should succeed with no work done."""

    service = ReEmbeddingService(
        memory_repository=memory_repo,
        embedding_adapter=embedding_adapter,
        batch_size=10,
    )
    result = await service.re_embed_all()

    assert result.total_processed == 0
    assert result.total_memories == 0
    assert result.validation.all_passed


@pytest.mark.e2e
async def test_re_embed_validation_checks(memory_repo, db_adapter, embedding_adapter):
    """Verify all validation checks pass after successful re-embed."""
    user_id, memories = await _create_test_memories(memory_repo, db_adapter, count=4)

    service = ReEmbeddingService(
        memory_repository=memory_repo,
        embedding_adapter=embedding_adapter,
        batch_size=2,
    )
    result = await service.re_embed_all()

    assert result.validation.count_ok
    assert result.validation.dimensions_ok
    assert result.validation.search_ok
    assert result.validation.all_passed


@pytest.mark.e2e
@pytest.mark.parametrize("problem", ["missing_embeddings", "wrong_dimensions"])
async def test_validation_checks_obsolete_only_database(
    memory_repo, db_adapter, embedding_adapter, monkeypatch, problem,
):
    user_id, memories = await _create_test_memories(memory_repo, db_adapter, count=1)
    await memory_repo.mark_obsolete(user_id, memories[0].id, "outdated")
    if problem == "missing_embeddings":
        await memory_repo.reset_embedding_storage()
    else:
        monkeypatch.setattr(settings, "EMBEDDING_DIMENSIONS", settings.EMBEDDING_DIMENSIONS + 1)

    validation = await ReEmbeddingService(memory_repo, embedding_adapter).validate()

    if problem == "missing_embeddings":
        assert not validation.count_ok
        assert not validation.search_ok
    else:
        assert not validation.dimensions_ok
