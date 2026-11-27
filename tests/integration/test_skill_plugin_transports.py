"""Skill Plugin REST and MCP transport shapes."""

from contextlib import asynccontextmanager

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from httpx import ASGITransport, AsyncClient

from app.bootstrap import build_runtime, dispose_runtime
from app.config.settings import settings
from app.routes.api import skills
from app.routes.mcp import meta_tools


@pytest.fixture
async def skill_plugin_app(skill_plugin_runtime, request, monkeypatch):
    if getattr(request, "param", None) == "warn":
        monkeypatch.setattr(settings, "SKILL_WRITE_PLUGIN_MODE", "warn")
    elif getattr(request, "param", None) == "off":
        monkeypatch.setattr(settings, "SKILL_WRITE_PLUGIN", "")
    monkeypatch.setattr(settings, "SKILLS_ENABLED", True)

    @asynccontextmanager
    async def lifespan(app):
        runtime = await build_runtime()
        app.skill_service = runtime.services.skill
        app.user_service = runtime.services.user
        app.registry = runtime.registry
        app._instance_permitted_tools = runtime.permitted_tools
        app._instance_scopes = runtime.instance_scopes
        try:
            yield
        finally:
            await dispose_runtime(runtime)

    app = FastMCP("Skill Plugin test", lifespan=lifespan)
    meta_tools.register(app)
    skills.register(app)
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
        "name": "transport-skill",
        "description": "Skill created through a transport",
        "content": "# Transport skill\n\n1. Do the thing.\n",
        "tags": [],
        "importance": 7,
    }
    base.update(changes)
    return base


# --- MCP --------------------------------------------------------------------


async def test_mcp_create_omits_warnings_when_allowed(skill_plugin_app):
    client, _ = skill_plugin_app
    created = await execute(client, "create_skill", body())
    assert "plugin_warnings" not in created
    assert created["id"]


async def test_mcp_create_returns_warning(skill_plugin_app):
    client, _ = skill_plugin_app
    created = await execute(client, "create_skill", body(tags=["warn"]))
    assert created["plugin_warnings"][0]["code"] == "source"


async def test_mcp_create_rejection_is_a_tool_error(skill_plugin_app):
    client, _ = skill_plugin_app
    with pytest.raises(ToolError, match="WRITE_PLUGIN_REJECTED"):
        await execute(client, "create_skill", body(tags=["blocked"]))


async def test_mcp_create_unavailable_is_a_tool_error(skill_plugin_app):
    client, _ = skill_plugin_app
    with pytest.raises(ToolError, match="WRITE_PLUGIN_UNAVAILABLE"):
        await execute(client, "create_skill", body(tags=["error"]))


async def test_mcp_update_noop_reports_no_warnings(skill_plugin_app):
    client, _ = skill_plugin_app
    created = await execute(client, "create_skill", body())
    updated = await execute(client, "update_skill", {
        "skill_id": created["id"], "description": "Skill created through a transport",
    })
    assert "plugin_warnings" not in updated


async def test_mcp_delete_warning_and_rejection(skill_plugin_app):
    client, _ = skill_plugin_app
    warned = await execute(client, "create_skill", body(tags=["delete_warn"]))
    deleted = await execute(client, "delete_skill", {"skill_id": warned["id"]})
    assert deleted["success"] is True
    assert deleted["plugin_warnings"][0]["code"] == "source"

    blocked = await execute(client, "create_skill", body(tags=["delete_blocked"]))
    with pytest.raises(ToolError, match="WRITE_PLUGIN_REJECTED"):
        await execute(client, "delete_skill", {"skill_id": blocked["id"]})


async def test_mcp_import_warning_reaches_the_response(skill_plugin_app):
    """import_skill delegates to create_skill, so its warnings surface too."""
    client, _ = skill_plugin_app
    markdown = (
        "---\nname: imported-transport\ndescription: Imported through MCP\n"
        "tags: [warn]\n---\n\nBody\n"
    )
    imported = await execute(client, "import_skill", {"skill_md_content": markdown})
    assert imported["plugin_warnings"][0]["code"] == "source"


# --- REST -------------------------------------------------------------------


async def test_rest_create_and_delete_shapes(skill_plugin_app):
    _, http = skill_plugin_app
    created = await http.post("/api/v1/skills", json=body(tags=["warn"]))
    assert created.status_code == 201
    assert created.json()["plugin_warnings"][0]["code"] == "source"
    skill_id = created.json()["id"]

    deleted = await http.delete(f"/api/v1/skills/{skill_id}")
    assert deleted.status_code == 200
    assert deleted.json()["success"] is True


async def test_rest_rejection_is_400(skill_plugin_app):
    _, http = skill_plugin_app
    response = await http.post("/api/v1/skills", json=body(tags=["blocked"]))
    assert response.status_code == 400
    assert "Remove the blocked tag" in response.json()["error"]


async def test_rest_unavailable_is_503(skill_plugin_app):
    _, http = skill_plugin_app
    response = await http.post("/api/v1/skills", json=body(tags=["error"]))
    assert response.status_code == 503


@pytest.mark.parametrize("skill_plugin_app", ["warn"], indirect=True)
async def test_rest_warn_mode_downgrades_rejection_to_201(skill_plugin_app):
    _, http = skill_plugin_app
    response = await http.post("/api/v1/skills", json=body(tags=["blocked"]))
    assert response.status_code == 201
    assert response.json()["plugin_warnings"][0]["outcome"] == "warn"


@pytest.mark.parametrize("skill_plugin_app", ["off"], indirect=True)
async def test_rest_without_plugin_has_no_warnings(skill_plugin_app):
    _, http = skill_plugin_app
    created = await http.post("/api/v1/skills", json=body(tags=["blocked"]))
    assert created.status_code == 201
    assert "plugin_warnings" not in created.json()
