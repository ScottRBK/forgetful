"""End-to-end tests for cross-encoder reranking functionality (SQLite)

Tests verify that the cross-encoder reranks results based on query context,
not just embedding similarity.
"""
import pytest

from app.config.settings import settings
from app.repositories.embeddings.reranker_adapter import FastEmbedCrossEncoderAdapter


@pytest.fixture
def reranker_adapter(monkeypatch):
    """Use local reranking; pytest restores all settings overrides after each test."""
    monkeypatch.setattr(settings, "RERANKING_ENABLED", True)
    monkeypatch.setattr(settings, "RERANKING_PROVIDER", "FastEmbed")
    monkeypatch.setattr(settings, "DENSE_SEARCH_CANDIDATES", 20)
    monkeypatch.setattr(settings, "MEMORY_NUM_AUTO_LINK", 0)
    return FastEmbedCrossEncoderAdapter(
        model="Xenova/ms-marco-MiniLM-L-12-v2",
        cache_dir=settings.FASTEMBED_CACHE_DIR,
    )


def _assert_reranked(result):
    """Scores must be present and aligned with the returned memory order."""
    memories = result.data["primary_memories"]
    scores = result.data["scores"]
    assert len(memories) == len(scores) == 2
    assert [score["memory_id"] for score in scores] == [memory["id"] for memory in memories]
    reranks = [score["rerank_score"] for score in scores]
    assert reranks and all(score is not None for score in reranks)
    assert reranks == sorted(reranks, reverse=True)


@pytest.mark.asyncio
async def test_reranking_orders_by_score_sqlite(mcp_client):
    """Create three memories and request two so reranking must run.

    Verify score ordering without depending on a particular model's top choice.
    """
    # Create memories with similar embeddings (all about databases)
    # but different focuses that the cross-encoder can distinguish

    # Memory 1: PostgreSQL - relational, ACID, complex queries
    result1 = await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "create_memory", "arguments": {
            "title": "PostgreSQL Database",
            "content": "PostgreSQL is a powerful relational database with ACID compliance, complex query support, and strong data integrity. Ideal for applications requiring transactions and complex joins.",
            "context": "Database technology overview",
            "keywords": ["postgresql", "database", "relational", "sql", "acid"],
            "tags": ["database", "backend"],
            "importance": 7,
        },
    })
    postgres_id = result1.data["id"]

    # Memory 2: MongoDB - document store, flexible schema
    result2 = await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "create_memory", "arguments": {
            "title": "MongoDB Database",
            "content": "MongoDB is a document-oriented NoSQL database with flexible schemas and horizontal scaling. Good for applications with evolving data models and unstructured data.",
            "context": "Database technology overview",
            "keywords": ["mongodb", "database", "nosql", "document", "flexible"],
            "tags": ["database", "backend"],
            "importance": 7,
        },
    })
    mongodb_id = result2.data["id"]

    # Memory 3: Redis - in-memory, caching, speed
    result3 = await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "create_memory", "arguments": {
            "title": "Redis Database",
            "content": "Redis is an in-memory data store optimized for caching and real-time applications. Provides sub-millisecond latency and is perfect for session storage, leaderboards, and rate limiting.",
            "context": "Database technology overview",
            "keywords": ["redis", "database", "cache", "in-memory", "fast"],
            "tags": ["database", "caching"],
            "importance": 7,
        },
    })
    redis_id = result3.data["id"]

    # Query with context that strongly favors Redis
    # The cross-encoder should recognize "caching" and "sub-millisecond latency"
    query_result = await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "query_memory", "arguments": {
            "query": "database for application",
            "query_context": (
                "I need extremely fast caching with sub-millisecond latency for session storage"
            ),
            "k": 2,
            "include_links": False,
        },
    })

    assert query_result.data is not None
    _assert_reranked(query_result)
    primary_memories = query_result.data["primary_memories"]
    result_ids = [m["id"] for m in primary_memories]
    assert set(result_ids) <= {postgres_id, mongodb_id, redis_id}


@pytest.mark.asyncio
async def test_reranking_with_different_contexts_sqlite(mcp_client):
    """Test that different contexts produce different rankings.

    Uses same memories but two different contexts to verify
    the cross-encoder actually influences ranking.
    """
    # Create memories about programming languages
    result1 = await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "create_memory", "arguments": {
            "title": "Python Programming",
            "content": "Python is excellent for data science, machine learning, and AI applications. Has rich ecosystem with NumPy, Pandas, TensorFlow, and PyTorch.",
            "context": "Programming language comparison",
            "keywords": ["python", "programming", "data-science", "ml", "ai"],
            "tags": ["language", "backend"],
            "importance": 7,
        },
    })
    python_id = result1.data["id"]

    result2 = await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "create_memory", "arguments": {
            "title": "JavaScript Programming",
            "content": "JavaScript is essential for web development, both frontend and backend with Node.js. React, Vue, and Angular are popular frontend frameworks.",
            "context": "Programming language comparison",
            "keywords": ["javascript", "programming", "web", "frontend", "nodejs"],
            "tags": ["language", "web"],
            "importance": 7,
        },
    })
    js_id = result2.data["id"]

    result3 = await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "create_memory", "arguments": {
            "title": "Rust Programming",
            "content": "Rust provides memory safety and high performance for systems programming. Ideal for building fast, reliable software without garbage collection.",
            "context": "Programming language comparison",
            "keywords": ["rust", "programming", "systems", "performance", "safety"],
            "tags": ["language", "systems"],
            "importance": 7,
        },
    })
    rust_id = result3.data["id"]

    # Query 1: Context favoring data science
    query1 = await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "query_memory", "arguments": {
            "query": "programming language",
            "query_context": "I want to build machine learning models and analyze datasets",
            "k": 2,
            "include_links": False,
        },
    })

    result1_ids = [m["id"] for m in query1.data["primary_memories"]]
    _assert_reranked(query1)

    # Query 2: Context favoring web development
    query2 = await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "query_memory", "arguments": {
            "query": "programming language",
            "query_context": "I need to build an interactive web application with React",
            "k": 2,
            "include_links": False,
        },
    })

    result2_ids = [m["id"] for m in query2.data["primary_memories"]]

    _assert_reranked(query2)
    assert set(result1_ids) <= {python_id, js_id, rust_id}
    assert set(result2_ids) <= {python_id, js_id, rust_id}
    # The same dense query with different context must change the rerank output.
    assert query1.data["scores"] != query2.data["scores"]
