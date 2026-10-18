"""E2E tests for entity write-path integrity with in-memory SQLite.

Covers the full stack (REST routes -> EntityService -> SqliteEntityRepository):
- updates validate the merged entity_type/custom_type state before writing
- project_ids that do not exist (or belong to another user) are rejected
  instead of being dropped, and never wipe existing project links
"""
import pytest
from fastmcp.exceptions import ToolError

from app.config.settings import settings
from app.events import EventBus
from app.exceptions import NotFoundError
from app.models.activity_models import ActionType
from app.models.entity_models import (
    EntityUpdate,
)
from app.models.user_models import UserCreate
from app.services.entity_service import EntityService


class _CollectingEventBus(EventBus):
    def __init__(self):
        super().__init__()
        self.collected_events = []

    async def emit(self, event):
        self.collected_events.append(event)
        await super().emit(event)


async def _default_user(app):
    return await app.user_service.get_or_create_user(
        UserCreate(
            external_id=settings.DEFAULT_USER_ID,
            name=settings.DEFAULT_USER_NAME,
            email=settings.DEFAULT_USER_EMAIL,
        ),
    )


async def _create_entity(http_client, **payload) -> dict:
    payload.setdefault("entity_type", "Organization")
    response = await http_client.post("/api/v1/entities", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


async def _create_project(http_client, name: str) -> int:
    response = await http_client.post("/api/v1/projects", json={
        "name": name,
        "description": f"Project {name}",
        "project_type": "development",
    })
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _create_foreign_project(http_client, monkeypatch) -> int:
    """Create a project owned by a different user than the default one."""
    with monkeypatch.context() as other_user:
        other_user.setattr(settings, "DEFAULT_USER_ID", "entity-integrity-other-user")
        other_user.setattr(settings, "DEFAULT_USER_EMAIL", "entity-integrity-other@example.test")
        return await _create_project(http_client, "Foreign project")


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
# project_ids validation on create and update
# ----------------------------------------------------------------------------


class TestProjectIdValidation:
    @pytest.mark.asyncio
    async def test_create_with_unknown_project_id_returns_404(self, http_client):
        response = await http_client.post("/api/v1/entities", json={
            "name": "orphan", "entity_type": "Team", "project_ids": [999],
        })

        assert response.status_code == 404
        assert "Projects not found" in response.json()["error"]
        listed = await http_client.get("/api/v1/entities")
        assert listed.json()["entities"] == []

    @pytest.mark.asyncio
    async def test_create_with_another_users_project_returns_404(
        self, http_client, monkeypatch,
    ):
        foreign_id = await _create_foreign_project(http_client, monkeypatch)

        response = await http_client.post("/api/v1/entities", json={
            "name": "sneaky", "entity_type": "Team", "project_ids": [foreign_id],
        })

        assert response.status_code == 404
        assert "Projects not found" in response.json()["error"]

    @pytest.mark.asyncio
    async def test_create_with_one_missing_project_id_creates_nothing(self, http_client):
        project_id = await _create_project(http_client, "real")

        response = await http_client.post("/api/v1/entities", json={
            "name": "partial", "entity_type": "Team", "project_ids": [project_id, 999],
        })

        assert response.status_code == 404
        listed = await http_client.get("/api/v1/entities")
        assert listed.json()["entities"] == []

    @pytest.mark.asyncio
    async def test_update_with_unknown_project_id_keeps_existing_links(self, http_client):
        project_id = await _create_project(http_client, "real")
        entity = await _create_entity(
            http_client, name="e", entity_type="Team", project_ids=[project_id],
        )

        response = await http_client.put(
            f"/api/v1/entities/{entity['id']}", json={"project_ids": [999]},
        )

        assert response.status_code == 404
        assert "Projects not found" in response.json()["error"]
        fetched = await http_client.get(f"/api/v1/entities/{entity['id']}")
        assert fetched.json()["project_ids"] == [project_id]

    @pytest.mark.asyncio
    async def test_update_with_another_users_project_keeps_existing_links(
        self, http_client, monkeypatch,
    ):
        project_id = await _create_project(http_client, "real")
        foreign_id = await _create_foreign_project(http_client, monkeypatch)
        entity = await _create_entity(
            http_client, name="e", entity_type="Team", project_ids=[project_id],
        )

        response = await http_client.put(
            f"/api/v1/entities/{entity['id']}",
            json={"name": "renamed", "project_ids": [project_id, foreign_id]},
        )

        assert response.status_code == 404
        fetched = await http_client.get(f"/api/v1/entities/{entity['id']}")
        # The rejected update is atomic: neither the rename nor the links changed
        assert fetched.json()["name"] == "e"
        assert fetched.json()["project_ids"] == [project_id]

    @pytest.mark.asyncio
    async def test_update_replaces_and_clears_valid_project_links(self, http_client):
        first = await _create_project(http_client, "first")
        second = await _create_project(http_client, "second")
        entity = await _create_entity(
            http_client, name="e", entity_type="Team", project_ids=[first],
        )

        replaced = await http_client.put(
            f"/api/v1/entities/{entity['id']}", json={"project_ids": [second]},
        )
        assert replaced.status_code == 200
        assert replaced.json()["project_ids"] == [second]

        cleared = await http_client.put(
            f"/api/v1/entities/{entity['id']}", json={"project_ids": []},
        )
        assert cleared.status_code == 200
        assert cleared.json()["project_ids"] == []

    @pytest.mark.asyncio
    async def test_rejected_project_update_emits_no_event(self, http_client, sqlite_app):
        user = await _default_user(sqlite_app)
        project_id = await _create_project(http_client, "real")
        entity = await _create_entity(
            http_client, name="e", entity_type="Team", project_ids=[project_id],
        )
        bus = _CollectingEventBus()
        service = EntityService(sqlite_app.entity_service.entity_repo, event_bus=bus)

        with pytest.raises(NotFoundError, match="Projects not found"):
            await service.update_entity(user.id, entity["id"], EntityUpdate(project_ids=[999]))

        assert [e for e in bus.collected_events if e.action == ActionType.UPDATED] == []


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


@pytest.mark.asyncio
async def test_mcp_update_entity_with_unknown_project_keeps_links(mcp_client):
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
            "entity_id": entity_id, "project_ids": [999],
        })

    fetched = await _call_tool(mcp_client, "get_entity", {"entity_id": entity_id})
    assert fetched.data["project_ids"] == [project_id]
