"""Task Plugin REST and MCP transport shapes."""

from contextlib import asynccontextmanager

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from httpx import ASGITransport, AsyncClient

from app.bootstrap import build_runtime, dispose_runtime
from app.config.settings import settings
from app.routes.api import plans, projects, tasks
from app.routes.mcp import meta_tools


@pytest.fixture
async def task_plugin_app(task_plugin_runtime, request, monkeypatch):
    if getattr(request, "param", None) == "warn":
        monkeypatch.setattr(settings, "TASK_WRITE_PLUGIN_MODE", "warn")
    elif getattr(request, "param", None) == "off":
        monkeypatch.setattr(settings, "TASK_WRITE_PLUGIN", "")
    monkeypatch.setattr(settings, "PLANNING_ENABLED", True)

    @asynccontextmanager
    async def lifespan(app):
        runtime = await build_runtime()
        app.task_service = runtime.services.task
        app.plan_service = runtime.services.plan
        app.project_service = runtime.services.project
        app.user_service = runtime.services.user
        app.registry = runtime.registry
        app._instance_permitted_tools = runtime.permitted_tools
        app._instance_scopes = runtime.instance_scopes
        try:
            yield
        finally:
            await dispose_runtime(runtime)

    app = FastMCP("Task Plugin test", lifespan=lifespan)
    meta_tools.register(app)
    projects.register(app)
    plans.register(app)
    tasks.register(app)
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


async def _active_plan(http):
    created = await http.post("/api/v1/projects", json={
        "name": "Task plugin project",
        "description": "Scope for transport tests",
        "project_type": "development",
    })
    assert created.status_code in (200, 201), created.text
    project_id = created.json()["id"]

    plan = await http.post("/api/v1/plans", json={
        "title": "Task plugin plan", "goal": "Ship", "project_id": project_id,
    })
    assert plan.status_code in (200, 201), plan.text
    plan_id = plan.json()["id"]
    activated = await http.put(f"/api/v1/plans/{plan_id}", json={"status": "active"})
    assert activated.status_code in (200, 201), activated.text
    return plan_id


def body(plan_id: int, **changes):
    base = {"plan_id": plan_id, "title": "transport task"}
    base.update(changes)
    return base


# --- MCP --------------------------------------------------------------------


async def test_mcp_create_omits_warnings_when_allowed(task_plugin_app):
    client, http = task_plugin_app
    plan_id = await _active_plan(http)
    created = await execute(client, "create_task", body(plan_id))
    assert "plugin_warnings" not in created
    assert created["id"]


async def test_mcp_create_returns_warning(task_plugin_app):
    client, http = task_plugin_app
    plan_id = await _active_plan(http)
    created = await execute(client, "create_task", body(plan_id, title="warn task"))
    assert created["plugin_warnings"][0]["code"] == "source"


async def test_mcp_create_rejection_is_a_tool_error(task_plugin_app):
    client, http = task_plugin_app
    plan_id = await _active_plan(http)
    with pytest.raises(ToolError, match="WRITE_PLUGIN_REJECTED"):
        await execute(client, "create_task", body(plan_id, title="blocked task"))


async def test_mcp_transition_warning_and_rejection(task_plugin_app):
    client, http = task_plugin_app
    plan_id = await _active_plan(http)
    created = await execute(client, "create_task", body(plan_id))
    transitioned = await execute(client, "transition_task", {
        "task_id": created["id"], "state": "doing", "version": created["version"],
    })
    assert transitioned["state"] == "doing"


async def test_mcp_update_noop_reports_no_warnings(task_plugin_app):
    client, http = task_plugin_app
    plan_id = await _active_plan(http)
    created = await execute(client, "create_task", body(plan_id))
    updated = await execute(client, "update_task", {
        "task_id": created["id"], "title": "transport task",
    })
    assert "plugin_warnings" not in updated


@pytest.mark.parametrize("task_plugin_app", ["off"], indirect=True)
async def test_mcp_without_plugin_has_no_warnings(task_plugin_app):
    client, http = task_plugin_app
    plan_id = await _active_plan(http)
    created = await execute(client, "create_task", body(plan_id, title="blocked task"))
    assert "plugin_warnings" not in created


# --- REST -------------------------------------------------------------------


async def test_rest_create_shape(task_plugin_app):
    _, http = task_plugin_app
    plan_id = await _active_plan(http)
    created = await http.post("/api/v1/tasks", json=body(plan_id, title="warn task"))
    assert created.status_code == 201
    assert created.json()["plugin_warnings"][0]["code"] == "source"


async def test_rest_rejection_is_400(task_plugin_app):
    _, http = task_plugin_app
    plan_id = await _active_plan(http)
    response = await http.post("/api/v1/tasks", json=body(plan_id, title="blocked task"))
    assert response.status_code == 400
    assert "Blocked by policy" in response.json()["error"]


async def test_rest_delete_warning_and_rejection(task_plugin_app):
    """Deletion is REST-only: there is no MCP tool and therefore no CLI path."""
    _, http = task_plugin_app
    plan_id = await _active_plan(http)
    created = await http.post("/api/v1/tasks", json=body(plan_id, title="delete-warn task"))
    assert created.status_code == 201
    task_id = created.json()["id"]

    deleted = await http.delete(f"/api/v1/tasks/{task_id}")
    assert deleted.status_code == 200
    assert deleted.json()["success"] is True
    assert deleted.json()["plugin_warnings"][0]["message"] == "Check the source."

    blocked = await http.post(
        "/api/v1/tasks", json=body(plan_id, title="delete-blocked task"),
    )
    assert blocked.status_code == 201
    rejected = await http.delete(f"/api/v1/tasks/{blocked.json()['id']}")
    assert rejected.status_code == 400
    assert "Blocked by policy" in rejected.json()["error"]


@pytest.mark.parametrize("task_plugin_app", ["warn"], indirect=True)
async def test_rest_warn_mode_downgrades_rejection_to_201(task_plugin_app):
    _, http = task_plugin_app
    plan_id = await _active_plan(http)
    response = await http.post("/api/v1/tasks", json=body(plan_id, title="blocked task"))
    assert response.status_code == 201
    assert response.json()["plugin_warnings"][0]["outcome"] == "warn"
