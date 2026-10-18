"""E2E tests for entity search and project name matching with real PostgreSQL.

Covers literal LIKE wildcards, per-alias matching and the project ids reported in
``search_entities`` results, so the PostgreSQL queries behave like the SQLite ones.
"""
import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _call(mcp_client, tool_name, arguments):
    result = await mcp_client.call_tool(
        "execute_forgetful_tool", {"tool_name": tool_name, "arguments": arguments},
    )
    return result.data


async def _create_entity(mcp_client, name, **extra):
    return await _call(
        mcp_client,
        "create_entity",
        {"name": name, "entity_type": "System", "notes": "matching test", **extra},
    )


async def _create_project(mcp_client, name):
    created = await _call(
        mcp_client,
        "create_project",
        {"name": name, "description": "matching test", "project_type": "development"},
    )
    return created["id"]


async def _search(mcp_client, query):
    data = await _call(mcp_client, "search_entities", {"query": query})
    return sorted(e["name"] for e in data["entities"])


async def _project_names(mcp_client, name):
    data = await _call(mcp_client, "list_projects", {"name": name})
    return sorted(p["name"] for p in data["projects"])


@pytest.mark.e2e
async def test_search_entities_reports_project_ids_e2e(mcp_client):
    """Search results carry the entity's real project ids, like list_entities."""
    first = await _create_project(mcp_client, "membership-first")
    second = await _create_project(mcp_client, "membership-second")
    await _create_entity(mcp_client, "Alice", project_ids=[first, second])
    await _create_entity(mcp_client, "Alicia")

    data = await _call(mcp_client, "search_entities", {"query": "Ali"})

    searched = {e["name"]: sorted(e["project_ids"]) for e in data["entities"]}
    assert searched == {"Alice": sorted([first, second]), "Alicia": []}


@pytest.mark.e2e
async def test_search_entities_underscore_is_literal_e2e(mcp_client):
    for name in ("auth_service", "auth-service", "authXservice"):
        await _create_entity(mcp_client, name)

    assert await _search(mcp_client, "auth_service") == ["auth_service"]


@pytest.mark.e2e
async def test_search_entities_percent_is_literal_e2e(mcp_client):
    for name in ("alpha", "beta", "100% done"):
        await _create_entity(mcp_client, name)

    assert await _search(mcp_client, "%") == ["100% done"]


@pytest.mark.e2e
async def test_search_entities_backslash_is_literal_e2e(mcp_client):
    for name in ("back\\slash", "backslash", "back/slash"):
        await _create_entity(mcp_client, name)

    assert await _search(mcp_client, "back\\slash") == ["back\\slash"]


@pytest.mark.e2e
async def test_search_entities_wildcards_are_literal_in_aliases_e2e(mcp_client):
    await _create_entity(mcp_client, "Underscore", aka=["svc_main"])
    await _create_entity(mcp_client, "Dash", aka=["svc-main"])
    await _create_entity(mcp_client, "Percent", aka=["50% off"])

    assert await _search(mcp_client, "svc_main") == ["Underscore"]
    assert await _search(mcp_client, "%") == ["Percent"]


@pytest.mark.e2e
@pytest.mark.parametrize("query", ["Big Corp", "BigCorp", "Big,Corp"])
async def test_search_entities_match_cannot_span_two_aliases_e2e(mcp_client, query):
    """Adjacent aliases are not joined into one searchable string."""
    await _create_entity(mcp_client, "e", aka=["Big", "Corp"])

    assert await _search(mcp_client, query) == []


@pytest.mark.e2e
async def test_search_entities_each_alias_matches_individually_e2e(mcp_client):
    await _create_entity(mcp_client, "e", aka=["Big", "Corp"])
    await _create_entity(mcp_client, "empty", aka=[])

    assert await _search(mcp_client, "Big") == ["e"]
    assert await _search(mcp_client, "corp") == ["e"]
    assert await _search(mcp_client, "[") == []


@pytest.mark.e2e
async def test_list_projects_name_wildcards_are_literal_e2e(mcp_client):
    for name in ("my_proj", "myXproj", "100% project", "back\\slash", "backslash"):
        await _create_project(mcp_client, name)

    assert await _project_names(mcp_client, "my_proj") == ["my_proj"]
    assert await _project_names(mcp_client, "%") == ["100% project"]
    assert await _project_names(mcp_client, "back\\slash") == ["back\\slash"]
    assert await _project_names(mcp_client, "MY_PROJ") == ["my_proj"]
