"""E2E tests for entity write-path integrity with in-memory SQLite.

Covers the full stack (REST routes -> EntityService -> SqliteEntityRepository):
- updates validate the merged entity_type/custom_type state before writing
"""
import pytest
from fastmcp.exceptions import ToolError


async def _create_entity(http_client, **payload) -> dict:
    payload.setdefault("entity_type", "Organization")
    response = await http_client.post("/api/v1/entities", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# ----------------------------------------------------------------------------
# entity_type / custom_type consistency on update
# ----------------------------------------------------------------------------


class TestCustomTypeConsistency:
    @pytest.mark.asyncio
    async def test_clearing_custom_type_of_other_entity_is_rejected(self, http_client):
        entity = await _create_entity(
            http_client, name="mq", entity_type="Other", custom_type="Middleware",
        )

        response = await http_client.put(
            f"/api/v1/entities/{entity['id']}", json={"custom_type": ""},
        )

        assert response.status_code == 400
        assert "custom_type is required" in response.json()["error"]

        # Nothing was written: the entity is still readable, listable and deletable
        fetched = await http_client.get(f"/api/v1/entities/{entity['id']}")
        assert fetched.status_code == 200
        assert fetched.json()["custom_type"] == "Middleware"
        listed = await http_client.get("/api/v1/entities")
        assert listed.json()["entities"][0]["custom_type"] == "Middleware"
        deleted = await http_client.delete(f"/api/v1/entities/{entity['id']}")
        assert deleted.status_code == 200

    @pytest.mark.asyncio
    async def test_null_custom_type_on_other_entity_is_rejected(self, http_client):
        entity = await _create_entity(
            http_client, name="mq", entity_type="Other", custom_type="Middleware",
        )

        response = await http_client.put(
            f"/api/v1/entities/{entity['id']}", json={"custom_type": None},
        )

        assert response.status_code == 400
        fetched = await http_client.get(f"/api/v1/entities/{entity['id']}")
        assert fetched.status_code == 200
        assert fetched.json()["custom_type"] == "Middleware"

    @pytest.mark.asyncio
    async def test_moving_away_from_other_clears_custom_type_in_list_and_search(
        self, http_client,
    ):
        entity = await _create_entity(
            http_client, name="mq", entity_type="Other", custom_type="Middleware",
        )

        response = await http_client.put(
            f"/api/v1/entities/{entity['id']}", json={"entity_type": "Team"},
        )

        assert response.status_code == 200
        assert response.json()["custom_type"] is None
        fetched = await http_client.get(f"/api/v1/entities/{entity['id']}")
        listed = await http_client.get("/api/v1/entities")
        searched = await http_client.post("/api/v1/entities/search", json={"query": "mq"})
        assert fetched.json()["custom_type"] is None
        assert listed.json()["entities"][0]["entity_type"] == "Team"
        assert listed.json()["entities"][0]["custom_type"] is None
        assert searched.json()["entities"][0]["custom_type"] is None

    @pytest.mark.asyncio
    async def test_custom_type_is_not_stored_for_non_other_entity(self, http_client):
        entity = await _create_entity(http_client, name="person", entity_type="Individual")

        response = await http_client.put(
            f"/api/v1/entities/{entity['id']}",
            json={"entity_type": "Team", "custom_type": "zzz"},
        )

        assert response.status_code == 200
        listed = await http_client.get("/api/v1/entities")
        assert listed.json()["entities"][0]["entity_type"] == "Team"
        assert listed.json()["entities"][0]["custom_type"] is None

    @pytest.mark.asyncio
    async def test_other_entity_custom_type_can_still_be_changed(self, http_client):
        entity = await _create_entity(
            http_client, name="mq", entity_type="Other", custom_type="Middleware",
        )

        response = await http_client.put(
            f"/api/v1/entities/{entity['id']}", json={"custom_type": "Broker"},
        )

        assert response.status_code == 200
        assert response.json()["custom_type"] == "Broker"
        listed = await http_client.get("/api/v1/entities")
        assert listed.json()["entities"][0]["custom_type"] == "Broker"


# ----------------------------------------------------------------------------
# MCP tool surface: clean errors instead of corrupted rows / raw SQL text
# ----------------------------------------------------------------------------


async def _call_tool(mcp_client, tool_name: str, arguments: dict):
    return await mcp_client.call_tool(
        "execute_forgetful_tool", {"tool_name": tool_name, "arguments": arguments},
    )


@pytest.mark.asyncio
async def test_mcp_update_entity_rejects_clearing_custom_type(mcp_client):
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
