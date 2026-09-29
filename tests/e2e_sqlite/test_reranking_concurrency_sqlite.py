"""Check shared-model result isolation through REST, not database throughput."""
import asyncio
from threading import Barrier, Lock

import pytest
from fastembed.rerank.cross_encoder import TextCrossEncoder

from app.config.settings import settings
from app.repositories.embeddings.reranker_adapter import FastEmbedCrossEncoderAdapter


@pytest.fixture
def reranker_adapter(monkeypatch):
    """Use a known local model even when the environment configures an HTTP model.

    Configuration wiring is covered by test_local_reranker_concurrency.py.
    """
    monkeypatch.setattr(settings, "RERANKING_ENABLED", True)
    monkeypatch.setattr(settings, "RERANKING_PROVIDER", "FastEmbed")
    monkeypatch.setattr(settings, "DENSE_SEARCH_CANDIDATES", 20)
    monkeypatch.setattr(settings, "MEMORY_NUM_AUTO_LINK", 0)
    return FastEmbedCrossEncoderAdapter(
        model="Xenova/ms-marco-MiniLM-L-12-v2",
        threads=4,
        workers=2,
        cache_dir=settings.FASTEMBED_CACHE_DIR,
    )


async def test_concurrent_searches_match_sequential_rankings(http_client, monkeypatch):
    memories = [
        ("Redis", "Redis offers fast in-memory caching and session storage."),
        ("PostgreSQL", "PostgreSQL supports ACID transactions and relational SQL queries."),
        ("Python", "Python supports machine learning and data science with NumPy and PyTorch."),
        (
            "Rust",
            "Rust provides memory safety and fast systems programming without garbage collection.",
        ),
    ]
    for title, content in memories:
        response = await http_client.post("/api/v1/memories", json={
            "title": title,
            "content": content,
            "context": "Technology comparison",
            "keywords": [title.lower()],
            "tags": ["concurrent-reranking"],
            "importance": 7,
        })
        assert response.status_code == 201

    requests = [
        {"query": "database", "query_context": "Fast caching for session storage"},
        {"query": "programming language", "query_context": "Training machine learning models"},
        {"query": "database", "query_context": "ACID transactions and relational queries"},
    ]

    async def search(request):
        response = await http_client.post(
            "/api/v1/memories/search", json={**request, "k": 2, "include_links": False},
        )
        assert response.status_code == 200
        payload = response.json()
        scores = payload["scores"]
        ids = [memory["id"] for memory in payload["primary_memories"]]
        assert len(ids) == len(scores) == 2
        assert [score["memory_id"] for score in scores] == ids
        reranks = [score["rerank_score"] for score in scores]
        assert all(score is not None for score in reranks)
        assert reranks == sorted(reranks, reverse=True)
        return ids, reranks

    sequential = [await search(request) for request in requests]

    # Require two real model calls in flight, not just overlapping HTTP requests.
    # A single worker times out at the gate instead of silently passing serially.
    rendezvous = Barrier(2, timeout=5)
    lock = Lock()
    started = 0
    real_rerank = TextCrossEncoder.rerank

    def synchronized_rerank(model, *args, **kwargs):
        nonlocal started
        with lock:
            paired = started < 2
            started += 1
        if paired:
            rendezvous.wait()
        try:
            return list(real_rerank(model, *args, **kwargs))
        finally:
            if paired:
                rendezvous.wait()

    monkeypatch.setattr(TextCrossEncoder, "rerank", synchronized_rerank)
    concurrent = await asyncio.gather(*(search(request) for request in requests))

    for (expected_ids, expected_scores), (actual_ids, actual_scores) in zip(
        sequential, concurrent, strict=True,
    ):
        assert actual_ids == expected_ids
        assert actual_scores == pytest.approx(expected_scores, rel=1e-5, abs=1e-6)
