"""E2E tests (in-memory SQLite) for argument handling in the memory tool adapters.

`execute_forgetful_tool` passes free-form arguments straight to the adapters, so the
sort options of get_recent_memories must be validated further down. These tests drive
the real stack (FastMCP client -> registry -> adapter -> service -> SQLite) and cover
case-insensitive and validated sort_by / sort_order.
"""
import json
from uuid import uuid4

import pytest
from fastmcp.exceptions import ToolError

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def disable_auto_linking():
    """Keep manual link/unlink assertions free of auto-linking side effects"""
    from app.config.settings import settings
    original_value = settings.MEMORY_NUM_AUTO_LINK
    settings.MEMORY_NUM_AUTO_LINK = 0
    yield
    settings.MEMORY_NUM_AUTO_LINK = original_value


async def _exec(client, tool_name, arguments):
    return await client.call_tool(
        "execute_forgetful_tool",
        {"tool_name": tool_name, "arguments": arguments},
    )


def _payload(result):
    return json.loads(result.content[0].text)


async def _create_memory(client, title, **extra):
    arguments = {
        "title": title,
        "content": f"content for {title}",
        "context": "adapter argument handling",
        "keywords": ["adapter-args"],
        "tags": ["adapter-args"],
        "importance": 5,
    }
    arguments.update(extra)
    return _payload(await _exec(client, "create_memory", arguments))["id"]


async def _create_projects(client, count):
    ids = []
    for i in range(count):
        result = await _exec(client, "create_project", {
            "name": f"adapter-args-project-{i}",
            "description": f"project {i}",
            "project_type": "development",
        })
        ids.append(_payload(result)["id"])
    return ids


async def _recent_ids(client, **arguments):
    result = await _exec(client, "get_recent_memories", arguments)
    return [m["id"] for m in _payload(result)["memories"]]


# ---------------------------------------------------------------------------
# sort_by / sort_order: case-insensitive, validated, never silently reversed
# ---------------------------------------------------------------------------

@pytest.fixture
async def three_memories(mcp_client):
    """Memories created oldest to newest with importance 3, 9 and 6."""
    return [
        await _create_memory(mcp_client, f"sort {i}", importance=importance)
        for i, importance in enumerate((3, 9, 6))
    ]


@pytest.mark.parametrize("sort_order", ["desc", "DESC", "Desc", " desc ", "desc\n"])
async def test_sort_order_desc_is_case_insensitive_and_returns_newest_first(mcp_client, three_memories, sort_order):
    assert await _recent_ids(mcp_client, sort_order=sort_order) == three_memories[::-1]


@pytest.mark.parametrize("sort_order", ["asc", "ASC", " Asc "])
async def test_sort_order_asc_is_case_insensitive_and_returns_oldest_first(mcp_client, three_memories, sort_order):
    assert await _recent_ids(mcp_client, sort_order=sort_order) == three_memories


async def test_sort_by_is_case_insensitive(mcp_client, three_memories):
    first, second, third = three_memories

    ids = await _recent_ids(mcp_client, sort_by="Importance", sort_order="DESC")

    assert ids == [second, third, first]


@pytest.mark.parametrize("sort_order", ["descending", "newest", "", None, 5])
async def test_invalid_sort_order_is_rejected(mcp_client, three_memories, sort_order):
    with pytest.raises(ToolError, match="sort_order must be one of: asc, desc"):
        await _exec(mcp_client, "get_recent_memories", {"sort_order": sort_order})


@pytest.mark.parametrize("sort_by", ["bogus", "createdat", "", None, 5])
async def test_invalid_sort_by_is_rejected(mcp_client, three_memories, sort_by):
    with pytest.raises(ToolError, match="sort_by must be one of: created_at, updated_at, importance"):
        await _exec(mcp_client, "get_recent_memories", {"sort_by": sort_by})


@pytest.mark.parametrize(
    ("sort_by", "sort_order", "message"),
    [
        ("bogus", "desc", "sort_by must be one of"),
        ("created_at", "DESC", "sort_order must be one of"),
        ("created_at", "newest", "sort_order must be one of"),
    ],
)
async def test_repository_refuses_unknown_sort_options_instead_of_falling_back(
    mcp_client, sqlite_app, sort_by, sort_order, message,
):
    # mcp_client starts the app lifespan, which attaches the services
    repo = sqlite_app.memory_service.memory_repo

    with pytest.raises(ValueError, match=message):
        await repo.list_memories(user_id=uuid4(), limit=10, sort_by=sort_by, sort_order=sort_order)
