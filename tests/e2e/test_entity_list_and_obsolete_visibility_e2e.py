"""PostgreSQL E2E coverage for entity listing and obsolete-memory visibility.

Mirrors tests/e2e_sqlite/test_entity_list_and_obsolete_visibility_sqlite.py against
the PostgreSQL repositories, which carry their own copy of the affected queries.
"""
import pytest

from app.config.settings import settings
from app.models.user_models import UserCreate

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _default_user_id(postgres_app):
    """Resolve the default (no-auth) user the HTTP/MCP front doors act as."""
    user = await postgres_app.user_service.get_or_create_user(
        UserCreate(
            external_id=settings.DEFAULT_USER_ID,
            name=settings.DEFAULT_USER_NAME,
            email=settings.DEFAULT_USER_EMAIL,
        ),
    )
    return user.id


async def _create_project(http_client, name: str) -> int:
    response = await http_client.post("/api/v1/projects", json={
        "name": name,
        "description": f"{name} description",
        "project_type": "development",
    })
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _create_entity(http_client, name: str, project_ids: list[int]) -> int:
    response = await http_client.post("/api/v1/entities", json={
        "name": name,
        "entity_type": "Organization",
        "project_ids": project_ids,
    })
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _create_memory(http_client, title: str, project_ids: list[int] | None = None) -> int:
    payload = {
        "title": title,
        "content": f"content of {title}",
        "context": "obsolete visibility test",
        "keywords": ["visibility"],
        "tags": ["visibility"],
        "importance": 7,
    }
    if project_ids:
        payload["project_ids"] = project_ids
    response = await http_client.post("/api/v1/memories", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _call(mcp_client, tool_name: str, arguments: dict):
    return await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": tool_name, "arguments": arguments,
    })


@pytest.mark.e2e
async def test_list_entities_project_filter_paginates_distinct_entities(postgres_app, http_client):
    """Entities linked to several requested projects occupy one slot, not one per project."""
    p1 = await _create_project(http_client, "page-p1")
    p2 = await _create_project(http_client, "page-p2")
    p3 = await _create_project(http_client, "page-p3")

    a = await _create_entity(http_client, "A both", [p1, p2])
    b = await _create_entity(http_client, "B both", [p1, p2])
    c = await _create_entity(http_client, "C all three", [p1, p2, p3])
    await _create_entity(http_client, "D other project", [p3])
    e = await _create_entity(http_client, "E one", [p2])

    user_id = await _default_user_id(postgres_app)

    pages = []
    offset = 0
    total = None
    while total is None or offset < total:
        entities, total = await postgres_app.entity_service.list_entities(
            user_id, project_ids=[p1, p2], limit=2, offset=offset,
        )
        pages.append([entity.id for entity in entities])
        offset += 2

    assert total == 4
    assert pages == [[e, c], [b, a]]


@pytest.mark.e2e
async def test_list_entities_empty_project_ids_is_no_filter(http_client, mcp_client):
    """project_ids=[] is treated like an omitted filter, as it is for memories."""
    project_id = await _create_project(http_client, "empty-filter-project")
    await _create_entity(http_client, "Linked entity", [project_id])
    await _create_entity(http_client, "Unlinked entity", [])

    unfiltered = await _call(mcp_client, "list_entities", {})
    with_empty = await _call(mcp_client, "list_entities", {"project_ids": []})
    filtered = await _call(mcp_client, "list_entities", {"project_ids": [project_id]})

    assert unfiltered.data["total_count"] == 2
    assert with_empty.data["total_count"] == 2
    assert filtered.data["total_count"] == 1
