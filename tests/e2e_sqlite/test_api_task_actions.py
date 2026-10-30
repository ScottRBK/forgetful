"""Task action request validation through HTTP and a temporary SQLite database."""

import sqlite3

import pytest
from fastmcp import FastMCP
from httpx import ASGITransport, AsyncClient

from app import bootstrap
from app.config.settings import settings
from app.routes.api import plans, projects, tasks


class FixedEmbeddings:
    async def generate_embedding(self, text: str) -> list[float]:
        return [1.0] + [0.0] * (settings.EMBEDDING_DIMENSIONS - 1)


@pytest.fixture
async def action_client(tmp_path, monkeypatch):
    """Use real persistence without local models, remote providers, or user data."""
    database_path = tmp_path / "task-actions.db"
    monkeypatch.setattr(settings, "DATABASE", "SQLite")
    monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(database_path))
    monkeypatch.setattr(settings, "PLANNING_ENABLED", True)
    monkeypatch.setattr(settings, "ACTIVITY_ENABLED", False)
    monkeypatch.setattr(settings, "MEMORY_WRITE_PLUGIN", "")
    monkeypatch.setattr(bootstrap, "get_embedding_adapter", FixedEmbeddings)
    monkeypatch.setattr(bootstrap, "get_reranker_adapter", lambda: None)
    monkeypatch.setattr(bootstrap, "check_first_run_models", lambda: None)
    runtime = await bootstrap.build_runtime()
    try:
        mcp = FastMCP("Task action validation")
        mcp.user_service = runtime.services.user
        mcp.project_service = runtime.services.project
        mcp.plan_service = runtime.services.plan
        mcp.task_service = runtime.services.task
        for routes in (projects, plans, tasks):
            routes.register(mcp)
        transport = ASGITransport(app=mcp.http_app(), raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client, database_path
    finally:
        await bootstrap.dispose_runtime(runtime)


@pytest.fixture
async def action_tasks(action_client):
    client, database_path = action_client
    response = await client.post("/api/v1/projects", json={
        "name": "Task actions", "description": "Request validation", "project_type": "development",
    })
    assert response.status_code == 201, response.text
    response = await client.post("/api/v1/plans", json={
        "project_id": response.json()["id"], "title": "Task action plan",
    })
    assert response.status_code == 201, response.text
    plan_id = response.json()["id"]
    created = []
    for title in ("Prerequisite", "Action target"):
        response = await client.post("/api/v1/tasks", json={"plan_id": plan_id, "title": title})
        assert response.status_code == 201, response.text
        created.append(response.json())
    prerequisite, target = created
    return client, database_path, target, prerequisite


def persisted_actions(database_path):
    """Read committed rows independently of the HTTP response/service objects."""
    with sqlite3.connect(database_path) as connection:
        return (
            connection.execute("SELECT * FROM tasks ORDER BY id").fetchall(),
            connection.execute("SELECT * FROM task_dependencies ORDER BY id").fetchall(),
        )


@pytest.mark.parametrize("action", ["transition", "claim", "dependencies"])
@pytest.mark.parametrize("content", ["null", "[]", '"body"', "1", "true", "{}", "{", ""])
async def test_reject_invalid_action_body(action_tasks, action, content):
    client, database_path, target, _ = action_tasks
    before = persisted_actions(database_path)
    response = await client.post(
        f"/api/v1/tasks/{target['id']}/{action}", content=content,
        headers={"Content-Type": "application/json"},
    )
    after = persisted_actions(database_path)
    assert response.status_code == 400, (response.text, before == after)
    assert "error" in response.json()
    assert after == before


@pytest.mark.parametrize("action", ["transition", "claim", "dependencies"])
@pytest.mark.parametrize("invalid", [None, [], {}, True, 1.5, 1.0, "1"])
async def test_reject_noninteger_action_fields(action_tasks, action, invalid):
    client, database_path, target, prerequisite = action_tasks
    bodies = {
        "transition": {"state": "doing", "version": invalid},
        "claim": {"agent_id": "agent-1", "version": invalid},
        "dependencies": {"depends_on_task_id": invalid},
    }
    # The prerequisite is the first task: bool/float/string coercions would
    # otherwise resolve to a real dependency, just as version=1 matches the task.
    assert prerequisite["id"] == 1
    before = persisted_actions(database_path)
    response = await client.post(f"/api/v1/tasks/{target['id']}/{action}", json=bodies[action])
    after = persisted_actions(database_path)
    assert response.status_code == 400, (response.text, before == after)
    assert "error" in response.json()
    assert after == before


@pytest.mark.parametrize("agent_id", [None, [], {}, 42, True])
async def test_reject_nonstring_agent_id(action_tasks, agent_id):
    client, database_path, target, _ = action_tasks
    before = persisted_actions(database_path)
    response = await client.post(f"/api/v1/tasks/{target['id']}/claim", json={
        "agent_id": agent_id, "version": target["version"],
    })
    after = persisted_actions(database_path)
    assert response.status_code == 400, (response.text, before == after)
    assert "error" in response.json()
    assert after == before


@pytest.mark.parametrize("action,field", [
    ("transition", "version"), ("claim", "version"), ("dependencies", "depends_on_task_id"),
])
@pytest.mark.parametrize("number", ["NaN", "Infinity", "1e400"])
async def test_reject_nonfinite_numbers_without_error_serialization_failure(action_tasks, action, field, number):
    client, database_path, target, _ = action_tasks
    before = persisted_actions(database_path)
    content = f'{{"state":"doing","agent_id":"agent-1","{field}":{number}}}'
    response = await client.post(
        f"/api/v1/tasks/{target['id']}/{action}", content=content,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400, response.text
    assert "error" in response.json()
    assert persisted_actions(database_path) == before


@pytest.mark.parametrize("state", [None, [], {}, True, 42, "unknown"])
async def test_reject_invalid_state(action_tasks, state):
    client, database_path, target, _ = action_tasks
    before = persisted_actions(database_path)
    response = await client.post(f"/api/v1/tasks/{target['id']}/transition", json={
        "state": state, "version": target["version"],
    })
    assert response.status_code == 400, response.text
    assert "error" in response.json()
    assert persisted_actions(database_path) == before


async def test_valid_actions_preserve_state_dependency_and_version_rules(action_tasks):
    client, database_path, target, prerequisite = action_tasks
    target_url = f"/api/v1/tasks/{target['id']}"
    prerequisite_url = f"/api/v1/tasks/{prerequisite['id']}"

    response = await client.post(f"{target_url}/dependencies", json={"depends_on_task_id": prerequisite["id"]})
    assert response.status_code == 201, response.text
    assert response.json()["depends_on_task_id"] == prerequisite["id"]
    before = persisted_actions(database_path)
    # Existing same-task/cycle checks still reject validly typed requests.
    for task_url, dependency_id in ((target_url, target["id"]), (prerequisite_url, target["id"])):
        response = await client.post(f"{task_url}/dependencies", json={"depends_on_task_id": dependency_id})
        assert response.status_code == 400, response.text
    for action, body in (
        ("claim", {"agent_id": "agent-1", "version": 1}),
        ("transition", {"state": "doing", "version": 1}),
        ("transition", {"state": "done", "version": 1}),
    ):
        response = await client.post(f"{target_url}/{action}", json=body)
        assert response.status_code == 422, response.text
    assert persisted_actions(database_path) == before

    for version, state in ((1, "doing"), (2, "done")):
        response = await client.post(f"{prerequisite_url}/transition", json={"state": state, "version": version})
        assert response.status_code == 200, response.text
        assert response.json()["version"] == version + 1
    response = await client.post(f"{target_url}/claim", json={"agent_id": "agent-1", "version": 1})
    assert response.status_code == 200, response.text
    assert response.json()["state"] == "doing"
    assert response.json()["assigned_agent"] == "agent-1"
    assert response.json()["version"] == 2
    assert (await client.get(target_url)).json() == response.json()
    before = persisted_actions(database_path)
    for action, body, status in (
        ("claim", {"agent_id": "agent-2", "version": 1}, 409),
        ("transition", {"state": "done", "version": 1}, 409),
        ("claim", {"agent_id": "agent-2", "version": 2}, 422),
    ):
        response = await client.post(f"{target_url}/{action}", json=body)
        assert response.status_code == status, response.text
    assert persisted_actions(database_path) == before


@pytest.mark.parametrize("action,body", [
    ("claim", {"agent_id": "agent-1", "version": 1}),
    ("transition", {"state": "doing", "version": 1}),
    ("dependencies", {"depends_on_task_id": 1}),
])
async def test_valid_action_on_missing_task_returns_not_found(action_tasks, action, body):
    client, database_path, _, _ = action_tasks
    before = persisted_actions(database_path)
    response = await client.post(f"/api/v1/tasks/99999/{action}", json=body)
    assert response.status_code == 404, response.text
    assert persisted_actions(database_path) == before
