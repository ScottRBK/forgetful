"""E2E tests for query_memory response_format (full vs compact)."""

import pytest
from fastmcp.exceptions import ToolError

from app.config.settings import settings

_QUERY_MEMORY_FULL_PRIMARY_KEYS = frozenset({
    "id",
    "title",
    "content",
    "keywords",
    "created_at",
    "access_count",
})

_QUERY_MEMORY_COMPACT_PRIMARY_KEYS = frozenset({
    "id",
    "title",
    "content",
    "context",
    "importance",
    "tags",
    "project_ids",
})

_QUERY_MEMORY_COMPACT_LINKED_KEYS = _QUERY_MEMORY_COMPACT_PRIMARY_KEYS | {
    "link_source_id",
}

_QUERY_MEMORY_COMPACT_SCORE_KEYS = frozenset({"memory_id", "similarity"})
_QUERY_MEMORY_COMPACT_HYBRID_SCORE_KEYS = _QUERY_MEMORY_COMPACT_SCORE_KEYS | {"fusion_score"}


async def _seed_query_memory_fixture(mcp_client):
    """Create a memory suitable for query_memory response_format tests."""
    return await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "create_memory",
        "arguments": {
            "title": "Python Testing Best Practices",
            "content": (
                "Use pytest for testing Python applications with fixtures and parametrization"
            ),
            "context": "Testing semantic search in E2E environment",
            "keywords": ["python", "pytest", "testing"],
            "tags": ["testing", "best-practices"],
            "importance": 8,
        },
    })


async def _query_memory_for_format_tests(mcp_client, response_format=None):
    await _seed_query_memory_fixture(mcp_client)
    arguments = {
        "query": "python testing practices",
        "query_context": "looking for testing information",
        "k": 5,
        "include_links": False,
    }
    if response_format is not None:
        arguments["response_format"] = response_format
    return await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "query_memory",
        "arguments": arguments,
    })


@pytest.mark.asyncio
async def test_query_memory_default_response_format_is_full_e2e(mcp_client):
    """Default query_memory returns full primary memory payloads."""
    query_result = await _query_memory_for_format_tests(mcp_client)
    assert query_result.data is not None
    assert len(query_result.data["primary_memories"]) > 0
    primary_keys = set(query_result.data["primary_memories"][0].keys())
    assert _QUERY_MEMORY_FULL_PRIMARY_KEYS <= primary_keys


@pytest.mark.asyncio
async def test_query_memory_explicit_full_matches_default_e2e(mcp_client):
    """response_format=full matches the default key sets."""
    default_result = await _query_memory_for_format_tests(mcp_client)
    full_result = await _query_memory_for_format_tests(
        mcp_client, response_format="full",
    )
    assert default_result.data is not None
    assert full_result.data is not None
    for idx, primary in enumerate(default_result.data["primary_memories"]):
        assert set(primary.keys()) == set(
            full_result.data["primary_memories"][idx].keys(),
        )
    for idx, score in enumerate(default_result.data["scores"]):
        assert set(score.keys()) == set(full_result.data["scores"][idx].keys())
    if default_result.data["linked_memories"]:
        for idx, linked in enumerate(default_result.data["linked_memories"]):
            assert set(linked.keys()) == set(
                full_result.data["linked_memories"][idx].keys(),
            )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("hybrid_enabled", "expected_score_keys"),
    [
        (False, _QUERY_MEMORY_COMPACT_SCORE_KEYS),
        (True, _QUERY_MEMORY_COMPACT_HYBRID_SCORE_KEYS),
    ],
)
async def test_query_memory_compact_response_format_e2e(
    mcp_client, monkeypatch, hybrid_enabled, expected_score_keys,
):
    """response_format=compact projects memories, links, and scores."""
    monkeypatch.setattr(settings, "HYBRID_SEARCH_ENABLED", hybrid_enabled)
    result1 = await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "create_memory",
        "arguments": {
            "title": "PostgreSQL Database",
            "content": "PostgreSQL is a powerful open-source relational database",
            "context": "Testing compact linked memory retrieval",
            "keywords": ["postgresql", "database", "sql"],
            "tags": ["database"],
            "importance": 8,
        },
    })
    assert result1.data is not None
    memory1_id = result1.data["id"]

    result2 = await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "create_memory",
        "arguments": {
            "title": "PostgreSQL Indexing",
            "content": "PostgreSQL supports various index types including B-tree and GIN",
            "context": "Testing compact linked memory retrieval with auto-linking",
            "keywords": ["postgresql", "indexing", "performance"],
            "tags": ["database", "performance"],
            "importance": 7,
        },
    })
    memory2_id = result2.data["id"]
    await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "link_memories",
        "arguments": {"memory_id": memory1_id, "related_ids": [memory2_id]},
    })

    query_result = await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "query_memory",
        "arguments": {
            "query": "PostgreSQL Database",
            "query_context": "testing compact response_format",
            "k": 1,
            "include_links": True,
            "max_links_per_primary": 5,
            "response_format": "compact",
        },
    })
    assert query_result.data is not None
    assert query_result.data["query"] == "PostgreSQL Database"
    assert isinstance(query_result.data["total_count"], int)
    assert isinstance(query_result.data["token_count"], int)
    assert isinstance(query_result.data["truncated"], bool)

    assert len(query_result.data["primary_memories"]) > 0
    for primary in query_result.data["primary_memories"]:
        assert set(primary.keys()) == _QUERY_MEMORY_COMPACT_PRIMARY_KEYS

    assert len(query_result.data["linked_memories"]) > 0
    for linked in query_result.data["linked_memories"]:
        assert set(linked.keys()) == _QUERY_MEMORY_COMPACT_LINKED_KEYS
        assert "memory" not in linked
        assert isinstance(linked["link_source_id"], int)

    scores = query_result.data["scores"]
    primaries = query_result.data["primary_memories"]
    assert len(scores) == len(primaries)
    for score in scores:
        assert set(score.keys()) == expected_score_keys


@pytest.mark.asyncio
async def test_query_memory_rejects_invalid_response_format_e2e(mcp_client):
    """Invalid response_format values fail validation instead of returning full payloads."""
    await _seed_query_memory_fixture(mcp_client)
    with pytest.raises(ToolError, match="response_format"):
        await mcp_client.call_tool("execute_forgetful_tool", {
            "tool_name": "query_memory",
            "arguments": {
                "query": "python testing practices",
                "query_context": "invalid response_format test",
                "k": 5,
                "include_links": False,
                "response_format": "tiny",
            },
        })
