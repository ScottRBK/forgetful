"""Reranked search honours ``k`` against the real SQLite repositories (sqlite-vec, no Docker).

Only the embedding provider and the cross-encoder are stubbed, so these tests drive the real
candidate fetch, rerank hand-off and truncation in ``search_scored`` and ``search_skills``.
"""

import pytest

from app.config.settings import settings
from app.models.memory_models import MemoryCreate
from app.models.skill_models import SkillCreate
from app.models.user_models import UserCreate
from app.repositories.sqlite.memory_repository import SqliteMemoryRepository
from app.repositories.sqlite.skill_repository import SqliteSkillRepository
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter
from app.repositories.sqlite.user_repository import SqliteUserRepository

DIMENSIONS = settings.EMBEDDING_DIMENSIONS


class FixedEmbeddings:
    """Every text maps to the same unit vector, so every row matches every query."""

    async def generate_embedding(self, text):
        vector = [0.0] * DIMENSIONS
        vector[0] = 1.0
        return vector


class RecordingReranker:
    """Scores later candidates higher and remembers how many documents it was given."""

    def __init__(self):
        self.document_counts = []

    async def rerank(self, query, documents):
        self.document_counts.append(len(documents))
        return sorted(
            ((index, float(index)) for index in range(len(documents))),
            key=lambda pair: -pair[1],
        )


@pytest.fixture
async def sqlite_env(monkeypatch):
    monkeypatch.setattr(settings, "DATABASE", "SQLite")
    monkeypatch.setattr(settings, "SQLITE_MEMORY", True)
    monkeypatch.setattr(settings, "RERANKING_ENABLED", True)
    monkeypatch.setattr(settings, "MEMORY_NUM_AUTO_LINK", 0)
    adapter = SqliteDatabaseAdapter()
    await adapter.init_db()
    user = await SqliteUserRepository(db_adapter=adapter).create_user(
        UserCreate(external_id="rerank-limits", name="Rerank", email="rerank@example.test"),
    )
    try:
        yield adapter, user.id
    finally:
        await adapter.dispose()


@pytest.fixture
def reranker():
    return RecordingReranker()


async def _memories(adapter, user_id, reranker, count, embeddings=None):
    repo = SqliteMemoryRepository(
        db_adapter=adapter,
        embedding_adapter=embeddings or FixedEmbeddings(),
        rerank_adapter=reranker,
    )
    for index in range(count):
        await repo.create_memory(user_id, MemoryCreate(
            title=f"memory {index}", content=f"content {index}", context="context",
            keywords=["k"], tags=["t"], importance=7,
        ))
    return repo


async def _skills(adapter, user_id, reranker, count):
    repo = SqliteSkillRepository(
        db_adapter=adapter, embedding_adapter=FixedEmbeddings(), rerank_adapter=reranker,
    )
    for index in range(count):
        await repo.create_skill(user_id, SkillCreate(
            name=f"skill-{index}", description=f"description {index}", content="body",
        ))
    return repo


async def _search_memories(repo, user_id, k):
    return await repo.search_scored(
        user_id=user_id, query="q", query_context="", k=k,
        importance_threshold=None, project_ids=None, exclude_ids=None,
    )


async def test_memory_search_returns_k_when_k_exceeds_dense_candidates(
    sqlite_env, monkeypatch, reranker,
):
    adapter, user_id = sqlite_env
    monkeypatch.setattr(settings, "DENSE_SEARCH_CANDIDATES", 5)
    repo = await _memories(adapter, user_id, reranker, 12)

    found = await _search_memories(repo, user_id, k=8)

    assert len(found) == 8


async def test_memory_search_returns_every_match_when_fewer_than_k(
    sqlite_env, monkeypatch, reranker,
):
    adapter, user_id = sqlite_env
    monkeypatch.setattr(settings, "DENSE_SEARCH_CANDIDATES", 5)
    repo = await _memories(adapter, user_id, reranker, 6)

    found = await _search_memories(repo, user_id, k=8)

    assert len(found) == 6


async def test_memory_search_still_reranks_when_k_is_within_dense_candidates(
    sqlite_env, monkeypatch, reranker,
):
    adapter, user_id = sqlite_env
    monkeypatch.setattr(settings, "DENSE_SEARCH_CANDIDATES", 5)
    repo = await _memories(adapter, user_id, reranker, 8)

    found = await _search_memories(repo, user_id, k=3)

    assert reranker.document_counts == [5]
    assert len(found) == 3
    assert all(score.rerank_score is not None for _, score in found)


async def test_skill_search_returns_k_when_k_exceeds_dense_candidates(
    sqlite_env, monkeypatch, reranker,
):
    adapter, user_id = sqlite_env
    monkeypatch.setattr(settings, "DENSE_SEARCH_CANDIDATES", 5)
    repo = await _skills(adapter, user_id, reranker, 12)

    found = await repo.search_skills(user_id, "description", k=8)

    assert len(found) == 8


async def test_skill_search_returns_every_match_when_fewer_than_k(
    sqlite_env, monkeypatch, reranker,
):
    adapter, user_id = sqlite_env
    monkeypatch.setattr(settings, "DENSE_SEARCH_CANDIDATES", 5)
    repo = await _skills(adapter, user_id, reranker, 6)

    found = await repo.search_skills(user_id, "description", k=8)

    assert len(found) == 6


async def test_skill_search_still_reranks_when_k_is_within_dense_candidates(
    sqlite_env, monkeypatch, reranker,
):
    adapter, user_id = sqlite_env
    monkeypatch.setattr(settings, "DENSE_SEARCH_CANDIDATES", 5)
    repo = await _skills(adapter, user_id, reranker, 8)

    found = await repo.search_skills(user_id, "description", k=3)

    assert reranker.document_counts == [5]
    assert len(found) == 3


