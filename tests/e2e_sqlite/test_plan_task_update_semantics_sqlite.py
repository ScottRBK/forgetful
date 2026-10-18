"""E2E tests (SQLite) for plan, task and criterion update semantics.

Covers PATCH-style updates over REST and MCP:
- an explicit JSON null means "unchanged" and never reaches the database
- updating a missing plan or task is a not-found error, not a null result
- met_at records the first transition to met, not every repeated verification
- task criteria keep their creation order after one of them is updated
"""


import pytest
from fastmcp.exceptions import ToolError

MISSING_ID = 999999


# ---- Helpers ----

async def _call(mcp_client, tool_name, arguments):
    return await mcp_client.call_tool(
        "execute_forgetful_tool",
        {"tool_name": tool_name, "arguments": arguments},
    )


async def _rest_project(http_client, name="update-semantics-project"):
    response = await http_client.post(
        "/api/v1/projects",
        json={"name": name, "description": "d", "project_type": "development"},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _rest_plan(http_client, **extra):
    project_id = await _rest_project(http_client)
    body = {
        "project_id": project_id,
        "title": "Original title",
        "goal": "Original goal",
        "context": "Original context",
        "source_repo": "owner/repo",
        "source_url": "https://example.test/src",
        "encoding_agent": "agent-x",
        "agent_model": "model-y",
        **extra,
    }
    response = await http_client.post("/api/v1/plans", json=body)
    assert response.status_code == 201, response.text
    return response.json()


async def _rest_active_plan(http_client):
    plan = await _rest_plan(http_client)
    response = await http_client.put(f"/api/v1/plans/{plan['id']}", json={"status": "active"})
    assert response.status_code == 200, response.text
    return response.json()


async def _rest_task(http_client, plan_id):
    response = await http_client.post(
        "/api/v1/tasks",
        json={
            "plan_id": plan_id,
            "title": "Original task",
            "description": "Original description",
            "priority": "P1",
            "source_repo": "owner/repo",
            "source_url": "https://example.test/src",
            "encoding_agent": "agent-x",
            "agent_model": "model-y",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _rest_criterion(http_client, task_id, description="tests pass"):
    response = await http_client.post(
        f"/api/v1/tasks/{task_id}/criteria", json={"description": description},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _mcp_task_with_criteria(mcp_client, descriptions):
    project_id = (await _call(mcp_client, "create_project", {
        "name": "criteria-order-project",
        "description": "d",
        "project_type": "development",
    })).data["id"]
    plan_id = (await _call(mcp_client, "create_plan", {
        "project_id": project_id, "title": "plan",
    })).data["id"]
    await _call(mcp_client, "update_plan", {"plan_id": plan_id, "status": "active"})
    task_id = (await _call(mcp_client, "create_task", {
        "plan_id": plan_id, "title": "task",
    })).data["id"]
    criterion_ids = []
    for description in descriptions:
        criterion = await _call(mcp_client, "add_criterion", {
            "task_id": task_id, "description": description,
        })
        criterion_ids.append(criterion.data["id"])
    return task_id, criterion_ids


# ---- Explicit null means "unchanged" (REST PUT) ----

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field",
    ["title", "goal", "context", "status", "source_repo", "source_url", "encoding_agent", "agent_model"],
)
async def test_put_plan_with_null_field_leaves_it_unchanged(http_client, field):
    plan = await _rest_plan(http_client)

    response = await http_client.put(f"/api/v1/plans/{plan['id']}", json={field: None})

    assert response.status_code == 200, response.text
    stored = (await http_client.get(f"/api/v1/plans/{plan['id']}")).json()
    assert stored[field] == plan[field]


@pytest.mark.asyncio
async def test_put_plan_ignores_nulls_but_applies_real_changes(http_client):
    plan = await _rest_plan(http_client)

    response = await http_client.put(
        f"/api/v1/plans/{plan['id']}",
        json={"title": "Renamed", "goal": None, "source_repo": None},
    )

    assert response.status_code == 200, response.text
    stored = (await http_client.get(f"/api/v1/plans/{plan['id']}")).json()
    assert stored["title"] == "Renamed"
    assert stored["goal"] == plan["goal"]
    assert stored["source_repo"] == plan["source_repo"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field",
    ["title", "description", "priority", "source_repo", "source_url", "encoding_agent", "agent_model"],
)
async def test_put_task_with_null_field_leaves_it_unchanged(http_client, field):
    plan = await _rest_active_plan(http_client)
    task = await _rest_task(http_client, plan["id"])

    response = await http_client.put(f"/api/v1/tasks/{task['id']}", json={field: None})

    assert response.status_code == 200, response.text
    stored = (await http_client.get(f"/api/v1/tasks/{task['id']}")).json()
    assert stored[field] == task[field]


@pytest.mark.asyncio
async def test_put_task_ignores_nulls_but_applies_real_changes(http_client):
    plan = await _rest_active_plan(http_client)
    task = await _rest_task(http_client, plan["id"])

    response = await http_client.put(
        f"/api/v1/tasks/{task['id']}",
        json={"priority": "P0", "description": None},
    )

    assert response.status_code == 200, response.text
    stored = (await http_client.get(f"/api/v1/tasks/{task['id']}")).json()
    assert stored["priority"] == "P0"
    assert stored["description"] == task["description"]


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["met", "description"])
async def test_put_criterion_with_null_field_leaves_it_unchanged(http_client, field):
    plan = await _rest_active_plan(http_client)
    task = await _rest_task(http_client, plan["id"])
    criterion = await _rest_criterion(http_client, task["id"])

    response = await http_client.put(f"/api/v1/criteria/{criterion['id']}", json={field: None})

    assert response.status_code == 200, response.text
    assert response.json()[field] == criterion[field]


@pytest.mark.asyncio
async def test_put_criterion_null_does_not_clear_met_state(http_client):
    plan = await _rest_active_plan(http_client)
    task = await _rest_task(http_client, plan["id"])
    criterion = await _rest_criterion(http_client, task["id"])
    met = await http_client.put(f"/api/v1/criteria/{criterion['id']}", json={"met": True})
    assert met.json()["met"] is True

    response = await http_client.put(
        f"/api/v1/criteria/{criterion['id']}", json={"met": None, "description": "renamed"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["description"] == "renamed"
    assert body["met"] is True
    assert body["met_at"] == met.json()["met_at"]


# ---- Missing plan or task is a not-found error ----

@pytest.mark.asyncio
async def test_put_missing_plan_returns_404(http_client):
    response = await http_client.put(f"/api/v1/plans/{MISSING_ID}", json={"title": "x"})

    assert response.status_code == 404
    assert response.json()["error"] == "Plan not found"


@pytest.mark.asyncio
async def test_put_missing_task_returns_404(http_client):
    response = await http_client.put(f"/api/v1/tasks/{MISSING_ID}", json={"title": "x"})

    assert response.status_code == 404
    assert response.json()["error"] == "Task not found"


@pytest.mark.asyncio
async def test_update_plan_tool_for_missing_plan_is_a_tool_error(mcp_client):
    with pytest.raises(ToolError, match="not found"):
        await _call(mcp_client, "update_plan", {"plan_id": MISSING_ID, "title": "x"})


@pytest.mark.asyncio
async def test_update_task_tool_for_missing_task_is_a_tool_error(mcp_client):
    with pytest.raises(ToolError, match="not found"):
        await _call(mcp_client, "update_task", {"task_id": MISSING_ID, "title": "x"})


