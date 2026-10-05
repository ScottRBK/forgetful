"""E2E tests for the get_memory_entities MCP tool (issue #78)"""
import pytest

from app.routes.mcp.scope_resolver import parse_scopes, resolve_permitted_tools

MISSING_MEMORY_ID = 999999


async def _call(mcp_client, tool_name, arguments):
    return await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": tool_name, "arguments": arguments})


async def _create_memory(mcp_client, title):
    result = await _call(mcp_client, "create_memory", {
        "title": title,
        "content": f"Memory body for {title}",
        "context": "Testing get_memory_entities",
        "keywords": ["entity", "reverse"],
        "tags": ["test"],
        "importance": 6,
    })
    return result.data["id"]


async def _create_entity(mcp_client, name, entity_type="Organization"):
    result = await _call(mcp_client, "create_entity", {
        "name": name, "entity_type": entity_type, "tags": ["reverse-lookup"]})
    return result.data["id"]


async def _link(mcp_client, entity_id, memory_id):
    await _call(mcp_client, "link_entity_to_memory", {
        "entity_id": entity_id, "memory_id": memory_id})


async def _get_memory_entities(mcp_client, memory_id):
    result = await _call(mcp_client, "get_memory_entities", {"memory_id": memory_id})
    return result.data


@pytest.mark.asyncio
async def test_get_memory_entities_returns_all_direct_links_e2e(mcp_client):
    memory_id = await _create_memory(mcp_client, "Memory with three entities")
    expected = {}
    for name, entity_type in [("Acme", "Organization"), ("Sarah", "Individual"), ("Ops", "Team")]:
        entity_id = await _create_entity(mcp_client, name, entity_type)
        await _link(mcp_client, entity_id, memory_id)
        expected[entity_id] = (name, entity_type)

    data = await _get_memory_entities(mcp_client, memory_id)

    assert data["count"] == 3
    assert data["entity_ids"] == sorted(expected)
    assert [entity["id"] for entity in data["entities"]] == data["entity_ids"]
    assert {entity["id"]: (entity["name"], entity["entity_type"]) for entity in data["entities"]} == expected


@pytest.mark.asyncio
async def test_get_memory_entities_empty_e2e(mcp_client):
    memory_id = await _create_memory(mcp_client, "Memory without entities")

    data = await _get_memory_entities(mcp_client, memory_id)

    assert data == {"entity_ids": [], "count": 0, "entities": []}


@pytest.mark.asyncio
async def test_get_memory_entities_excludes_other_memories_e2e(mcp_client):
    target_id = await _create_memory(mcp_client, "Target memory")
    other_id = await _create_memory(mcp_client, "Other memory")
    mine = await _create_entity(mcp_client, "Linked to target")
    theirs = await _create_entity(mcp_client, "Linked to other")
    await _link(mcp_client, mine, target_id)
    await _link(mcp_client, theirs, other_id)

    data = await _get_memory_entities(mcp_client, target_id)

    assert data["entity_ids"] == [mine]


@pytest.mark.asyncio
async def test_get_memory_entities_missing_memory_e2e(mcp_client):
    with pytest.raises(Exception) as exc_info:
        await _get_memory_entities(mcp_client, MISSING_MEMORY_ID)

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_memory_entities_reflects_link_and_unlink_e2e(mcp_client):
    memory_id = await _create_memory(mcp_client, "Memory for link changes")
    entity_id = await _create_entity(mcp_client, "Comes and goes")

    await _link(mcp_client, entity_id, memory_id)
    assert (await _get_memory_entities(mcp_client, memory_id))["entity_ids"] == [entity_id]

    await _call(mcp_client, "unlink_entity_from_memory", {
        "entity_id": entity_id, "memory_id": memory_id})
    assert (await _get_memory_entities(mcp_client, memory_id))["entity_ids"] == []


@pytest.mark.asyncio
async def test_get_memory_entities_large_set_is_complete_e2e(mcp_client):
    memory_id = await _create_memory(mcp_client, "Memory with many entities")
    entity_ids = []
    for index in range(25):
        entity_id = await _create_entity(mcp_client, f"Bulk entity {index}")
        await _link(mcp_client, entity_id, memory_id)
        entity_ids.append(entity_id)

    data = await _get_memory_entities(mcp_client, memory_id)

    assert data["count"] == 25
    assert data["entity_ids"] == sorted(entity_ids)


@pytest.mark.asyncio
async def test_get_memory_entities_available_with_read_scope_e2e(mcp_client, sqlite_app):
    memory_id = await _create_memory(mcp_client, "Memory for read scope")
    entity_id = await _create_entity(mcp_client, "Readable entity")
    await _link(mcp_client, entity_id, memory_id)

    instance_scopes = parse_scopes("read")
    sqlite_app._instance_permitted_tools = resolve_permitted_tools(instance_scopes, sqlite_app.registry)
    sqlite_app._instance_scopes = instance_scopes

    discovered = await mcp_client.call_tool("discover_forgetful_tools", {})
    tools = [tool for cat_tools in discovered.data["tools_by_category"].values() for tool in cat_tools]
    matches = [tool for tool in tools if tool["name"] == "get_memory_entities"]
    assert len(matches) == 1
    assert matches[0]["mutates"] is False

    data = await _get_memory_entities(mcp_client, memory_id)
    assert data["entity_ids"] == [entity_id]
