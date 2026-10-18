"""Reranked search honours ``k`` against the real SQLite repositories (sqlite-vec, no Docker).

Only the embedding provider and the cross-encoder are stubbed, so these tests drive the real
candidate fetch, rerank hand-off and truncation in ``search_scored`` and ``search_skills``.
"""
import json
import math
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from app.config.settings import settings
from app.models.memory_models import MemoryCreate
from app.models.skill_models import SkillCreate
from app.models.user_models import UserCreate
from app.repositories.embeddings.reranker_adapter import HttpRerankAdapter
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


class AngleEmbeddings:
    """The query sits at angle 0 and memories at increasing angles (alpha is closest)."""

    ANGLES = {"alpha": 0.1, "beta": 0.5, "BESTMATCH": 1.0}

    async def generate_embedding(self, text):
        angle = 0.0
        for key, theta in self.ANGLES.items():
            if key in text:
                angle = theta
        vector = [0.0] * DIMENSIONS
        vector[0] = math.cos(angle)
        vector[1] = math.sin(angle)
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


class _IndexOrderRerankHandler(BaseHTTPRequestHandler):
    """A /v1/rerank server that answers in document order instead of score order."""

    def do_POST(self):  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        results = [
            {"index": index, "relevance_score": 0.95 if "BESTMATCH" in document else 0.05}
            for index, document in enumerate(body["documents"])
        ]
        payload = json.dumps({"results": results}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


@pytest.fixture
def index_order_rerank_url():
    server = HTTPServer(("127.0.0.1", 0), _IndexOrderRerankHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1/rerank"
    finally:
        server.shutdown()
        server.server_close()


async def test_http_reranker_answering_in_document_order_still_picks_best_match(
    sqlite_env, monkeypatch, index_order_rerank_url,
):
    adapter, user_id = sqlite_env
    monkeypatch.setattr(settings, "DENSE_SEARCH_CANDIDATES", 20)
    repo = SqliteMemoryRepository(
        db_adapter=adapter,
        embedding_adapter=AngleEmbeddings(),
        rerank_adapter=HttpRerankAdapter(model="m", url=index_order_rerank_url, api_key=""),
    )
    for word in ("alpha", "beta", "BESTMATCH"):
        await repo.create_memory(user_id, MemoryCreate(
            title=f"{word} memory", content=f"content about {word}", context="context",
            keywords=[word], tags=["t"], importance=7,
        ))

    found = await _search_memories(repo, user_id, k=1)

    assert len(found) == 1
    memory, score = found[0]
    assert "BESTMATCH" in memory.title
    assert score.rerank_score == pytest.approx(0.95)
