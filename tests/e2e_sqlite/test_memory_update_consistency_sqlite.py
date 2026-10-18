"""E2E tests (SQLite) for update_memory consistency

Covers skill_ids round-tripping on every read path and the embedding written by
update_memory.
"""
import asyncio
import hashlib
import random
import struct
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.config.settings import settings
from app.exceptions import NotFoundError
from app.models.memory_models import MemoryCreate, MemoryUpdate
from app.models.user_models import UserCreate
from app.repositories.sqlite.memory_repository import SqliteMemoryRepository
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter
from app.repositories.sqlite.user_repository import SqliteUserRepository
from app.services.memory_service import MemoryService
from app.utils.embedding_helpers import build_embedding_text

CREATE_BODY = {
    "title": "Original title",
    "content": "Original content for update consistency tests.",
    "context": "Original context",
    "keywords": ["alpha", "beta"],
    "tags": ["t1"],
    "importance": 7,
    "source_repo": "owner/repo",
    "source_url": "https://example.com/x",
}


async def _create_memory(http_client, **extra):
    response = await http_client.post("/api/v1/memories", json={**CREATE_BODY, **extra})
    assert response.status_code == 201, response.text
    return response.json()["id"]


# ============================================================================
# skill_ids round trip
# ============================================================================


async def _create_skill(http_client, name):
    response = await http_client.post(
        "/api/v1/skills",
        json={
            "name": name,
            "description": f"Skill {name}",
            "content": "# Steps\n1. Do the thing",
            "tags": ["test"],
            "importance": 7,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _get_memory(http_client, memory_id):
    response = await http_client.get(f"/api/v1/memories/{memory_id}")
    assert response.status_code == 200, response.text
    return response.json()


async def _listed_skill_ids(http_client, memory_id):
    response = await http_client.get("/api/v1/memories")
    assert response.status_code == 200, response.text
    return next(m["skill_ids"] for m in response.json()["memories"] if m["id"] == memory_id)


async def test_get_memory_reports_linked_skill_ids(http_client):
    skill_id = await _create_skill(http_client, "get-skill")
    memory_id = await _create_memory(http_client, skill_ids=[skill_id])

    assert (await _get_memory(http_client, memory_id))["skill_ids"] == [skill_id]
    assert await _listed_skill_ids(http_client, memory_id) == [skill_id]


async def test_put_replaces_skill_ids(http_client):
    first = await _create_skill(http_client, "first-skill")
    second = await _create_skill(http_client, "second-skill")
    memory_id = await _create_memory(http_client, skill_ids=[first])

    response = await http_client.put(f"/api/v1/memories/{memory_id}", json={"skill_ids": [second]})

    assert response.status_code == 200, response.text
    assert response.json()["skill_ids"] == [second]
    assert (await _get_memory(http_client, memory_id))["skill_ids"] == [second]
    assert await _listed_skill_ids(http_client, memory_id) == [second]


async def test_put_links_skills_to_memory_without_any(http_client):
    skill_id = await _create_skill(http_client, "late-skill")
    memory_id = await _create_memory(http_client)

    response = await http_client.put(f"/api/v1/memories/{memory_id}", json={"skill_ids": [skill_id]})

    assert response.status_code == 200, response.text
    assert response.json()["skill_ids"] == [skill_id]
    assert (await _get_memory(http_client, memory_id))["skill_ids"] == [skill_id]


async def test_put_empty_skill_ids_clears_links(http_client):
    skill_id = await _create_skill(http_client, "cleared-skill")
    memory_id = await _create_memory(http_client, skill_ids=[skill_id])

    response = await http_client.put(f"/api/v1/memories/{memory_id}", json={"skill_ids": []})

    assert response.status_code == 200, response.text
    assert response.json()["skill_ids"] == []
    assert (await _get_memory(http_client, memory_id))["skill_ids"] == []
    assert await _listed_skill_ids(http_client, memory_id) == []


async def test_put_other_field_keeps_skill_links_in_response_and_storage(http_client):
    skill_id = await _create_skill(http_client, "kept-skill")
    memory_id = await _create_memory(http_client, skill_ids=[skill_id])

    response = await http_client.put(f"/api/v1/memories/{memory_id}", json={"title": "Renamed"})

    assert response.status_code == 200, response.text
    assert response.json()["title"] == "Renamed"
    assert response.json()["skill_ids"] == [skill_id]
    assert (await _get_memory(http_client, memory_id))["skill_ids"] == [skill_id]


async def test_put_unknown_skill_id_is_not_found_and_keeps_links(http_client):
    skill_id = await _create_skill(http_client, "survivor-skill")
    memory_id = await _create_memory(http_client, skill_ids=[skill_id])

    response = await http_client.put(
        f"/api/v1/memories/{memory_id}", json={"skill_ids": [skill_id + 1000]},
    )

    assert response.status_code == 404, response.text
    assert (await _get_memory(http_client, memory_id))["skill_ids"] == [skill_id]


async def test_search_and_linked_memories_report_skill_ids(http_client):
    skill_id = await _create_skill(http_client, "search-skill")
    skilled_id = await _create_memory(
        http_client,
        title="Skilled memory about espresso machines",
        content="Descaling an espresso machine every three months keeps it healthy.",
        skill_ids=[skill_id],
    )
    primary_id = await _create_memory(
        http_client,
        title="Volcano hiking boots",
        content="Waterproof boots with a stiff sole are best for volcano trails.",
    )
    linked = await http_client.post(
        f"/api/v1/memories/{primary_id}/links", json={"related_ids": [skilled_id]},
    )
    assert linked.status_code == 200, linked.text

    response = await http_client.post(
        "/api/v1/memories/search",
        json={
            "query": "waterproof boots for volcano trails",
            "query_context": "choosing hiking gear",
            "k": 1,
            "include_links": 1,
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert [m["id"] for m in body["primary_memories"]] == [primary_id]
    assert [(lm["memory"]["id"], lm["memory"]["skill_ids"]) for lm in body["linked_memories"]] == [
        (skilled_id, [skill_id]),
    ]

    primary_hit = await http_client.post(
        "/api/v1/memories/search",
        json={
            "query": "descaling an espresso machine",
            "query_context": "kitchen appliance care",
            "k": 1,
            "include_links": 0,
        },
    )
    assert primary_hit.status_code == 200, primary_hit.text
    assert [(m["id"], m["skill_ids"]) for m in primary_hit.json()["primary_memories"]] == [
        (skilled_id, [skill_id]),
    ]


async def test_subgraph_has_memory_skill_edge(http_client):
    skill_id = await _create_skill(http_client, "graph-skill")
    memory_id = await _create_memory(http_client, skill_ids=[skill_id])

    response = await http_client.get(
        f"/api/v1/graph/subgraph?node_id=memory_{memory_id}&node_types=memory,skill",
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert f"skill_{skill_id}" in {node["id"] for node in body["nodes"]}
    assert [edge for edge in body["edges"] if edge["type"] == "memory_skill"], body["edges"]


# ============================================================================
# Embedding written by update_memory
# ============================================================================


class RecordingEmbedder:
    """Deterministic text -> vector adapter that mimics a remote provider.

    latency: seconds each call takes, so concurrent updates overlap like real network calls
    before_return: optional coroutine run on every call, used to change the row mid-embedding
    """

    def __init__(self):
        self.latency = 0.0
        self.calls = 0
        self.open_sessions = lambda: 0
        self.sessions_open_during_calls: list[int] = []
        self.before_return = None

    @staticmethod
    def vector(value: str) -> list[float]:
        seed = int.from_bytes(hashlib.sha256(value.encode()).digest()[:8], "big")
        rng = random.Random(seed)
        return [rng.uniform(-1.0, 1.0) for _ in range(settings.EMBEDDING_DIMENSIONS)]

    async def generate_embedding(self, text: str) -> list[float]:  # noqa: A002
        self.calls += 1
        self.sessions_open_during_calls.append(self.open_sessions())
        if self.latency:
            await asyncio.sleep(self.latency)
        if self.before_return is not None:
            await self.before_return(self.calls)
        return self.vector(text)


@pytest.fixture
async def embedding_stack(tmp_path, monkeypatch):
    """Service and repository on a file backed SQLite database.

    Concurrent writers need separate connections, which the shared in-memory database
    used by the other fixtures does not provide.
    """
    monkeypatch.setattr(settings, "DATABASE", "SQLite")
    monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "forgetful.db"))

    db = SqliteDatabaseAdapter()
    await db.init_db()

    embedder = RecordingEmbedder()
    open_sessions = 0
    real_session = db.session

    @asynccontextmanager
    async def counting_session(user_id):
        nonlocal open_sessions
        open_sessions += 1
        try:
            async with real_session(user_id) as session:
                yield session
        finally:
            open_sessions -= 1

    monkeypatch.setattr(db, "session", counting_session)
    embedder.open_sessions = lambda: open_sessions

    repo = SqliteMemoryRepository(db_adapter=db, embedding_adapter=embedder, rerank_adapter=None)
    service = MemoryService(repo, event_bus=None)
    user = await SqliteUserRepository(db).create_user(
        UserCreate(external_id=f"ext-{uuid4()}", name="Embedding Tester", email="embed@example.com"),
    )
    try:
        yield service, repo, db, embedder, user.id
    finally:
        await db.dispose()


async def _create_embedded_memory(service, embedder, user_id):
    created = await service.create_memory(
        user_id=user_id,
        memory_data=MemoryCreate(
            title="old title",
            content="old content",
            context="some context",
            keywords=["alpha"],
            tags=["beta"],
            importance=7,
        ),
    )
    memory = created.memory
    embedder.calls = 0
    embedder.sessions_open_during_calls.clear()
    return memory


async def _stored_vector(db, memory_id):
    async with db.system_session() as session:
        row = (
            await session.execute(
                text("SELECT embedding FROM vec_memories WHERE memory_id = :memory_id"),
                {"memory_id": str(memory_id)},
            )
        ).one()
    raw = row[0]
    return list(struct.unpack(f"{len(raw) // 4}f", raw))


def _same_vector(left, right):
    return len(left) == len(right) and all(abs(a - b) < 1e-5 for a, b in zip(left, right, strict=True))


async def _assert_embedding_matches_row(repo, db, user_id, memory_id):
    final = await repo.get_memory_by_id(user_id=user_id, memory_id=memory_id)
    expected = RecordingEmbedder.vector(build_embedding_text(final))
    assert _same_vector(await _stored_vector(db, memory_id), expected), (
        f"stored embedding does not match the stored row (title={final.title!r}, content={final.content!r})"
    )
    return final


async def test_update_memory_embeds_before_opening_a_database_session(embedding_stack):
    service, _repo, _db, embedder, user_id = embedding_stack
    memory = await _create_embedded_memory(service, embedder, user_id)

    await service.update_memory(user_id, memory.id, MemoryUpdate(content="new content"))

    assert embedder.sessions_open_during_calls == [0]


async def test_sequential_updates_keep_embedding_in_sync(embedding_stack):
    service, repo, db, embedder, user_id = embedding_stack
    memory = await _create_embedded_memory(service, embedder, user_id)

    await service.update_memory(user_id, memory.id, MemoryUpdate(title="new title"))
    await service.update_memory(user_id, memory.id, MemoryUpdate(content="new content"))

    final = await _assert_embedding_matches_row(repo, db, user_id, memory.id)
    assert (final.title, final.content) == ("new title", "new content")


async def test_concurrent_updates_of_different_fields_keep_embedding_in_sync(embedding_stack):
    service, repo, db, embedder, user_id = embedding_stack
    memory = await _create_embedded_memory(service, embedder, user_id)
    embedder.latency = 0.2

    await asyncio.gather(
        service.update_memory(user_id, memory.id, MemoryUpdate(title="new title")),
        service.update_memory(user_id, memory.id, MemoryUpdate(content="new content")),
    )

    final = await _assert_embedding_matches_row(repo, db, user_id, memory.id)
    assert (final.title, final.content) == ("new title", "new content")


async def test_burst_of_concurrent_updates_keeps_embedding_in_sync(embedding_stack):
    service, repo, db, embedder, user_id = embedding_stack
    memory = await _create_embedded_memory(service, embedder, user_id)
    embedder.latency = 0.1

    await asyncio.gather(
        service.update_memory(user_id, memory.id, MemoryUpdate(title="burst title")),
        service.update_memory(user_id, memory.id, MemoryUpdate(content="burst content")),
        service.update_memory(user_id, memory.id, MemoryUpdate(context="burst context")),
        service.update_memory(user_id, memory.id, MemoryUpdate(keywords=["burst"])),
    )

    final = await _assert_embedding_matches_row(repo, db, user_id, memory.id)
    assert (final.title, final.content, final.context, final.keywords) == (
        "burst title", "burst content", "burst context", ["burst"],
    )


async def test_concurrent_updates_of_same_field_keep_embedding_in_sync(embedding_stack):
    service, repo, db, embedder, user_id = embedding_stack
    memory = await _create_embedded_memory(service, embedder, user_id)
    embedder.latency = 0.2

    await asyncio.gather(
        service.update_memory(user_id, memory.id, MemoryUpdate(title="first title")),
        service.update_memory(user_id, memory.id, MemoryUpdate(title="second title", tags=["gamma"])),
    )

    final = await _assert_embedding_matches_row(repo, db, user_id, memory.id)
    assert final.tags == ["gamma"]
    assert final.title in {"first title", "second title"}


async def test_update_still_succeeds_when_the_row_keeps_changing_during_embedding(embedding_stack):
    """Sustained contention must end in a successful update, not an error or an endless loop."""
    service, repo, db, embedder, user_id = embedding_stack
    memory = await _create_embedded_memory(service, embedder, user_id)

    async def change_title_behind_the_update(call_number):
        async with db.system_session() as session:
            await session.execute(
                text("UPDATE memories SET title = :title WHERE id = :memory_id"),
                {"title": f"interfering title {call_number}", "memory_id": memory.id},
            )

    embedder.before_return = change_title_behind_the_update

    result = await asyncio.wait_for(
        service.update_memory(user_id, memory.id, MemoryUpdate(content="new content")),
        timeout=30,
    )

    assert result.memory.content == "new content"
    assert 2 <= embedder.calls <= 5
    stored = await repo.get_memory_by_id(user_id=user_id, memory_id=memory.id)
    assert stored.content == "new content"


async def test_update_of_missing_memory_raises_not_found_without_touching_vectors(embedding_stack):
    service, repo, db, embedder, user_id = embedding_stack
    memory = await _create_embedded_memory(service, embedder, user_id)

    with pytest.raises(NotFoundError):
        await repo.update_memory(
            user_id=user_id,
            memory_id=memory.id + 1000,
            updated_memory=MemoryUpdate(title="ghost"),
            existing_memory=memory,
            search_fields_changed=True,
        )

    async with db.system_session() as session:
        count = (await session.execute(text("SELECT COUNT(*) FROM vec_memories"))).scalar()
    assert count == 1
