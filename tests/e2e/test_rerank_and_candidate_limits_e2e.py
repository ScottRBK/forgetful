"""PostgreSQL reranked search: honour ``k`` and never hold a connection while awaiting providers.

Runs the real PostgreSQL memory and skill repositories (pgvector, RLS sessions, default
connection pool). Only the embedding provider and the cross-encoder are stubbed.
"""
import asyncio

import pytest

from app.config.settings import settings
from app.models.memory_models import MemoryCreate
from app.models.skill_models import SkillCreate, SkillUpdate
from app.models.user_models import UserCreate
from app.repositories.postgres.memory_repository import PostgresMemoryRepository
from app.repositories.postgres.skill_repository import PostgresSkillRepository
from app.repositories.postgres.user_repository import PostgresUserRepository

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.asyncio(loop_scope="session"),
]

DIMENSIONS = settings.EMBEDDING_DIMENSIONS


class SpyEmbeddings:
    """Every text maps to the same unit vector; records pooled connections in use per call."""

    def __init__(self, pool):
        self.pool = pool
        self.checked_out = []

    async def generate_embedding(self, text):
        self.checked_out.append(self.pool.checkedout())
        vector = [0.0] * DIMENSIONS
        vector[0] = 1.0
        return vector


class SpyReranker:
    """Prefers later candidates; records pooled connections in use and documents per call."""

    def __init__(self, pool, expected_calls=1):
        self.pool = pool
        self.checked_out = []
        self.document_counts = []
        self.all_arrived = asyncio.Event()
        self._expected_calls = expected_calls

    async def rerank(self, query, documents):
        self.checked_out.append(self.pool.checkedout())
        self.document_counts.append(len(documents))
        if len(self.document_counts) >= self._expected_calls:
            self.all_arrived.set()
        await asyncio.wait_for(self.all_arrived.wait(), timeout=10)
        return sorted(
            ((index, float(index)) for index in range(len(documents))),
            key=lambda pair: -pair[1],
        )


@pytest.fixture
async def user_id(db_adapter):
    user = await PostgresUserRepository(db_adapter).create_user(
        UserCreate(external_id="rerank-limits", name="Rerank", email="rerank@example.test"),
    )
    return user.id


@pytest.fixture
def embeddings(db_adapter):
    return SpyEmbeddings(db_adapter._engine.pool)


async def _seed_skills(repo, user_id, count):
    for index in range(count):
        await repo.create_skill(user_id, SkillCreate(
            name=f"skill-{index}", description=f"description {index}", content="body",
        ))


async def test_memory_search_returns_k_when_k_exceeds_dense_candidates(
    db_adapter, user_id, embeddings, monkeypatch,
):
    monkeypatch.setattr(settings, "RERANKING_ENABLED", True)
    monkeypatch.setattr(settings, "DENSE_SEARCH_CANDIDATES", 5)
    monkeypatch.setattr(settings, "MEMORY_NUM_AUTO_LINK", 0)
    repo = PostgresMemoryRepository(db_adapter, embeddings, SpyReranker(embeddings.pool))
    for index in range(12):
        await repo.create_memory(user_id, MemoryCreate(
            title=f"memory {index}", content=f"content {index}", context="context",
            keywords=["k"], tags=["t"], importance=7,
        ))

    found = await repo.search_scored(
        user_id=user_id, query="q", query_context="", k=8,
        importance_threshold=None, project_ids=None, exclude_ids=None,
    )

    assert len(found) == 8


async def test_skill_search_releases_connection_before_reranking(
    db_adapter, user_id, embeddings,
):
    reranker = SpyReranker(embeddings.pool)
    repo = PostgresSkillRepository(db_adapter, embeddings, reranker)
    await _seed_skills(repo, user_id, 6)

    found = await repo.search_skills(user_id, "description", k=2)

    assert len(found) == 2
    assert reranker.document_counts == [6]
    assert reranker.checked_out == [0]


async def test_concurrent_reranked_skill_searches_do_not_exhaust_connection_pool(
    db_adapter, user_id, embeddings,
):
    # More simultaneous searches than the default pool can hand out (5 + 10 overflow).
    searches = 20
    reranker = SpyReranker(embeddings.pool, expected_calls=searches)
    repo = PostgresSkillRepository(db_adapter, embeddings, reranker)
    await _seed_skills(repo, user_id, 6)

    results = await asyncio.gather(
        *(repo.search_skills(user_id, f"description {index}", k=2) for index in range(searches)),
    )

    assert [len(found) for found in results] == [2] * searches
    assert len(reranker.document_counts) == searches


async def test_skill_update_embeds_without_holding_a_connection(db_adapter, user_id, embeddings):
    repo = PostgresSkillRepository(db_adapter, embeddings, None)
    await _seed_skills(repo, user_id, 1)
    skill_id = (await repo.list_skills(user_id))[0].id
    embeddings.checked_out.clear()

    updated = await repo.update_skill(user_id, skill_id, SkillUpdate(description="new description"))

    assert updated.description == "new description"
    assert embeddings.checked_out == [0]
