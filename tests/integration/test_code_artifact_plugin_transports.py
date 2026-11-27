"""Code Artifact Plugin REST and MCP transport shapes."""

from contextlib import asynccontextmanager

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from httpx import ASGITransport, AsyncClient

from app.bootstrap import build_runtime, dispose_runtime
from app.config.settings import settings
from app.routes.api import code_artifacts
from app.routes.mcp import meta_tools


@pytest.fixture
async def artifact_plugin_app(code_artifact_plugin_runtime, request, monkeypatch):
    if getattr(request, "param", None) == "warn":
        monkeypatch.setattr(settings, "CODE_ARTIFACT_WRITE_PLUGIN_MODE", "warn")
    elif getattr(request, "param", None) == "off":
        monkeypatch.setattr(settings, "CODE_ARTIFACT_WRITE_PLUGIN", "")

    @asynccontextmanager
    async def lifespan(app):
        runtime = await build_runtime()
        app.code_artifact_service = runtime.services.code_artifact
        app.user_service = runtime.services.user
        app.registry = runtime.registry
        app._instance_permitted_tools = runtime.permitted_tools
        app._instance_scopes = runtime.instance_scopes
        try:
            yield
        finally:
            await dispose_runtime(runtime)

    app = FastMCP("Code Artifact Plugin test", lifespan=lifespan)
    meta_tools.register(app)
    code_artifacts.register(app)
    async with Client(app) as client:
        async with AsyncClient(
            transport=ASGITransport(app=app.http_app(), raise_app_exceptions=False),
            base_url="http://test",
        ) as http:
            yield client, http


async def execute(client, name, arguments):
    result = await client.call_tool(
        "execute_forgetful_tool", {"tool_name": name, "arguments": arguments},
    )
    return result.data


def body(**changes):
    base = {
        "title": "Transport artifact",
        "description": "Created through a transport",
        "code": "def transport_helper():\n    return 1\n",
        "language": "python",
        "tags": [],
    }
    base.update(changes)
    return base


# --- MCP --------------------------------------------------------------------


async def test_mcp_create_omits_warnings_when_allowed(artifact_plugin_app):
    client, _ = artifact_plugin_app
    created = await execute(client, "create_code_artifact", body())
    assert "plugin_warnings" not in created
    assert created["id"]


async def test_mcp_create_returns_warning(artifact_plugin_app):
    client, _ = artifact_plugin_app
    created = await execute(client, "create_code_artifact", body(tags=["warn"]))
    assert created["plugin_warnings"][0]["code"] == "source"


async def test_mcp_create_rejection_is_a_tool_error(artifact_plugin_app):
    client, _ = artifact_plugin_app
    with pytest.raises(ToolError, match="WRITE_PLUGIN_REJECTED"):
        await execute(client, "create_code_artifact", body(tags=["blocked"]))


async def test_mcp_create_unavailable_is_a_tool_error(artifact_plugin_app):
    client, _ = artifact_plugin_app
    with pytest.raises(ToolError, match="WRITE_PLUGIN_UNAVAILABLE"):
        await execute(client, "create_code_artifact", body(tags=["error"]))


async def test_mcp_update_noop_reports_no_warnings(artifact_plugin_app):
    client, _ = artifact_plugin_app
    created = await execute(client, "create_code_artifact", body())
    updated = await execute(client, "update_code_artifact", {
        "artifact_id": created["id"], "description": "Created through a transport",
    })
    assert "plugin_warnings" not in updated


async def test_mcp_delete_warning_and_rejection(artifact_plugin_app):
    client, _ = artifact_plugin_app
    warned = await execute(client, "create_code_artifact", body(tags=["delete_warn"]))
    deleted = await execute(client, "delete_code_artifact", {"artifact_id": warned["id"]})
    assert deleted["success"] is True
    assert deleted["plugin_warnings"][0]["code"] == "source"

    blocked = await execute(client, "create_code_artifact", body(tags=["delete_blocked"]))
    with pytest.raises(ToolError, match="WRITE_PLUGIN_REJECTED"):
        await execute(client, "delete_code_artifact", {"artifact_id": blocked["id"]})


# --- REST -------------------------------------------------------------------


async def test_rest_create_and_delete_shapes(artifact_plugin_app):
    _, http = artifact_plugin_app
    created = await http.post("/api/v1/code-artifacts", json=body(tags=["warn"]))
    assert created.status_code == 201
    assert created.json()["plugin_warnings"][0]["code"] == "source"
    artifact_id = created.json()["id"]

    deleted = await http.delete(f"/api/v1/code-artifacts/{artifact_id}")
    assert deleted.status_code == 200
    assert deleted.json()["success"] is True


async def test_rest_rejection_is_400(artifact_plugin_app):
    _, http = artifact_plugin_app
    response = await http.post("/api/v1/code-artifacts", json=body(tags=["blocked"]))
    assert response.status_code == 400
    assert "Remove the blocked tag" in response.json()["error"]


async def test_rest_unavailable_is_503(artifact_plugin_app):
    _, http = artifact_plugin_app
    response = await http.post("/api/v1/code-artifacts", json=body(tags=["error"]))
    assert response.status_code == 503


@pytest.mark.parametrize("artifact_plugin_app", ["warn"], indirect=True)
async def test_rest_warn_mode_downgrades_rejection_to_201(artifact_plugin_app):
    _, http = artifact_plugin_app
    response = await http.post("/api/v1/code-artifacts", json=body(tags=["blocked"]))
    assert response.status_code == 201
    assert response.json()["plugin_warnings"][0]["outcome"] == "warn"


@pytest.mark.parametrize("artifact_plugin_app", ["off"], indirect=True)
async def test_rest_without_plugin_has_no_warnings(artifact_plugin_app):
    _, http = artifact_plugin_app
    created = await http.post("/api/v1/code-artifacts", json=body(tags=["blocked"]))
    assert created.status_code == 201
    assert "plugin_warnings" not in created.json()
