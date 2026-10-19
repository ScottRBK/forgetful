"""Concurrent REST searches use real bounded FastEmbed inference and PostgreSQL."""
import asyncio

import pytest
import pytest_asyncio

from app.repositories.embeddings.embedding_adapter import FastEmbeddingAdapter

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio(loop_scope="session")]


@pytest_asyncio.fixture(loop_scope="session")
async def embedding_adapter():
    adapter = FastEmbeddingAdapter(providers=["CPUExecutionProvider"], max_concurrency=2)
    try:
        yield adapter
    finally:
        await adapter.aclose()


def memory_payloads():
    """Unrelated topics make incorrect embedding/result association observable."""
    return [
        {"title": "Sourdough bread", "content": "Bake sourdough bread with flour, water, salt and a fermented starter.",
         "context": "Bread baking recipe", "keywords": ["sourdough", "bread"], "tags": ["cooking"], "importance": 7},
        {"title": "Saturn astronomy", "content": "Saturn is a gas giant planet with icy rings orbiting the Sun.",
         "context": "Solar system astronomy", "keywords": ["Saturn", "planet"], "tags": ["astronomy"], "importance": 8},
        {"title": "PostgreSQL indexing", "content": "PostgreSQL database B-tree indexes accelerate SQL queries on indexed columns.",
         "context": "Database query optimization", "keywords": ["PostgreSQL", "index"], "tags": ["databases"], "importance": 9},
    ]


async def assert_distinct_search_results(http_client, payloads, memory_ids):
    results = await asyncio.gather(*(
        http_client.post("/api/v1/memories/search", json={
            "query": payload["content"], "query_context": payload["context"], "k": 1,
        }) for payload in payloads
    ))
    returned_ids = []
    for payload, memory_id, response in zip(payloads, memory_ids, results, strict=True):
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["query"] == payload["content"]
        assert len(result["primary_memories"]) == 1
        memory = result["primary_memories"][0]
        assert memory["id"] == memory_id
        assert memory["title"] == payload["title"]
        assert memory["content"] == payload["content"]
        returned_ids.append(memory["id"])
    assert len(set(returned_ids)) == len(payloads)


async def test_concurrent_search_returns_distinct_expected_memories(http_client):
    payloads = memory_payloads()
    memory_ids = []
    for payload in payloads:
        response = await http_client.post("/api/v1/memories", json=payload)
        assert response.status_code == 201, response.text
        memory_ids.append(response.json()["id"])
    await assert_distinct_search_results(http_client, payloads, memory_ids)


async def test_concurrent_creation_preserves_each_memory_and_embedding(http_client):
    # Concurrent first requests raced default-user provisioning in the in-memory
    # SQLite harness (InvalidRequestError on refresh; see commit message).
    # Initialize the user first so this test isolates concurrent memory creation.
    response = await http_client.get("/api/v1/memories")
    assert response.status_code == 200, response.text
    payloads = memory_payloads()
    responses = await asyncio.gather(*(
        http_client.post("/api/v1/memories", json=payload) for payload in payloads
    ))
    memory_ids = []
    for payload, response in zip(payloads, responses, strict=True):
        assert response.status_code == 201, response.text
        memory_id = response.json()["id"]
        memory_ids.append(memory_id)
        stored = await http_client.get(f"/api/v1/memories/{memory_id}")
        assert stored.status_code == 200, stored.text
        memory = stored.json()
        for field in ("title", "content", "context", "importance"):
            assert memory[field] == payload[field]
        for field in ("keywords", "tags"):
            assert set(memory[field]) == set(payload[field])
    assert len(set(memory_ids)) == len(payloads)
    # Readback checks rows; semantic search also checks their vector association.
    await assert_distinct_search_results(http_client, payloads, memory_ids)
