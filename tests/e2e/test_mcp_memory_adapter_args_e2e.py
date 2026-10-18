"""Postgres e2e tests for argument handling in the memory tool adapters.

The PostgreSQL repository shares the sort handling changed for the memory listing, so
these tests exercise it against a real database: sort options are case-insensitive,
unknown values raise instead of silently falling back, and textual booleans are parsed.
"""
import json
from uuid import uuid4

import pytest
from fastmcp.exceptions import ToolError

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.asyncio(loop_scope="session"),
]


async def _exec(client, tool_name, arguments):
    return await client.call_tool(
        "execute_forgetful_tool",
        {"tool_name": tool_name, "arguments": arguments},
    )


async def _create_memory(client, title, **extra):
    arguments = {
        "title": title,
        "content": f"content for {title}",
        "context": "adapter argument handling",
        "keywords": ["adapter-args"],
        "tags": ["pg-adapter-args"],
        "importance": 5,
    }
    arguments.update(extra)
    result = await _exec(client, "create_memory", arguments)
    return json.loads(result.content[0].text)["id"]


async def _recent_ids(client, **arguments):
    result = await _exec(client, "get_recent_memories", {"tags": ["pg-adapter-args"], **arguments})
    return [m["id"] for m in json.loads(result.content[0].text)["memories"]]


@pytest.mark.asyncio
@pytest.mark.parametrize("sort_order", ["desc", "DESC", " Desc "])
async def test_sort_order_desc_is_case_insensitive_e2e(mcp_client, sort_order):
    ids = [await _create_memory(mcp_client, f"pg sort {i}") for i in range(3)]

    assert await _recent_ids(mcp_client, sort_order=sort_order) == ids[::-1]


@pytest.mark.asyncio
@pytest.mark.parametrize("sort_order", ["asc", "ASC"])
async def test_sort_order_asc_is_case_insensitive_e2e(mcp_client, sort_order):
    ids = [await _create_memory(mcp_client, f"pg sort {i}") for i in range(3)]

    assert await _recent_ids(mcp_client, sort_order=sort_order) == ids


@pytest.mark.asyncio
async def test_sort_by_importance_is_case_insensitive_e2e(mcp_client):
    first = await _create_memory(mcp_client, "pg importance low", importance=3)
    second = await _create_memory(mcp_client, "pg importance high", importance=9)
    third = await _create_memory(mcp_client, "pg importance mid", importance=6)

    ids = await _recent_ids(mcp_client, sort_by="IMPORTANCE", sort_order="DESC")

    assert ids == [second, third, first]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"sort_order": "descending"}, "sort_order must be one of: asc, desc"),
        ({"sort_order": "newest"}, "sort_order must be one of: asc, desc"),
        ({"sort_by": "bogus"}, "sort_by must be one of: created_at, updated_at, importance"),
    ],
)
async def test_invalid_sort_options_are_rejected_e2e(mcp_client, arguments, message):
    await _create_memory(mcp_client, "pg sort invalid")

    with pytest.raises(ToolError, match=message):
        await _exec(mcp_client, "get_recent_memories", arguments)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("sort_by", "sort_order", "message"),
    [
        ("bogus", "desc", "sort_by must be one of"),
        ("created_at", "DESC", "sort_order must be one of"),
        ("created_at", "newest", "sort_order must be one of"),
    ],
)
async def test_repository_refuses_unknown_sort_options_instead_of_falling_back_e2e(
    mcp_client, postgres_app, sort_by, sort_order, message,
):
    # mcp_client starts the app lifespan, which attaches the services
    repo = postgres_app.memory_service.memory_repo

    with pytest.raises(ValueError, match=message):
        await repo.list_memories(user_id=uuid4(), limit=10, sort_by=sort_by, sort_order=sort_order)


@pytest.mark.asyncio
@pytest.mark.parametrize("include_obsolete", ["false", "False", "0", "no", False])
async def test_include_obsolete_false_strings_hide_obsolete_memories_e2e(mcp_client, include_obsolete):
    memory_id = await _create_memory(mcp_client, "pg obsolete")
    await _exec(mcp_client, "mark_memory_obsolete", {"memory_id": memory_id, "reason": "test"})

    assert await _recent_ids(mcp_client, include_obsolete=include_obsolete) == []
    assert await _recent_ids(mcp_client, include_obsolete="true") == [memory_id]


@pytest.mark.asyncio
async def test_string_project_id_filters_on_that_project_e2e(mcp_client):
    project_ids = []
    for i in range(12):
        result = await _exec(mcp_client, "create_project", {
            "name": f"pg-adapter-args-project-{i}",
            "description": f"project {i}",
            "project_type": "development",
        })
        project_ids.append(json.loads(result.content[0].text)["id"])
    in_last = await _create_memory(mcp_client, "pg in last", project_ids=[project_ids[11]])
    await _create_memory(mcp_client, "pg in first", project_ids=[project_ids[0]])
    await _create_memory(mcp_client, "pg in second", project_ids=[project_ids[1]])

    assert await _recent_ids(mcp_client, project_ids=str(project_ids[11])) == [in_last]
