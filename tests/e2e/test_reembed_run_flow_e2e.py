"""E2E tests for the re-embed run against real PostgreSQL (pgvector).

Tests ReEmbeddingService -> PostgresMemoryRepository / PostgresSkillRepository: skills must be
migrated with the memories, and the schema must be left exactly as the application models
declare it once a re-embed has completed.
"""
import hashlib
from datetime import UTC, datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.config.settings import settings
from app.models.memory_models import MemoryCreate
from app.models.skill_models import SkillCreate
from app.repositories.postgres.memory_repository import PostgresMemoryRepository
from app.repositories.postgres.skill_repository import PostgresSkillRepository
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


async def restore_schema(db_adapter, table: str) -> None:
    """Leave the shared database as the migrations created it for the next test module."""
    async with db_adapter.system_session() as session:
        await session.execute(text(f"DELETE FROM {table}"))  # noqa: S608 - fixed table names
        await session.execute(text(
            f"ALTER TABLE {table} ALTER COLUMN embedding "
            f"TYPE vector({settings.EMBEDDING_DIMENSIONS})",
        ))
        await session.execute(text(f"ALTER TABLE {table} ALTER COLUMN embedding SET NOT NULL"))


@pytest_asyncio.fixture(loop_scope="session")
async def memory_repo(db_adapter, clean_database):
    """Repository on a schema that starts exactly as the migrations create it."""
    await restore_schema(db_adapter, "memories")
    repo = PostgresMemoryRepository(
        db_adapter=db_adapter, embedding_adapter=StubEmbeddings(), rerank_adapter=None,
    )
    try:
        yield repo
    finally:
        await restore_schema(db_adapter, "memories")


@pytest_asyncio.fixture(loop_scope="session")
async def skill_repo(db_adapter, clean_database):
    await restore_schema(db_adapter, "skills")
    repo = PostgresSkillRepository(
        db_adapter=db_adapter, embedding_adapter=StubEmbeddings(), rerank_adapter=None,
    )
    try:
        yield repo
    finally:
        await restore_schema(db_adapter, "skills")


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


@pytest.mark.e2e
async def test_skills_are_migrated_with_memories_and_keep_their_constraint(
    memory_repo, skill_repo, db_adapter,
):
    # Arrange: stored memories and skills whose vectors came from another (8-wide) model,
    # while the application already runs with the new configuration, as after a restart.
    user_id = await create_user(db_adapter)
    await memory_repo.create_memory(user_id, MemoryCreate(
        title="Memory", content="content", context="run flow",
        keywords=["run"], tags=["flow"], importance=7,
    ))
    for name in ("pdf-processing", "docx-processing"):
        await skill_repo.create_skill(user_id, SkillCreate(
            name=name, description=f"Process pdf documents for {name}", content="# Steps",
        ))
    before = {s.id: s.updated_at for s in await skill_repo.get_skills_for_reembedding(10, 0)}
    async with db_adapter.system_session() as session:
        for table in ("memories", "skills"):
            await session.execute(text(f"ALTER TABLE {table} ALTER COLUMN embedding DROP NOT NULL"))
            await session.execute(text(
                f"ALTER TABLE {table} ALTER COLUMN embedding TYPE vector(8) USING NULL",
            ))
            await session.execute(text(
                f"UPDATE {table} SET embedding = '[1,0,0,0,0,0,0,0]'::vector",  # noqa: S608
            ))

    # Act
    result = await ReEmbeddingService(
        memory_repo, StubEmbeddings(), batch_size=1, skill_repository=skill_repo,
    ).re_embed_all()

    # Assert: skills have vectors of the configured width again, and search works.
    assert (result.total_skills, result.skills_processed) == (2, 2)
    assert result.validation.all_passed
    assert not await embedding_is_nullable(db_adapter, "skills")
    async with db_adapter.system_session() as session:
        widths = (await session.execute(text("SELECT DISTINCT vector_dims(embedding) FROM skills"))).all()
    assert [row[0] for row in widths] == [settings.EMBEDDING_DIMENSIONS]
    hits = await skill_repo.search_skills(user_id=user_id, query="pdf", k=5)
    assert {hit.name for hit in hits} == {"pdf-processing", "docx-processing"}
    # Rebuilding a vector is not an edit of the skill.
    after = {s.id: s.updated_at for s in await skill_repo.get_skills_for_reembedding(10, 0)}
    assert after == before
