"""Live meta-tool and REST boundaries over the production runtime and SQLite."""

from contextlib import asynccontextmanager

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from httpx import ASGITransport, AsyncClient
from test_write_plugin_runtime import data
from test_write_plugin_runtime import plugin_runtime as plugin_runtime

from app.bootstrap import build_runtime, dispose_runtime
from app.config.settings import settings
from app.routes.api import memories
from app.routes.mcp import meta_tools


@pytest.fixture
async def plugin_app(plugin_runtime, request, monkeypatch):
    if getattr(request, "param", True) is False:
        monkeypatch.setattr(settings, "MEMORY_WRITE_PLUGIN", "")

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
            transport=ASGITransport(app=app.http_app(), raise_app_exceptions=False),
            base_url="http://test",
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
    for tool, args in [
        ("mark_memory_obsolete", {"memory_id": 1, "reason": "Old fact"}),
        ("unobsolete_memory", {"memory_id": 1}),
    ]:
        with pytest.raises(ToolError, match="not permitted under current scopes"):
            await execute(client, tool, args)
    # REST has its own auth path; it does not inherit the MCP scope ceiling.
    monkeypatch.setattr(app, "auth", object())
    response = await http.post("/api/v1/memories", json=data().model_dump(exclude_unset=True))
    assert response.status_code == 401
    assert response.json()["error"] == "Missing or invalid Authorization header"
    response = await http.delete("/api/v1/memories/1")
    assert response.status_code == 401
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


@pytest.mark.parametrize("operation,tool", [
    ("obsolete", "mark_memory_obsolete"), ("restore", "unobsolete_memory"),
])
async def test_mcp_lifecycle_success_warning_and_error_shapes(plugin_app, operation, tool):
    _, client, _ = plugin_app

    async def prepare(tags):
        result = await execute(client, "create_memory", data(tags).model_dump(exclude_unset=True))
        if operation == "restore":
            await execute(client, "mark_memory_obsolete", {
                "memory_id": result["id"], "reason": "Old fact",
            })
        args = {"memory_id": result["id"]}
        if operation == "obsolete":
            args["reason"] = "Old fact"
        return args

    plain = await execute(client, tool, await prepare([]))
    assert plain == {"success": True}
    warned = await execute(client, tool, await prepare([f"{operation}_warn", "post_warn"]))
    assert warned == {"success": True, "plugin_warnings": [
        {"outcome": "warn", "message": "Check the lifecycle change.", "code": None},
        {"outcome": "warn", "message": "Review saved memory.", "code": "review"},
    ]}
    for marker, error in [("blocked", "WRITE_PLUGIN_REJECTED: Keep this state"),
                          ("error", "WRITE_PLUGIN_UNAVAILABLE: Memory Write Plugin unavailable")]:
        args = await prepare([f"{operation}_{marker}"])
        with pytest.raises(ToolError, match=error):
            await execute(client, tool, args)
        saved = await execute(client, "get_memory", {"memory_id": args["memory_id"]})
        assert saved["is_obsolete"] is (operation == "restore")


async def test_rest_delete_warning_rejection_and_unavailability(plugin_app):
    _, _, http = plugin_app
    for tags, status, error in [
        ([], 200, None),
        (["obsolete_warn", "post_warn"], 200, None),
        (["obsolete_blocked"], 400, "Keep this state."),
        (["obsolete_error"], 503, "Memory Write Plugin unavailable."),
    ]:
        created = await http.post(
            "/api/v1/memories", json=data(tags).model_dump(exclude_unset=True),
        )
        memory_id = created.json()["id"]

        response = await http.request(
            "DELETE", f"/api/v1/memories/{memory_id}", json={"reason": "Old fact"},
        )

        assert response.status_code == status
        if error:
            assert response.json() == {"error": error}
        elif tags:
            assert response.json()["success"] is True
            assert len(response.json()["plugin_warnings"]) == 2
        else:
            assert response.json() == {"success": True}
        saved = (await http.get(f"/api/v1/memories/{memory_id}")).json()
        assert saved["is_obsolete"] is (status == 200)


@pytest.mark.parametrize("plugin_app", [True, False], indirect=True)
async def test_rest_delete_rejects_invalid_body_without_mutation(plugin_app):
    _, _, http = plugin_app
    created = await http.post("/api/v1/memories", json=data().model_dump(exclude_unset=True))
    path = f"/api/v1/memories/{created.json()['id']}"

    for body in (
        '{"reason": 123}', '{"superseded_by": "SECRET"}',
        '{"superseded_by": true}', '{"superseded_by": 1.5}',
        "[]", '{"reason":',
    ):
        response = await http.request(
            "DELETE", path, content=body, headers={"content-type": "application/json"},
        )

        assert response.status_code == 400
        assert response.json()["error"].startswith("Invalid obsolete request")
        assert "SECRET" not in response.text
        saved = (await http.get(path)).json()
        assert saved["is_obsolete"] is False
        assert saved["obsolete_reason"] is None
        assert saved["superseded_by"] is None


@pytest.mark.parametrize("plugin_app", [True, False], indirect=True)
async def test_rest_delete_preserves_defaults_and_valid_replacement(plugin_app):
    _, _, http = plugin_app
    replacement = await http.post("/api/v1/memories", json=data().model_dump(exclude_unset=True))
    replacement_id = replacement.json()["id"]
    for body in (None, {}, {"reason": "Use revised fact", "superseded_by": replacement_id}):
        created = await http.post("/api/v1/memories", json=data().model_dump(exclude_unset=True))
        path = f"/api/v1/memories/{created.json()['id']}"

        response = await http.request("DELETE", path, **({} if body is None else {"json": body}))

        assert response.status_code == 200
        assert response.json() == {"success": True}
        saved = (await http.get(path)).json()
        assert saved["is_obsolete"] is True
        assert saved["obsolete_reason"] == (
            "Use revised fact" if body else "Marked obsolete via API"
        )
        assert saved["superseded_by"] == (replacement_id if body else None)


@pytest.mark.parametrize("tag", ["post_warn", "post_error"])
async def test_live_after_save_warnings_preserve_create_and_update_success(plugin_app, tag):
    _, client, http = plugin_app
    for transport in ("mcp", "rest"):
        if transport == "mcp":
            created = await execute(
                client, "create_memory", data([tag]).model_dump(exclude_unset=True),
            )
            updated = await execute(client, "update_memory", {
                "memory_id": created["id"], "importance": 8,
            })
        else:
            response = await http.post(
                "/api/v1/memories", json=data([tag]).model_dump(exclude_unset=True),
            )
            assert response.status_code == 201
            created = response.json()
            response = await http.put(
                f"/api/v1/memories/{created['id']}", json={"importance": 8},
            )
            assert response.status_code == 200
            updated = response.json()

        for payload in (created, updated):
            assert "memory" not in payload
            assert payload["id"] == created["id"]
            assert payload["plugin_warnings"][0]["code"] == (
                "review" if tag == "post_warn" else "MEMORY_PLUGIN_AFTER_SAVE_UNAVAILABLE"
            )
            assert "SECRET" not in str(payload)
        saved = await execute(client, "get_memory", {"memory_id": created["id"]})
        assert saved["importance"] == 8
        assert "plugin_warnings" not in saved
