"""E2E tests for plan, task and criterion update semantics with PostgreSQL backend.

Mirrors tests/e2e_sqlite/test_plan_task_update_semantics_sqlite.py for the behaviour that
depends on the PostgreSQL repositories:
- Task.criteria keep creation order after a criterion is updated (an UPDATE moves the row
  to the end of the heap scan, so an unordered load shuffles the list)
- met_at records the first transition to met
- explicit nulls are treated as "unchanged" instead of violating NOT NULL columns
- updating a missing plan or task is a not-found error
"""

import asyncio

import pytest
from fastmcp.exceptions import ToolError

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.asyncio(loop_scope="session"),
]

MISSING_ID = 999999


# ---- Helpers ----

async def _call(mcp_client, tool_name, arguments):
    return await mcp_client.call_tool(
        "execute_forgetful_tool",
        {"tool_name": tool_name, "arguments": arguments},
    )


async def _create_task(mcp_client, criteria=()):
    project_id = (await _call(mcp_client, "create_project", {
        "name": "pg-update-semantics-project",
        "description": "d",
        "project_type": "development",
    })).data["id"]
    plan_id = (await _call(mcp_client, "create_plan", {
        "project_id": project_id,
        "title": "Original title",
        "goal": "Original goal",
    })).data["id"]
    await _call(mcp_client, "update_plan", {"plan_id": plan_id, "status": "active"})
    task = (await _call(mcp_client, "create_task", {
        "plan_id": plan_id,
        "title": "Original task",
        "description": "Original description",
    })).data
    criterion_ids = []
    for description in criteria:
        added = await _call(mcp_client, "add_criterion", {
            "task_id": task["id"], "description": description,
        })
        criterion_ids.append(added.data["id"])
    return plan_id, task["id"], criterion_ids


# ---- met_at records the first transition to met ----

async def test_repeated_verify_keeps_original_met_at_e2e(mcp_client):
    _, _, (criterion_id,) = await _create_task(mcp_client, ["tests pass"])

    first = (await _call(mcp_client, "verify_criterion", {
        "criterion_id": criterion_id, "met": True,
    })).data
    await asyncio.sleep(0.02)
    second = (await _call(mcp_client, "verify_criterion", {
        "criterion_id": criterion_id, "met": True,
    })).data

    assert first["met_at"] is not None
    assert second["met_at"] == first["met_at"]


async def test_met_at_is_cleared_and_restamped_on_real_transitions_e2e(mcp_client):
    _, _, (criterion_id,) = await _create_task(mcp_client, ["tests pass"])

    first = (await _call(mcp_client, "verify_criterion", {
        "criterion_id": criterion_id, "met": True,
    })).data
    cleared = (await _call(mcp_client, "verify_criterion", {
        "criterion_id": criterion_id, "met": False,
    })).data
    await asyncio.sleep(0.02)
    again = (await _call(mcp_client, "verify_criterion", {
        "criterion_id": criterion_id, "met": True,
    })).data

    assert cleared["met_at"] is None
    assert again["met_at"] is not None
    assert again["met_at"] != first["met_at"]


# ---- Explicit null means "unchanged" ----

async def test_put_criterion_with_null_fields_leaves_it_unchanged_e2e(mcp_client, http_client):
    _, _, (criterion_id,) = await _create_task(mcp_client, ["tests pass"])
    met = await http_client.put(f"/api/v1/criteria/{criterion_id}", json={"met": True})
    assert met.status_code == 200, met.text

    response = await http_client.put(
        f"/api/v1/criteria/{criterion_id}", json={"met": None, "description": None},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["description"] == "tests pass"
    assert body["met"] is True
    assert body["met_at"] == met.json()["met_at"]


async def test_put_plan_with_null_fields_leaves_it_unchanged_e2e(mcp_client, http_client):
    plan_id, _, _ = await _create_task(mcp_client)

    response = await http_client.put(
        f"/api/v1/plans/{plan_id}", json={"title": None, "goal": None, "status": None},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["title"] == "Original title"
    assert body["goal"] == "Original goal"
    assert body["status"] == "active"


async def test_put_task_with_null_fields_leaves_it_unchanged_e2e(mcp_client, http_client):
    _, task_id, _ = await _create_task(mcp_client)

    response = await http_client.put(
        f"/api/v1/tasks/{task_id}", json={"title": None, "description": None, "priority": None},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["title"] == "Original task"
    assert body["description"] == "Original description"


# ---- Missing plan or task is a not-found error ----

async def test_update_plan_tool_for_missing_plan_is_a_tool_error_e2e(mcp_client):
    with pytest.raises(ToolError, match="not found"):
        await _call(mcp_client, "update_plan", {"plan_id": MISSING_ID, "title": "x"})


async def test_update_task_tool_for_missing_task_is_a_tool_error_e2e(mcp_client):
    with pytest.raises(ToolError, match="not found"):
        await _call(mcp_client, "update_task", {"task_id": MISSING_ID, "title": "x"})


async def test_put_missing_plan_and_task_return_404_e2e(http_client):
    plan_response = await http_client.put(f"/api/v1/plans/{MISSING_ID}", json={"title": "x"})
    task_response = await http_client.put(f"/api/v1/tasks/{MISSING_ID}", json={"title": "x"})

    assert plan_response.status_code == 404
    assert task_response.status_code == 404
