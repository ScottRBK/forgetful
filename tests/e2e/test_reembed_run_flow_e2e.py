"""E2E tests for the re-embed run against real PostgreSQL (pgvector).

Tests ReEmbeddingService -> PostgresMemoryRepository: the schema must be left exactly as the
application models declare it once a re-embed has completed.
"""
import hashlib
from datetime import UTC, datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.config.settings import settings
from app.models.memory_models import MemoryCreate
from app.repositories.postgres.memory_repository import PostgresMemoryRepository
from app.services.re_embedding_service import ReEmbeddingService

pytestmark = pytest.mark.asyncio(loop_scope="session")


class StubEmbeddings:
    """Deterministic offline embeddings at the configured width."""

    async def generate_embedding(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()
        return [(digest[i % len(digest)] + 1) / 256.0 for i in range(settings.EMBEDDING_DIMENSIONS)]


async def embedding_is_nullable(db_adapter, table: str = "memories") -> bool:
    async with db_adapter.system_session() as session:
        value = await session.scalar(
            text(
                "SELECT is_nullable FROM information_schema.columns "
                "WHERE table_name = :table AND column_name = 'embedding'",
            ),
            {"table": table},
        )
    return value == "YES"


async def create_user(db_adapter):
    user_id = uuid4()
    now = datetime.now(UTC)
    async with db_adapter.system_session() as session:
        await session.execute(
            text(
                "INSERT INTO users (id, external_id, name, email, created_at, updated_at) "
                "VALUES (:id, :external_id, 'Run Flow', 'run-flow@example.com', :now, :now)",
            ),
            {"id": str(user_id), "external_id": f"ext-{user_id}", "now": now},
        )
    return user_id


@pytest_asyncio.fixture(loop_scope="session")
async def memory_repo(db_adapter, clean_database):
    """Repository on a schema that starts exactly as the migrations create it."""
    async with db_adapter.system_session() as session:
        await session.execute(text("ALTER TABLE memories ALTER COLUMN embedding SET NOT NULL"))
    repo = PostgresMemoryRepository(
        db_adapter=db_adapter, embedding_adapter=StubEmbeddings(), rerank_adapter=None,
    )
    try:
        yield repo
    finally:
        # Leave the shared database as the migrations created it for the next test module.
        async with db_adapter.system_session() as session:
            await session.execute(text("DELETE FROM memories"))
            await session.execute(text("ALTER TABLE memories ALTER COLUMN embedding SET NOT NULL"))


@pytest.mark.e2e
@pytest.mark.parametrize("count", [0, 3], ids=["empty", "three-memories"])
async def test_not_null_embedding_constraint_is_restored_after_re_embed(
    memory_repo, db_adapter, count,
):
    # Arrange
    user_id = await create_user(db_adapter)
    for index in range(count):
        await memory_repo.create_memory(user_id, MemoryCreate(
            title=f"Memory {index}", content=f"content number {index}", context="run flow",
            keywords=["run"], tags=["flow"], importance=7,
        ))
    assert not await embedding_is_nullable(db_adapter)

    # Act
    result = await ReEmbeddingService(memory_repo, StubEmbeddings(), batch_size=2).re_embed_all()

    # Assert: the reset relaxes the column while vectors are rebuilt; a finished run restores it.
    assert result.validation.all_passed
    assert not await embedding_is_nullable(db_adapter)
