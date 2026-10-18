"""SQLite end-to-end tests for task dependency, criteria and plan-state invariants.

Exercises the full stack (MCP tools / REST routes -> TaskService -> SqliteTaskRepository)
on in-memory SQLite, plus file-backed SQLite where real concurrent connections matter.
"""

import pytest
from fastmcp.exceptions import ToolError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _tool(client, tool_name, /, **arguments):
    return await client.call_tool(
        "execute_forgetful_tool", {"tool_name": tool_name, "arguments": arguments},
    )


async def _mcp_active_plan(client, project_id, title="plan"):
    plan_id = (await _tool(client, "create_plan", project_id=project_id, title=title)).data["id"]
    await _tool(client, "update_plan", plan_id=plan_id, status="active")
    return plan_id


async def _mcp_project(client, name):
    return (await _tool(
        client, "create_project", name=name, description=f"{name} project", project_type="development",
    )).data["id"]


async def _rest_project_and_plans(http_client, count=1):
    r = await http_client.post("/api/v1/projects", json={
        "name": "integrity-rest", "description": "integrity", "project_type": "development"})
    assert r.status_code == 201, r.text
    project_id = r.json()["id"]
    plan_ids = []
    for index in range(count):
        r = await http_client.post("/api/v1/plans", json={"project_id": project_id, "title": f"P{index}"})
        assert r.status_code == 201, r.text
        plan_id = r.json()["id"]
        r = await http_client.put(f"/api/v1/plans/{plan_id}", json={"status": "active"})
        assert r.status_code == 200, r.text
        plan_ids.append(plan_id)
    return plan_ids


async def _rest_task(http_client, plan_id, title, **extra):
    r = await http_client.post("/api/v1/tasks", json={"plan_id": plan_id, "title": title, **extra})
    assert r.status_code == 201, r.text
    return r.json()


async def _titles(client, plan_id):
    data = (await _tool(client, "query_tasks", plan_id=plan_id)).data
    return [t["title"] for t in data["tasks"]]


# ---------------------------------------------------------------------------
# create_task is all-or-nothing
# ---------------------------------------------------------------------------


async def test_failed_create_task_leaves_no_orphan_via_mcp(mcp_client):
    project_id = await _mcp_project(mcp_client, "atomic-create")
    plan_a = await _mcp_active_plan(mcp_client, project_id, "A")
    plan_b = await _mcp_active_plan(mcp_client, project_id, "B")
    foreign = (await _tool(mcp_client, "create_task", plan_id=plan_b, title="foreign")).data["id"]
    first = (await _tool(mcp_client, "create_task", plan_id=plan_a, title="first")).data["id"]

    for dependency_ids in ([foreign], [999999], [first, 999999]):
        with pytest.raises(ToolError):
            await _tool(
                mcp_client, "create_task", plan_id=plan_a, title="X",
                dependency_ids=dependency_ids, criteria=[{"description": "c"}],
            )

    assert await _titles(mcp_client, plan_a) == ["first"]


async def test_duplicate_dependency_ids_in_create_task_leave_no_orphan(mcp_client):
    project_id = await _mcp_project(mcp_client, "dup-ids-create")
    plan_id = await _mcp_active_plan(mcp_client, project_id)
    prereq = (await _tool(mcp_client, "create_task", plan_id=plan_id, title="prereq")).data["id"]

    with pytest.raises(ToolError, match="more than once"):
        await _tool(
            mcp_client, "create_task", plan_id=plan_id, title="X", dependency_ids=[prereq, prereq],
        )

    assert await _titles(mcp_client, plan_id) == ["prereq"]


async def test_rest_create_task_with_cross_plan_dependency_is_a_client_error(http_client):
    plan_a, plan_b = await _rest_project_and_plans(http_client, count=2)
    foreign = await _rest_task(http_client, plan_b, "foreign")

    r = await http_client.post("/api/v1/tasks", json={
        "plan_id": plan_a, "title": "X", "dependency_ids": [foreign["id"]],
        "criteria": [{"description": "c"}],
    })

    assert r.status_code == 400, r.text
    assert "same plan" in r.json()["error"]
    listed = await http_client.get(f"/api/v1/tasks?plan_id={plan_a}")
    assert listed.json()["total"] == 0
