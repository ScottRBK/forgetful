"""PostgreSQL regression tests: read telemetry and embedding writes keep `updated_at` intact.

On PostgreSQL the vector lives in `memories.embedding`, so a Core `UPDATE memories SET embedding=...`
fires the `updated_at` column `onupdate` default unless the statement pins the column. These tests
backdate `updated_at` through raw SQL and assert the repository writes leave it untouched.

Uses a deterministic embedding adapter so no model is needed.
"""
from datetime import UTC, datetime, timedelta
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
    """Deterministic embedding adapter, independent of the configured provider."""

    async def generate_embedding(self, text: str) -> list[float]:
        vector = [0.0] * settings.EMBEDDING_DIMENSIONS
        vector[len(text) % settings.EMBEDDING_DIMENSIONS] = 1.0
        return vector


@pytest_asyncio.fixture(loop_scope="session")
async def memory_repo(db_adapter):
    repo = PostgresMemoryRepository(
        db_adapter=db_adapter,
        embedding_adapter=StubEmbeddings(),
        rerank_adapter=None,
    )
    try:
        yield repo
    finally:
        # re_embed_all resets the vector column; restore the configured dimensions for later tests.
        await repo.reset_embedding_storage()


async def _seed(repo, db_adapter, count=3):
    """Create a user and memories, then backdate `updated_at` to distinct known times."""
    user_id = uuid4()
    now = datetime.now(UTC)
    async with db_adapter.system_session() as session:
        await session.execute(
            text(
                "INSERT INTO users (id, external_id, name, email, created_at, updated_at) "
                "VALUES (:id, :external_id, 'u', :email, :now, :now)",
            ),
            {"id": str(user_id), "external_id": f"ext-{user_id}", "email": f"{user_id}@example.com", "now": now},
        )
    ids = []
    for index in range(count):
        memory = await repo.create_memory(
            user_id=user_id,
            memory=MemoryCreate(
                title=f"Title {index}",
                content=f"Content number {index} about topic {index}",
                context=f"ctx {index}",
                keywords=[f"k{index}"],
                tags=[f"t{index}"],
                importance=7,
            ),
        )
        ids.append(memory.id)
    backdated = {memory_id: datetime(2020, 1, 1, tzinfo=UTC) + timedelta(days=n) for n, memory_id in enumerate(ids)}
    async with db_adapter.system_session() as session:
        for memory_id, updated_at in backdated.items():
            await session.execute(
                text("UPDATE memories SET updated_at = :updated_at WHERE id = :id"),
                {"updated_at": updated_at, "id": memory_id},
            )
    return user_id, backdated


async def _updated_at(repo, user_id, ids):
    return {
        memory_id: (await repo.get_memory_by_id(user_id=user_id, memory_id=memory_id)).updated_at
        for memory_id in ids
    }


@pytest.mark.e2e
async def test_record_memory_access_keeps_updated_at(memory_repo, db_adapter):
    user_id, backdated = await _seed(memory_repo, db_adapter)

    assert await memory_repo.record_memory_access(user_id=user_id, memory_ids=list(backdated)) == len(backdated)

    for memory_id in backdated:
        memory = await memory_repo.get_memory_by_id(user_id=user_id, memory_id=memory_id)
        assert memory.access_count == 1
        assert memory.last_accessed_at is not None
    assert await _updated_at(memory_repo, user_id, backdated) == backdated


@pytest.mark.e2e
async def test_re_embed_all_keeps_updated_at(memory_repo, db_adapter):
    user_id, backdated = await _seed(memory_repo, db_adapter)

    result = await ReEmbeddingService(memory_repo, StubEmbeddings(), batch_size=2).re_embed_all()

    assert result.total_processed == len(backdated)
    assert result.validation.count_ok
    assert await _updated_at(memory_repo, user_id, backdated) == backdated


@pytest.mark.e2e
async def test_rebuild_targeted_keeps_updated_at(memory_repo, db_adapter):
    user_id, backdated = await _seed(memory_repo, db_adapter)

    result = await ReEmbeddingService(memory_repo, StubEmbeddings(), batch_size=10).rebuild_targeted(
        user_id=user_id,
        memory_ids=list(backdated),
    )

    assert sorted(result.rebuilt_ids) == sorted(backdated)
    assert result.failed == []
    assert await _updated_at(memory_repo, user_id, backdated) == backdated


@pytest.mark.e2e
async def test_project_exists_for_user_is_owner_scoped(memory_repo, db_adapter):
    owner_id, _ = await _seed(memory_repo, db_adapter, count=1)
    other_id, _ = await _seed(memory_repo, db_adapter, count=1)
    now = datetime.now(UTC)
    async with db_adapter.system_session() as session:
        project_id = (
            await session.execute(
                text(
                    "INSERT INTO projects (user_id, name, description, project_type, status, created_at, updated_at) "
                    "VALUES (:user_id, 'p', 'd', 'development', 'active', :now, :now) RETURNING id",
                ),
                {"user_id": str(owner_id), "now": now},
            )
        ).scalar_one()

    assert await memory_repo.project_exists_for_user(user_id=owner_id, project_id=project_id)
    assert not await memory_repo.project_exists_for_user(user_id=other_id, project_id=project_id)
    assert not await memory_repo.project_exists_for_user(user_id=owner_id, project_id=project_id + 1000)
