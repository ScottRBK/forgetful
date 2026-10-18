"""Live meta-tool and REST boundaries over the production runtime and SQLite."""

from contextlib import asynccontextmanager

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from httpx import ASGITransport, AsyncClient
from test_write_plugin_runtime import data
from test_write_plugin_runtime import plugin_runtime as plugin_runtime

from app.bootstrap import build_runtime, dispose_runtime
from app.routes.api import memories
from app.routes.mcp import meta_tools


@pytest.fixture
async def plugin_app(plugin_runtime):
    @asynccontextmanager
    async def lifespan(app):
        runtime = await build_runtime()
        app.memory_service = runtime.services.memory
        app.user_service = runtime.services.user
        app.registry = runtime.registry
        app._instance_permitted_tools = runtime.permitted_tools
        app._instance_scopes = runtime.instance_scopes
        try:
            yield
        finally:
            await dispose_runtime(runtime)

    app = FastMCP("Write Plugin test", lifespan=lifespan)
    meta_tools.register(app)
    memories.register(app)
    async with Client(app) as client:
        async with AsyncClient(
            transport=ASGITransport(app=app.http_app()), base_url="http://test",
        ) as http:
            yield app, client, http


async def execute(client, name, arguments):
    result = await client.call_tool(
        "execute_forgetful_tool", {"tool_name": name, "arguments": arguments},
    )
    return result.data


async def test_mcp_warn_update_shape_rejection_and_read_isolation(plugin_app):
    _, client, _ = plugin_app
    allowed = await execute(client, "create_memory", data().model_dump(exclude_unset=True))
    assert allowed["similar_memories"] == []
    assert allowed["obsolete_matches"] == []
    assert "plugin_warnings" not in allowed
    warned = await execute(client, "update_memory", {"memory_id": allowed["id"], "tags": ["warn"]})
    assert warned["id"] == allowed["id"]
    assert "memory" not in warned
    assert warned["plugin_warnings"][0]["message"] == "Check the source."
    with pytest.raises(ToolError, match="WRITE_PLUGIN_REJECTED: Remove the blocked tag"):
        await execute(client, "create_memory", data(["blocked"]).model_dump(exclude_unset=True))
    with pytest.raises(
        ToolError, match="WRITE_PLUGIN_UNAVAILABLE: Memory Write Plugin unavailable",
    ):
        await execute(client, "update_memory", {"memory_id": allowed["id"], "tags": ["error"]})
    read = await execute(client, "get_memory", {"memory_id": allowed["id"]})
    assert read["tags"] == ["warn"]
    assert "plugin_warnings" not in read
    listing = await execute(client, "get_recent_memories", {})
    assert listing["total_count"] == 1
    assert "plugin_warnings" not in listing["memories"][0]


async def test_rest_warnings_errors_and_flat_update(plugin_app):
    _, _, http = plugin_app
    created = await http.post(
        "/api/v1/memories", json=data(["warn"]).model_dump(exclude_unset=True),
    )
    assert created.status_code == 201
    payload = created.json()
    assert payload["plugin_warnings"][0]["message"] == "Check the source."
    assert payload["obsolete_matches"] == []
    memory_id = payload["id"]
    updated = await http.put(f"/api/v1/memories/{memory_id}", json={"tags": []})
    assert updated.status_code == 200
    assert updated.json()["id"] == memory_id
    assert updated.json()["tags"] == []
    assert "plugin_warnings" not in updated.json()
    rejected = await http.put(f"/api/v1/memories/{memory_id}", json={"tags": ["blocked"]})
    assert rejected.status_code == 400
    assert rejected.json()["error"] == "Remove the blocked tag."
    unavailable = await http.post(
        "/api/v1/memories", json=data(["error"]).model_dump(exclude_unset=True),
    )
    assert unavailable.status_code == 503
    assert unavailable.json()["error"] == "Memory Write Plugin unavailable."
    read = await http.get(f"/api/v1/memories/{memory_id}")
    assert "plugin_warnings" not in read.json()
    listing = await http.get("/api/v1/memories")
    assert listing.json()["total"] == 1


async def test_scopes_and_rest_auth_stop_before_plugin(plugin_app, plugin_runtime, monkeypatch):
    import importlib

    from app.routes.mcp.scope_resolver import parse_scopes, resolve_permitted_tools

    app, client, http = plugin_app
    scope = parse_scopes("read")
    monkeypatch.setattr(app, "_instance_scopes", scope)
    monkeypatch.setattr(
        app, "_instance_permitted_tools", resolve_permitted_tools(scope, app.registry),
    )
    with pytest.raises(ToolError, match="not permitted under current scopes"):
        await execute(client, "create_memory", data().model_dump(exclude_unset=True))
    # REST has its own auth path; it does not inherit the MCP scope ceiling.
    monkeypatch.setattr(app, "auth", object())
    response = await http.post("/api/v1/memories", json=data().model_dump(exclude_unset=True))
    assert response.status_code == 401
    assert response.json()["error"] == "Missing or invalid Authorization header"
    assert importlib.import_module(plugin_runtime).calls == []


async def test_plugin_warning_coexists_with_obsolete_match_and_query_stays_clean(
    plugin_app, monkeypatch,
):
    from app.config.settings import settings

    monkeypatch.setattr(settings, "OBSOLETE_WARNING_ENABLED", True)
    _, client, _ = plugin_app
    old = await execute(client, "create_memory", data().model_dump(exclude_unset=True))
    await execute(client, "mark_memory_obsolete", {"memory_id": old["id"], "reason": "Outdated"})
    new = await execute(client, "create_memory", data(["warn"]).model_dump(exclude_unset=True))
    assert new["obsolete_matches"][0]["id"] == old["id"]
    assert new["plugin_warnings"][0]["message"] == "Check the source."
    query = await execute(client, "query_memory", {"query": "A fact", "query_context": "Testing"})
    assert [memory["id"] for memory in query["primary_memories"]] == [new["id"]]
    assert "plugin_warnings" not in query["primary_memories"][0]
