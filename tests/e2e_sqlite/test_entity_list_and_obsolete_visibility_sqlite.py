"""E2E tests for entity listing and obsolete-memory visibility with in-memory SQLite.

Covers:
- list_entities pagination over DISTINCT entities when filtering by project_ids
- project_ids=[] behaving as "no project filter" (as memory listing does)
"""
import pytest

from app.config.settings import settings
from app.models.user_models import UserCreate


async def _default_user_id(sqlite_app):
    """Resolve the default (no-auth) user the HTTP/MCP front doors act as."""
    user = await sqlite_app.user_service.get_or_create_user(
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


# ============================================================================
# list_entities: project filter pagination and empty filter
# ============================================================================

@pytest.mark.asyncio
async def test_list_entities_project_filter_paginates_distinct_entities(sqlite_app, http_client):
    """Entities linked to several requested projects occupy one slot, not one per project."""
    p1 = await _create_project(http_client, "page-p1")
    p2 = await _create_project(http_client, "page-p2")
    p3 = await _create_project(http_client, "page-p3")

    # Created oldest -> newest; listing is newest first.
    a = await _create_entity(http_client, "A both", [p1, p2])
    b = await _create_entity(http_client, "B both", [p1, p2])
    c = await _create_entity(http_client, "C all three", [p1, p2, p3])
    await _create_entity(http_client, "D other project", [p3])
    e = await _create_entity(http_client, "E one", [p2])

    user_id = await _default_user_id(sqlite_app)
    service = sqlite_app.entity_service

    pages = []
    offset = 0
    total = None
    while total is None or offset < total:
        entities, total = await service.list_entities(
            user_id, project_ids=[p1, p2], limit=2, offset=offset,
        )
        pages.append([entity.id for entity in entities])
        offset += 2

    assert total == 4
    assert pages == [[e, c], [b, a]]


@pytest.mark.asyncio
async def test_list_entities_project_filter_single_page_returns_each_entity_once(
    sqlite_app, http_client,
):
    """A page large enough for every entity returns each exactly once, sized to total."""
    p1 = await _create_project(http_client, "once-p1")
    p2 = await _create_project(http_client, "once-p2")
    ids = [await _create_entity(http_client, f"Both {i}", [p1, p2]) for i in range(3)]

    user_id = await _default_user_id(sqlite_app)
    entities, total = await sqlite_app.entity_service.list_entities(
        user_id, project_ids=[p1, p2], limit=3, offset=0,
    )

    assert total == 3
    assert sorted(entity.id for entity in entities) == sorted(ids)


@pytest.mark.asyncio
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
    assert len(with_empty.data["entities"]) == 2
    # A real filter still narrows the result
    assert filtered.data["total_count"] == 1
