"""Public REST and MCP memory updates over the production SQLite runtime."""

from contextlib import asynccontextmanager

import pytest
from fastmcp import Client, FastMCP
from httpx import ASGITransport, AsyncClient
from test_memory_write_plugin import RecordingEmbeddings, candidate

from app.bootstrap import build_runtime, dispose_runtime
from app.models.write_plugin_models import WriteDecision
from app.protocols.write_plugin_protocol import MemoryPlugin
from app.routes.api import memories
from app.routes.mcp import meta_tools
from app.services.write_plugin_service import WritePluginService


def checks(handler):
    return MemoryPlugin(before_save={"create": handler, "update": handler})


@pytest.fixture(params=[False, True], ids=["plugin-disabled", "plugin-enabled"])
async def memory_app(sqlite_runtime_settings, monkeypatch, request):
    monkeypatch.setattr("app.bootstrap.get_embedding_adapter", RecordingEmbeddings)
    monkeypatch.setattr("app.bootstrap.check_first_run_models", lambda: None)

    async def allow(_request):
        return WriteDecision(outcome="allow")

    @asynccontextmanager
    async def lifespan(app):
        runtime = await build_runtime()
        app.memory_service = runtime.services.memory
        app.user_service = runtime.services.user
        app.registry = runtime.registry
        app._instance_permitted_tools = runtime.permitted_tools
        app._instance_scopes = runtime.instance_scopes
        if request.param:
            runtime.services.memory._write_plugin = WritePluginService(checks(allow))
        try:
            yield
        finally:
            await dispose_runtime(runtime)

    app = FastMCP("Memory null update test", lifespan=lifespan)
    meta_tools.register(app)
    memories.register(app)
    async with Client(app) as client:
        async with AsyncClient(transport=ASGITransport(app=app.http_app()), base_url="http://test") as http:
            yield client, http


async def execute(client, name, arguments):
    result = await client.call_tool("execute_forgetful_tool", {"tool_name": name, "arguments": arguments})
    return result.data


async def test_rest_null_only_is_successful_noop(memory_app):
    _, http = memory_app
    created = await http.post("/api/v1/memories", json=candidate().model_dump(exclude_unset=True))
    assert created.status_code == 201
    before = (await http.get(f"/api/v1/memories/{created.json()['id']}")).json()
    response = await http.put(f"/api/v1/memories/{before['id']}", json={"title": None})
    assert response.status_code == 200
    updated = response.json()
    assert updated["title"] == before["title"]
    assert updated["updated_at"] == before["updated_at"]
    read = await http.get(f"/api/v1/memories/{before['id']}")
    assert read.json()["title"] == before["title"]
    assert read.json()["updated_at"] == before["updated_at"]


async def test_rest_mixed_null_update_preserves_title_and_falsy_values(memory_app):
    _, http = memory_app
    created = await http.post("/api/v1/memories", json=candidate(tags=["saved"], confidence=0.8, importance=7).model_dump(exclude_unset=True))
    assert created.status_code == 201
    before = (await http.get(f"/api/v1/memories/{created.json()['id']}")).json()
    response = await http.put(
        f"/api/v1/memories/{before['id']}", json={"title": None, "importance": 9, "tags": [], "confidence": 0},
    )
    assert response.status_code == 200
    read = await http.get(f"/api/v1/memories/{before['id']}")
    saved = read.json()
    assert saved["title"] == before["title"] and saved["importance"] == 9
    assert saved["tags"] == [] and saved["confidence"] == 0


async def test_mcp_null_update_parity_control(memory_app):
    client, _ = memory_app
    created = await execute(client, "create_memory", candidate(tags=["saved"], confidence=0.8, importance=7).model_dump(exclude_unset=True))
    before = await execute(client, "get_memory", {"memory_id": created["id"]})
    noop = await execute(client, "update_memory", {"memory_id": before["id"], "title": None})
    assert noop["title"] == before["title"] and noop["updated_at"] == before["updated_at"]
    await execute(client, "update_memory", {
        "memory_id": before["id"], "title": None, "importance": 9, "tags": [], "confidence": 0,
    })
    saved = await execute(client, "get_memory", {"memory_id": before["id"]})
    assert saved["title"] == before["title"] and saved["importance"] == 9
    assert saved["tags"] == [] and saved["confidence"] == 0
