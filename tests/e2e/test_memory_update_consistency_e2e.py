"""PostgreSQL E2E coverage for update_memory consistency

Covers skill_ids on every memory read path, replacing skill links through PUT, and
how update_memory uses pooled connections while an embedding is being generated.
"""

import asyncio
import hashlib
import random

import pytest
from sqlalchemy import select

from app.config.settings import settings
from app.models.memory_models import MemoryCreate, MemoryUpdate
from app.models.user_models import UserCreate
from app.repositories.postgres.postgres_tables import MemoryTable
from app.utils.embedding_helpers import build_embedding_text

pytestmark = pytest.mark.asyncio(loop_scope="session")

CREATE_BODY = {
    "title": "Memory for update consistency",
    "content": "Original content for update consistency tests.",
    "context": "Update consistency",
    "keywords": ["alpha"],
    "tags": ["test"],
    "importance": 7,
}


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


async def _create_memory(http_client, **extra):
    response = await http_client.post("/api/v1/memories", json={**CREATE_BODY, **extra})
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _get_memory(http_client, memory_id):
    response = await http_client.get(f"/api/v1/memories/{memory_id}")
    assert response.status_code == 200, response.text
    return response.json()


# ============================================================================
# skill_ids round trip
# ============================================================================


@pytest.mark.e2e
async def test_get_memory_reports_linked_skill_ids(http_client):
    skill_id = await _create_skill(http_client, "pg-get-skill")
    memory_id = await _create_memory(http_client, skill_ids=[skill_id])

    assert (await _get_memory(http_client, memory_id))["skill_ids"] == [skill_id]


@pytest.mark.e2e
async def test_put_replaces_and_clears_skill_ids(http_client):
    first = await _create_skill(http_client, "pg-first-skill")
    second = await _create_skill(http_client, "pg-second-skill")
    memory_id = await _create_memory(http_client, skill_ids=[first])

    replaced = await http_client.put(f"/api/v1/memories/{memory_id}", json={"skill_ids": [second]})
    assert replaced.status_code == 200, replaced.text
    assert replaced.json()["skill_ids"] == [second]
    assert (await _get_memory(http_client, memory_id))["skill_ids"] == [second]

    cleared = await http_client.put(f"/api/v1/memories/{memory_id}", json={"skill_ids": []})
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["skill_ids"] == []
    assert (await _get_memory(http_client, memory_id))["skill_ids"] == []


@pytest.mark.e2e
async def test_put_other_field_keeps_skill_links(http_client):
    skill_id = await _create_skill(http_client, "pg-kept-skill")
    memory_id = await _create_memory(http_client, skill_ids=[skill_id])

    response = await http_client.put(f"/api/v1/memories/{memory_id}", json={"title": "Renamed"})

    assert response.status_code == 200, response.text
    assert response.json()["skill_ids"] == [skill_id]
    assert (await _get_memory(http_client, memory_id))["skill_ids"] == [skill_id]


@pytest.mark.e2e
async def test_put_unknown_skill_id_is_not_found_and_keeps_links(http_client):
    skill_id = await _create_skill(http_client, "pg-survivor-skill")
    memory_id = await _create_memory(http_client, skill_ids=[skill_id])

    response = await http_client.put(
        f"/api/v1/memories/{memory_id}", json={"skill_ids": [skill_id + 1000]},
    )

    assert response.status_code == 404, response.text
    assert (await _get_memory(http_client, memory_id))["skill_ids"] == [skill_id]


@pytest.mark.e2e
async def test_search_and_linked_memories_report_skill_ids(http_client):
    skill_id = await _create_skill(http_client, "pg-search-skill")
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


@pytest.mark.e2e
async def test_subgraph_has_memory_skill_edge(http_client):
    skill_id = await _create_skill(http_client, "pg-graph-skill")
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


class ProbeEmbedder:
    """Deterministic text -> vector adapter that mimics a slow remote provider.

    Records how many pooled connections are checked out while a call is in flight.
    """

    def __init__(self, pool, latency=0.0):
        self.pool = pool
        self.latency = latency
        self.checked_out_during_calls: list[int] = []

    @staticmethod
    def vector(value: str) -> list[float]:
        seed = int.from_bytes(hashlib.sha256(value.encode()).digest()[:8], "big")
        rng = random.Random(seed)
        return [rng.uniform(-1.0, 1.0) for _ in range(settings.EMBEDDING_DIMENSIONS)]

    async def generate_embedding(self, text: str) -> list[float]:  # noqa: A002
        self.checked_out_during_calls.append(self.pool.checkedout())
        if self.latency:
            await asyncio.sleep(self.latency)
        return self.vector(text)


async def _embedding_stack(postgres_app, db_adapter, monkeypatch, latency=0.0):
    """Default user, the live memory repository and a probe embedder installed on it."""
    user = await postgres_app.user_service.get_or_create_user(
        UserCreate(
            external_id=settings.DEFAULT_USER_ID,
            name=settings.DEFAULT_USER_NAME,
            email=settings.DEFAULT_USER_EMAIL,
        ),
    )
    repo = postgres_app.memory_service.memory_repo
    embedder = ProbeEmbedder(db_adapter._engine.pool, latency=latency)
    monkeypatch.setattr(repo, "embedding_adapter", embedder)
    memory = await repo.create_memory(
        user.id,
        MemoryCreate(
            title="old title",
            content="old content",
            context="some context",
            keywords=["alpha"],
            tags=["beta"],
            importance=7,
        ),
    )
    embedder.checked_out_during_calls.clear()
    return user, repo, embedder, memory


async def _stored_vector(db_adapter, memory_id):
    async with db_adapter.system_session() as session:
        result = await session.execute(select(MemoryTable.embedding).where(MemoryTable.id == memory_id))
        return [float(value) for value in result.scalar_one()]


def _same_vector(left, right):
    return len(left) == len(right) and all(abs(a - b) < 1e-5 for a, b in zip(left, right, strict=True))


@pytest.mark.e2e
async def test_update_does_not_hold_a_pooled_connection_while_embedding(
    mcp_client, postgres_app, db_adapter, monkeypatch,
):
    user, repo, embedder, memory = await _embedding_stack(postgres_app, db_adapter, monkeypatch)
    baseline = db_adapter._engine.pool.checkedout()

    updated = await repo.update_memory(
        user_id=user.id,
        memory_id=memory.id,
        updated_memory=MemoryUpdate(content="changed content"),
        existing_memory=memory,
        search_fields_changed=True,
    )

    assert updated.content == "changed content"
    assert embedder.checked_out_during_calls == [baseline]


@pytest.mark.e2e
async def test_concurrent_updates_of_different_fields_keep_embedding_in_sync(
    mcp_client, postgres_app, db_adapter, monkeypatch,
):
    user, repo, embedder, memory = await _embedding_stack(
        postgres_app, db_adapter, monkeypatch, latency=0.3,
    )

    await asyncio.gather(
        postgres_app.memory_service.update_memory(user.id, memory.id, MemoryUpdate(title="new title")),
        postgres_app.memory_service.update_memory(user.id, memory.id, MemoryUpdate(content="new content")),
    )

    final = await repo.get_memory_by_id(user_id=user.id, memory_id=memory.id)
    assert (final.title, final.content) == ("new title", "new content")
    expected = ProbeEmbedder.vector(build_embedding_text(final))
    assert _same_vector(await _stored_vector(db_adapter, memory.id), expected)


@pytest.mark.e2e
async def test_updates_beyond_the_pool_size_do_not_starve_other_requests(
    mcp_client, postgres_app, db_adapter, monkeypatch,
):
    """More slow embedding updates than the pool has connections must leave the pool free."""
    user, repo, embedder, memory = await _embedding_stack(
        postgres_app, db_adapter, monkeypatch, latency=2.0,
    )
    pool = db_adapter._engine.pool
    capacity = pool.size() + pool._max_overflow
    updates = [
        asyncio.create_task(
            repo.update_memory(
                user_id=user.id,
                memory_id=memory.id,
                updated_memory=MemoryUpdate(content=f"content {number}"),
                existing_memory=memory,
                search_fields_changed=True,
            ),
        )
        for number in range(capacity + 5)
    ]
    try:
        await asyncio.sleep(0.5)

        assert pool.checkedout() == 0
        await asyncio.wait_for(repo.get_memory_by_id(user_id=user.id, memory_id=memory.id), timeout=1.0)
    finally:
        await asyncio.gather(*updates, return_exceptions=True)
