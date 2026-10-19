"""Real FastEmbed vectors and concurrent REST searches over SQLite."""
import asyncio

import numpy as np
import pytest_asyncio

from app.repositories.embeddings.embedding_adapter import FastEmbeddingAdapter


@pytest_asyncio.fixture
async def embedding_adapter():
    adapter = FastEmbeddingAdapter(providers=["CPUExecutionProvider"], max_concurrency=2)
    try:
        yield adapter
    finally:
        await adapter.aclose()


async def test_real_model_concurrent_vectors_match_sequential(embedding_adapter):
    texts = ["blue ocean", "software architecture", "fresh coffee", "persistent agent memory"]
    sequential = [await embedding_adapter.generate_embedding(text) for text in texts]
    concurrent = await asyncio.gather(*(embedding_adapter.generate_embedding(text) for text in texts))
    assert not np.allclose(sequential[0], sequential[1])
    for expected, actual in zip(sequential, concurrent, strict=True):
        np.testing.assert_allclose(actual, expected, rtol=1e-5, atol=1e-6)


async def test_concurrent_search_returns_correct_request_results(http_client):
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
