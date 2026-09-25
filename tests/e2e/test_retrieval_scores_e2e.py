"""Postgres e2e tests for retrieval scores."""

import pytest

from app.config.settings import settings

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.asyncio(loop_scope="session"),
]


@pytest.mark.asyncio
async def test_scores_aligned_and_non_increasing(mcp_client):
    prev_rerank = settings.RERANKING_ENABLED
    settings.RERANKING_ENABLED = False
    try:
        for title, content, keywords in [
            (
                "Pg scores A",
                "Kubernetes operators manage custom resources in clusters.",
                ["k8s", "operator"],
            ),
            (
                "Pg scores B",
                "Italian pasta dough rests before rolling thin sheets.",
                ["pasta", "dough"],
            ),
            (
                "Pg scores C",
                "Chess endgames favor rook and pawn structures.",
                ["chess", "endgame"],
            ),
        ]:
            await mcp_client.call_tool(
                "execute_forgetful_tool",
                {
                    "tool_name": "create_memory",
                    "arguments": {
                        "title": title,
                        "content": content,
                        "context": "pg scores",
                        "keywords": keywords,
                        "tags": ["pg-scores"],
                        "importance": 7,
                    },
                },
            )
        query_result = await mcp_client.call_tool(
            "execute_forgetful_tool",
            {
                "tool_name": "query_memory",
                "arguments": {
                    "query": "kubernetes pasta chess",
                    "query_context": "pg scores test",
                    "k": 3,
                    "include_links": False,
                },
            },
        )
        primaries = query_result.data["primary_memories"]
        scores = query_result.data["scores"]
        assert len(scores) == len(primaries)
        sims = [s["similarity"] for s in scores]
        assert sims == sorted(sims, reverse=True)
    finally:
        settings.RERANKING_ENABLED = prev_rerank


@pytest.mark.asyncio
async def test_rerank_scores_present_and_ordered(mcp_client):
    prev = settings.RERANKING_ENABLED
    settings.RERANKING_ENABLED = True
    try:
        project_result = await mcp_client.call_tool(
            "execute_forgetful_tool",
            {
                "tool_name": "create_project",
                "arguments": {
                    "name": "Rerank scores isolation project",
                    "description": "Isolates rerank score e2e memories from other tests",
                    "project_type": "development",
                },
            },
        )
        project_id = project_result.data["id"]

        for title, content, keywords in [
            (
                "PostgreSQL Database",
                "PostgreSQL relational ACID database.",
                ["postgresql", "database"],
            ),
            (
                "MongoDB Database",
                "MongoDB document NoSQL database.",
                ["mongodb", "database"],
            ),
            (
                "Redis Database",
                "Redis in-memory cache database fast.",
                ["redis", "database", "cache"],
            ),
            (
                "MySQL Database",
                "MySQL relational database for web applications and replication.",
                ["mysql", "database", "relational"],
            ),
        ]:
            await mcp_client.call_tool(
                "execute_forgetful_tool",
                {
                    "tool_name": "create_memory",
                    "arguments": {
                        "title": title,
                        "content": content,
                        "context": "rerank scores",
                        "keywords": keywords,
                        "tags": ["pg-scores"],
                        "importance": 7,
                        "project_ids": [project_id],
                    },
                },
            )
        query_result = await mcp_client.call_tool(
            "execute_forgetful_tool",
            {
                "tool_name": "query_memory",
                "arguments": {
                    "query": "database for application",
                    "query_context": "caching sub-millisecond latency session storage",
                    "k": 3,
                    "include_links": False,
                    "project_ids": [project_id],
                },
            },
        )
        scores = query_result.data["scores"]
        assert len(scores) == 3
        reranks = [s["rerank_score"] for s in scores]
        assert all(r is not None for r in reranks)
        assert reranks == sorted(reranks, reverse=True)
    finally:
        settings.RERANKING_ENABLED = prev
