"""E2E tests for MCP tool-surface argument validation with in-memory SQLite

Covers the document, code artifact, entity, file and project tools reached through
``execute_forgetful_tool``, plus the unmounted legacy skill link/unlink tools.
"""
import base64

import pytest
from fastmcp.exceptions import ToolError

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
