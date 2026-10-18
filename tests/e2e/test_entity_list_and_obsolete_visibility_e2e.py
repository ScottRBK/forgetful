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


@pytest.mark.e2e
async def test_entity_memories_exclude_obsolete_memory(http_client):
    """GET /entities/{id}/memories no longer lists a soft-deleted memory."""
    entity_id = await _create_entity(http_client, "Obsolete entity", [])
    kept = await _create_memory(http_client, "Kept memory")
    doomed = await _create_memory(http_client, "Doomed memory")
    for memory_id in (kept, doomed):
        link = await http_client.post(
            f"/api/v1/entities/{entity_id}/memories", json={"memory_id": memory_id},
        )
        assert link.status_code == 200, link.text

    deleted = await http_client.request(
        "DELETE", f"/api/v1/memories/{doomed}", json={"reason": "no longer true"},
    )
    assert deleted.status_code == 200, deleted.text

    after = (await http_client.get(f"/api/v1/entities/{entity_id}/memories")).json()
    assert after["memory_ids"] == [kept]
    assert after["count"] == 1
    assert [m["id"] for m in after["memories"]] == [kept]


@pytest.mark.e2e
async def test_skill_links_exclude_obsolete_memory(mcp_client):
    """The get_skill_links reverse lookup no longer reports a memory marked obsolete."""
    skill = await _call(mcp_client, "create_skill", {
        "name": "obsolete-links-skill",
        "description": "Skill used to check obsolete memory visibility",
        "content": "# Content",
        "tags": [],
        "importance": 7,
    })
    skill_id = skill.data["id"]

    memory_ids = []
    for title in ("Kept skill memory", "Doomed skill memory"):
        memory = await _call(mcp_client, "create_memory", {
            "title": title,
            "content": f"content of {title}",
            "context": "obsolete visibility test",
            "keywords": ["visibility"],
            "tags": ["visibility"],
            "importance": 7,
        })
        memory_ids.append(memory.data["id"])
        await _call(mcp_client, "link_skill_to_memory", {
            "skill_id": skill_id, "memory_id": memory.data["id"],
        })
    kept, doomed = memory_ids

    await _call(mcp_client, "mark_memory_obsolete", {
        "memory_id": doomed, "reason": "superseded",
    })

    links = await _call(mcp_client, "get_skill_links", {"skill_id": skill_id})
    assert links.data["memory_ids"] == [kept]
    assert links.data["total_count"] == 1


@pytest.mark.e2e
async def test_project_memory_count_excludes_obsolete_memories(http_client):
    """memory_count on project list and detail counts only non-obsolete memories."""
    project_id = await _create_project(http_client, "count-project")
    await _create_memory(http_client, "Counted memory", [project_id])
    doomed = await _create_memory(http_client, "Doomed counted memory", [project_id])

    detail = (await http_client.get(f"/api/v1/projects/{project_id}")).json()
    assert detail["memory_count"] == 2

    deleted = await http_client.request(
        "DELETE", f"/api/v1/memories/{doomed}", json={"reason": "obsolete"},
    )
    assert deleted.status_code == 200, deleted.text

    detail = (await http_client.get(f"/api/v1/projects/{project_id}")).json()
    listing = (await http_client.get("/api/v1/projects")).json()["projects"]
    summary = next(p for p in listing if p["id"] == project_id)
    assert (detail["memory_count"], summary["memory_count"]) == (1, 1)
