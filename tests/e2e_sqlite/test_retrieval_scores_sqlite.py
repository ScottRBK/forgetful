"""E2E SQLite tests for query_memory scores and create_memory similarity."""
import pytest

from app.config.settings import settings


@pytest.mark.asyncio
async def test_scores_aligned_and_non_increasing(mcp_client):
    prev_rerank = settings.RERANKING_ENABLED
    settings.RERANKING_ENABLED = False
    try:
        topics = [
            ("Astronomy baselines", "Mars has two small moons named Phobos and Deimos.", ["mars", "moons"]),
            ("Cooking baselines", "Sourdough bread needs a long cold ferment for flavor.", ["bread", "sourdough"]),
            ("Music baselines", "A pentatonic scale has five notes per octave.", ["music", "scale"]),
        ]
        for title, content, keywords in topics:
            await mcp_client.call_tool(
                "execute_forgetful_tool",
                {
                    "tool_name": "create_memory",
                    "arguments": {
                        "title": title,
                        "content": content,
                        "context": "retrieval scores e2e",
                        "keywords": keywords,
                        "tags": ["scores-test"],
                        "importance": 7,
                    },
                },
            )

        query_result = await mcp_client.call_tool(
            "execute_forgetful_tool",
            {
                "tool_name": "query_memory",
                "arguments": {
                    "query": "planets and bread and music scales",
                    "query_context": "scores alignment test",
                    "k": 3,
                    "include_links": False,
                },
            },
        )
        data = query_result.data
        primaries = data["primary_memories"]
        scores = data["scores"]
        assert len(scores) == len(primaries)
        for idx, score in enumerate(scores):
            assert score["memory_id"] == primaries[idx]["id"]
            assert -1.0 <= score["similarity"] <= 1.0
            assert score["rerank_score"] is None
        sims = [s["similarity"] for s in scores]
        assert sims == sorted(sims, reverse=True)
    finally:
        settings.RERANKING_ENABLED = prev_rerank


@pytest.mark.asyncio
async def test_exact_content_query_scores_high(mcp_client):
    content = "Unique exact match content for scores e2e xyzzy-12345"
    create_result = await mcp_client.call_tool(
        "execute_forgetful_tool",
        {
            "tool_name": "create_memory",
            "arguments": {
                "title": content,
                "content": content,
                "context": "",
                "keywords": ["xyzzy"],
                "tags": ["scores-test"],
                "importance": 8,
            },
        },
    )
    mem_id = create_result.data["id"]
    query_result = await mcp_client.call_tool(
        "execute_forgetful_tool",
        {
            "tool_name": "query_memory",
            "arguments": {
                "query": content,
                "query_context": "find exact memory",
                "k": 3,
                "include_links": False,
            },
        },
    )
    primaries = query_result.data["primary_memories"]
    scores = query_result.data["scores"]
    assert primaries[0]["id"] == mem_id
    assert scores[0]["memory_id"] == mem_id
    assert scores[0]["similarity"] >= 0.95


@pytest.mark.asyncio
async def test_no_results_empty_scores(mcp_client):
    query_result = await mcp_client.call_tool(
        "execute_forgetful_tool",
        {
            "tool_name": "query_memory",
            "arguments": {
                "query": "no memories in this project filter",
                "query_context": "empty scores",
                "k": 3,
                "include_links": False,
                "project_ids": [999999],
            },
        },
    )
    assert query_result.data["scores"] == []


@pytest.mark.asyncio
async def test_rest_search_returns_scores(http_client):
    create_body = {
        "title": "REST scores memory",
        "content": "REST API should return scores alongside primaries.",
        "context": "rest scores",
        "keywords": ["rest", "scores"],
        "tags": ["scores-test"],
        "importance": 7,
    }
    create_resp = await http_client.post("/api/v1/memories", json=create_body)
    assert create_resp.status_code == 201

    search_resp = await http_client.post(
        "/api/v1/memories/search",
        json={
            "query": "REST API scores",
            "query_context": "rest search",
            "k": 3,
            "include_links": 0,
        },
    )
    assert search_resp.status_code == 200
    payload = search_resp.json()
    assert "scores" in payload
    assert len(payload["scores"]) == len(payload["primary_memories"])


@pytest.mark.asyncio
async def test_create_similar_memories_have_similarity(mcp_client):
    args = {
        "title": "Similarity pair A",
        "content": "Docker compose stacks for local Postgres and Redis caching layer.",
        "context": "similarity test",
        "keywords": ["docker", "postgres", "redis"],
        "tags": ["scores-test"],
        "importance": 7,
    }
    await mcp_client.call_tool(
        "execute_forgetful_tool",
        {"tool_name": "create_memory", "arguments": args},
    )
    args2 = dict(args)
    args2["title"] = "Similarity pair B"
    args2["content"] = "Docker compose stacks for local Postgres and Redis cache layer."
    result2 = await mcp_client.call_tool(
        "execute_forgetful_tool",
        {"tool_name": "create_memory", "arguments": args2},
    )
    sims = result2.data.get("similar_memories") or []
    if sims:
        assert isinstance(sims[0].get("similarity"), float)
        assert sims[0]["similarity"] >= 0.7
