"""E2E tests for entity write-path integrity with real PostgreSQL

Covers the PostgreSQL repository paths touched by the integrity fixes:
- unknown project_ids are rejected and never wipe existing links
- the unique relationship index surfaces as a conflict (409 / clean tool error)
- the merged entity_type/custom_type state is validated before the write
"""
import pytest
from fastmcp.exceptions import ToolError

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _call_tool(mcp_client, tool_name: str, arguments: dict):
    return await mcp_client.call_tool(
        "execute_forgetful_tool", {"tool_name": tool_name, "arguments": arguments},
    )


@pytest.mark.e2e
async def test_update_entity_with_unknown_project_keeps_links_e2e(mcp_client):
    project = await _call_tool(mcp_client, "create_project", {
        "name": "real", "description": "Real project", "project_type": "development",
    })
    project_id = project.data["id"]
    created = await _call_tool(mcp_client, "create_entity", {
        "name": "e", "entity_type": "Team", "project_ids": [project_id],
    })
    entity_id = created.data["id"]

    with pytest.raises(ToolError, match="Projects not found"):
        await _call_tool(mcp_client, "update_entity", {
            "entity_id": entity_id, "project_ids": [999999],
        })

    fetched = await _call_tool(mcp_client, "get_entity", {"entity_id": entity_id})
    assert fetched.data["project_ids"] == [project_id]


@pytest.mark.e2e
async def test_create_entity_with_unknown_project_is_rejected_e2e(mcp_client, http_client):
    response = await http_client.post("/api/v1/entities", json={
        "name": "orphan", "entity_type": "Team", "project_ids": [999999],
    })

    assert response.status_code == 404
    assert "Projects not found" in response.json()["error"]
    listed = await http_client.get("/api/v1/entities")
    assert listed.json()["entities"] == []


@pytest.mark.e2e
async def test_duplicate_relationship_returns_409_e2e(http_client):
    source = (await http_client.post(
        "/api/v1/entities", json={"name": "A", "entity_type": "Organization"},
    )).json()
    target = (await http_client.post(
        "/api/v1/entities", json={"name": "B", "entity_type": "Organization"},
    )).json()
    url = f"/api/v1/entities/{source['id']}/relationships"
    body = {"target_entity_id": target["id"], "relationship_type": "owns"}

    first = await http_client.post(url, json=body)
    duplicate = await http_client.post(url, json=body)
    manages = await http_client.post(url, json={**body, "relationship_type": "manages"})

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert "already exists" in duplicate.json()["error"]
    assert manages.status_code == 201

    collision = await http_client.put(
        f"/api/v1/entities/relationships/{manages.json()['id']}",
        json={"relationship_type": "owns"},
    )
    assert collision.status_code == 409


@pytest.mark.e2e
async def test_duplicate_relationship_tool_error_is_clean_e2e(mcp_client):
    source = await _call_tool(mcp_client, "create_entity", {"name": "A", "entity_type": "Team"})
    target = await _call_tool(mcp_client, "create_entity", {"name": "B", "entity_type": "Team"})
    arguments = {
        "source_entity_id": source.data["id"],
        "target_entity_id": target.data["id"],
        "relationship_type": "owns",
    }
    await _call_tool(mcp_client, "create_entity_relationship", arguments)

    with pytest.raises(ToolError, match="already exists") as excinfo:
        await _call_tool(mcp_client, "create_entity_relationship", arguments)

    assert "duplicate key" not in str(excinfo.value)


@pytest.mark.e2e
async def test_custom_type_update_is_validated_before_write_e2e(mcp_client):
    created = await _call_tool(mcp_client, "create_entity", {
        "name": "mq", "entity_type": "Other", "custom_type": "Middleware",
    })
    entity_id = created.data["id"]

    with pytest.raises(ToolError, match="custom_type is required"):
        await _call_tool(mcp_client, "update_entity", {
            "entity_id": entity_id, "custom_type": "",
        })
    fetched = await _call_tool(mcp_client, "get_entity", {"entity_id": entity_id})
    assert fetched.data["custom_type"] == "Middleware"

    await _call_tool(mcp_client, "update_entity", {
        "entity_id": entity_id, "entity_type": "Team",
    })
    listed = await _call_tool(mcp_client, "list_entities", {})
    entity = next(e for e in listed.data["entities"] if e["id"] == entity_id)
    assert entity["entity_type"] == "Team"
    assert entity["custom_type"] is None
