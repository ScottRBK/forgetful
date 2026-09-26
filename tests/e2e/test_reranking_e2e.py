"""End-to-end tests for cross-encoder reranking functionality (PostgreSQL/Docker)

Tests verify that the cross-encoder reranks results based on query context,
not just embedding similarity.

Uses the in-process app and the real PostgreSQL and reranker fixtures.
"""
import pytest

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.asyncio(loop_scope="session"),
]


SETTINGS_OVERRIDE = {
    "RERANKING_ENABLED": True,
    "MEMORY_NUM_AUTO_LINK": 0,
}


def _assert_reranked(result):
    """Public scores prove reranking ran and determine the returned order."""
    memories = result.data["primary_memories"]
    scores = result.data["scores"]
    assert len(memories) == len(scores) == 2
    assert [score["memory_id"] for score in scores] == [memory["id"] for memory in memories]
    reranks = [score["rerank_score"] for score in scores]
    assert all(score is not None for score in reranks)
    assert reranks == sorted(reranks, reverse=True)


async def test_reranking_orders_by_score_e2e(mcp_client):
    """Test that the real cross-encoder supplies scores and orders results.

    Creates 3 database-related memories and requests 2 so reranking must run.
    Uses a context that clearly favors caching/speed.
    Verify the score contract without depending on a particular model's top choice.
    """
    # Create memories with similar embeddings (all about databases)
    # but different focuses that the cross-encoder can distinguish

    # Memory 1: PostgreSQL - relational, ACID, complex queries
    result1 = await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "create_memory", "arguments": {
            "title": "PostgreSQL Database",
            "content": (
                "PostgreSQL is a powerful relational database with ACID compliance, complex "
                "query support, and strong data integrity. Ideal for applications requiring "
                "transactions and complex joins."
            ),
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
            "content": (
                "MongoDB is a document-oriented NoSQL database with flexible schemas and "
                "horizontal scaling. Good for applications with evolving data models and "
                "unstructured data."
            ),
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
            "content": (
                "Redis is an in-memory data store optimized for caching and real-time "
                "applications. Provides sub-millisecond latency and is perfect for session "
                "storage, leaderboards, and rate limiting."
            ),
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
    primary_memories = query_result.data["primary_memories"]
    _assert_reranked(query_result)

    # Get the ranking order
    result_ids = [m["id"] for m in primary_memories]

    assert set(result_ids) <= {postgres_id, mongodb_id, redis_id}


async def test_reranking_with_different_contexts_e2e(mcp_client):
    """Test that different contexts produce different rankings.

    Uses same memories but two different contexts to verify
    the cross-encoder actually influences ranking.
    """
    # Create memories about programming languages
    result1 = await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "create_memory", "arguments": {
            "title": "Python Programming",
            "content": (
                "Python is excellent for data science, machine learning, and AI applications. "
                "Has rich ecosystem with NumPy, Pandas, TensorFlow, and PyTorch."
            ),
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
            "content": (
                "JavaScript is essential for web development, both frontend and backend with "
                "Node.js. React, Vue, and Angular are popular frontend frameworks."
            ),
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
            "content": (
                "Rust provides memory safety and high performance for systems programming. "
                "Ideal for building fast, reliable software without garbage collection."
            ),
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
    # The same dense query with a different context must change rerank output.
    assert query1.data["scores"] != query2.data["scores"]

    # The relevant language must survive selection into the top two for each context.
    assert python_id in result1_ids
    assert js_id in result2_ids
