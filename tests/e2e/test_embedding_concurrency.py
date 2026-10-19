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


async def test_concurrent_postgres_search_keeps_results_associated(http_client):
    response = await http_client.post("/api/v1/memories", json={
        "title": "Concurrent embedding search",
        "content": "Persistent memory for software agents",
        "context": "Concurrency regression",
        "keywords": ["memory", "agent"], "tags": ["test"], "importance": 7,
    })
    assert response.status_code == 201
    queries = ["persistent memory", "software agents", "memory for agents", "agent memory"]
    results = await asyncio.gather(*(
        http_client.post("/api/v1/memories/search", json={"query": query, "query_context": "Concurrency regression", "k": 1})
        for query in queries
    ))
    for query, result in zip(queries, results, strict=True):
        assert result.status_code == 200
        assert result.json()["query"] == query
        assert result.json()["primary_memories"][0]["title"] == "Concurrent embedding search"
