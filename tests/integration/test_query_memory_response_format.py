"""Unit tests for query_memory response_format validation and projection (no DB)."""

import inspect
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from app.models.memory_models import (
    LinkedMemory,
    Memory,
    MemoryQueryCompactResult,
    MemoryQueryResult,
    MemoryScore,
    parse_query_memory_response_format,
)
from app.routes.mcp import memory_tools
from app.routes.mcp.query_memory_format import (
    project_query_memory_result,
    require_query_memory_response_format,
)
from app.routes.mcp.tool_adapters import MemoryToolAdapters


def _full_result() -> MemoryQueryResult:
    memory = Memory(
        id=41,
        title="Python testing",
        content="Use pytest fixtures",
        context="Unit test fixture",
        keywords=["python", "pytest"],
        tags=["testing"],
        importance=8,
        project_ids=[7],
    )
    return MemoryQueryResult(
        query="python testing",
        primary_memories=[memory],
        linked_memories=[LinkedMemory(memory=memory, link_source_id=41)],
        scores=[
            MemoryScore(memory_id=41, similarity=0.91, rerank_score=0.4, fusion_score=0.7),
        ],
        total_count=2,
        token_count=12,
        truncated=False,
    )


@pytest.mark.parametrize("value", ["full", "compact"])
def test_parse_query_memory_response_format_accepts_known_values(value):
    assert parse_query_memory_response_format(value) == value


def test_parse_query_memory_response_format_rejects_unknown_without_transport_prefix():
    with pytest.raises(ValueError, match="response_format") as excinfo:
        parse_query_memory_response_format("tiny")
    assert "VALIDATION_ERROR" not in str(excinfo.value)


def test_require_query_memory_response_format_raises_tool_validation_error():
    with pytest.raises(ToolError, match="^VALIDATION_ERROR: response_format"):
        require_query_memory_response_format("tiny")


def test_project_query_memory_result_full_returns_same_instance():
    result = _full_result()
    assert project_query_memory_result(result, "full") is result


def test_project_query_memory_result_compact_projects_keys():
    projected = project_query_memory_result(_full_result(), "compact")
    assert isinstance(projected, MemoryQueryCompactResult)
    primary_keys = {"id", "title", "content", "context", "importance", "tags", "project_ids"}
    assert set(projected.primary_memories[0].model_dump().keys()) == primary_keys
    linked = projected.linked_memories[0].model_dump()
    assert set(linked.keys()) == primary_keys | {"link_source_id"}
    assert "memory" not in linked
    assert projected.scores[0].model_dump() == {
        "memory_id": 41,
        "similarity": 0.91,
        "fusion_score": 0.7,
    }
    assert projected.query == "python testing"
    assert projected.total_count == 2


def test_project_query_memory_result_compact_omits_fusion_score_without_hybrid():
    result = _full_result()
    result.scores = [MemoryScore(memory_id=41, similarity=0.91, rerank_score=None)]
    projected = project_query_memory_result(result, "compact")
    assert projected.scores[0].model_dump() == {"memory_id": 41, "similarity": 0.91}


@pytest.mark.asyncio
async def test_adapter_query_memory_rejects_invalid_format_before_service_call():
    memory_service = MagicMock()
    memory_service.query_memory = AsyncMock()
    adapters = MemoryToolAdapters(
        memory_service=memory_service,
        user_service=MagicMock(),
        re_embedding_service=MagicMock(),
    )

    with pytest.raises(ToolError, match="^VALIDATION_ERROR: response_format"):
        await adapters.query_memory(
            query="python testing",
            query_context="invalid format",
            ctx=MagicMock(),
            response_format="tiny",
        )

    memory_service.query_memory.assert_not_awaited()


@pytest.mark.asyncio
async def test_mcp_tool_query_memory_rejects_invalid_format_before_service_call():
    mcp = FastMCP("query-memory-format-test")
    memory_tools.register(mcp)
    tool = mcp.get_tool("query_memory")
    if inspect.isawaitable(tool):
        tool = await tool

    memory_service = MagicMock()
    memory_service.query_memory = AsyncMock()
    ctx = SimpleNamespace(fastmcp=SimpleNamespace(memory_service=memory_service))

    with pytest.raises(ToolError, match="^VALIDATION_ERROR: response_format"):
        await tool.fn(
            query="python testing",
            query_context="invalid format",
            ctx=ctx,
            response_format="tiny",
        )

    memory_service.query_memory.assert_not_awaited()
