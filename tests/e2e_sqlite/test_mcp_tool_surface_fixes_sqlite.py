"""E2E tests for MCP tool-surface argument validation with in-memory SQLite

Covers the document, code artifact, entity, file and project tools reached through
``execute_forgetful_tool``, plus the unmounted legacy skill link/unlink tools.
"""
import base64

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError

from app.routes.mcp import skill_tools

FILE_DATA = base64.b64encode(b"hello").decode("utf-8")


async def call(client, tool_name, **arguments):
    return await client.call_tool(
        "execute_forgetful_tool", {"tool_name": tool_name, "arguments": arguments},
    )


async def make_document(client, tags=None, **extra):
    result = await call(
        client, "create_document", title="doc", description="d", content="c",
        document_type="text", tags=tags or [], **extra,
    )
    return result.data["id"]


async def make_code_artifact(client, tags=None, **extra):
    result = await call(
        client, "create_code_artifact", title="art", description="d", code="print(1)",
        language="python", tags=tags or [], **extra,
    )
    return result.data["id"]


async def make_entity(client, name="ent", tags=None, **extra):
    result = await call(
        client, "create_entity", name=name, entity_type="Organization", tags=tags or [], **extra,
    )
    return result.data["id"]


async def make_file(client, tags=None, **extra):
    result = await call(
        client, "create_file", filename="f.txt", description="d", data=FILE_DATA,
        mime_type="text/plain", tags=tags or [], **extra,
    )
    return result.data["id"]


async def make_project(client, name="proj"):
    result = await call(
        client, "create_project", name=name, description="d", project_type="development",
    )
    return result.data["id"]


async def make_memory(client):
    result = await call(
        client, "create_memory", title="m", content="c", context="ctx",
        keywords=["k"], tags=["t"], importance=7,
    )
    return result.data["id"]


@pytest.mark.asyncio
async def test_update_project_missing_project_is_not_found_error(mcp_client):
    """Updating a project that does not exist is an error, not a successful null result."""
    with pytest.raises(ToolError, match="Project with id 99999 not found"):
        await call(mcp_client, "update_project", project_id=99999, name="x")


@pytest.mark.asyncio
async def test_update_project_existing_project_still_updates(mcp_client):
    project_id = await make_project(mcp_client)

    updated = await call(mcp_client, "update_project", project_id=project_id, name="renamed")

    assert updated.data["id"] == project_id
    assert updated.data["name"] == "renamed"


@pytest.mark.asyncio
async def test_get_entity_relationships_direction_is_normalised_or_rejected(mcp_client):
    """Entity 2 has one incoming and one outgoing edge; direction narrows or errors."""
    first = await make_entity(mcp_client, name="first")
    middle = await make_entity(mcp_client, name="middle")
    last = await make_entity(mcp_client, name="last")
    for source, target in ((first, middle), (middle, last)):
        await call(
            mcp_client, "create_entity_relationship", source_entity_id=source,
            target_entity_id=target, relationship_type="manages",
        )

    async def count(direction):
        result = await call(
            mcp_client, "get_entity_relationships", entity_id=middle, direction=direction,
        )
        return len(result.data["relationships"])

    assert await count("incoming") == 1
    assert await count("outgoing") == 1
    assert await count("Incoming") == 1
    assert await count("OUTGOING") == 1
    assert await count("both") == 2
    assert await count(None) == 2

    for unknown in ("sideways", "in"):
        with pytest.raises(ToolError, match="direction"):
            await count(unknown)


@pytest.fixture
async def legacy_skill_client(sqlite_app, mcp_client):
    """The unmounted legacy skill tool module wired to the real services."""
    legacy = FastMCP("legacy-skill-tools")
    legacy.user_service = sqlite_app.user_service
    legacy.skill_service = sqlite_app.skill_service
    skill_tools.register(legacy)
    async with Client(legacy) as client:
        yield client


@pytest.mark.asyncio
async def test_legacy_skill_unlink_reports_whether_a_link_was_removed(
    legacy_skill_client, mcp_client,
):
    """The legacy tools return the service confirmation, not an always-truthy wrapper."""
    skill = await call(
        mcp_client, "create_skill", name="legacy-skill", description="d", content="# body",
    )
    skill_id = skill.data["id"]
    memory_id = await make_memory(mcp_client)

    linked = await legacy_skill_client.call_tool(
        "link_skill_to_memory", {"skill_id": skill_id, "memory_id": memory_id},
    )
    assert linked.data["skill_id"] == skill_id
    assert linked.data["memory_id"] == memory_id
    assert "success" not in linked.data

    first = await legacy_skill_client.call_tool(
        "unlink_skill_from_memory", {"skill_id": skill_id, "memory_id": memory_id},
    )
    second = await legacy_skill_client.call_tool(
        "unlink_skill_from_memory", {"skill_id": skill_id, "memory_id": memory_id},
    )
    assert first.data["unlinked"] is True
    assert second.data["unlinked"] is False

    never_linked = await legacy_skill_client.call_tool(
        "unlink_skill_from_file", {"skill_id": skill_id, "file_id": 999},
    )
    assert never_linked.data["unlinked"] is False
    assert never_linked.data["file_id"] == 999
