"""E2E tests (SQLite): malformed REST requests are client errors, never 500.

Covers non-numeric / out-of-range path ids, invalid or non-object JSON bodies,
bad task and plan query parameters, and invalid claim payloads.

The sweeps enumerate every route registered by the covered API modules, so a
new route that forgets the shared request helpers fails here.
"""
import re

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from httpx import ASGITransport, AsyncClient

from app.routes.api import (
    code_artifacts,
    documents,
    entities,
    files,
    memories,
    plans,
    projects,
    skills,
    tasks,
)

API_MODULES = (
    code_artifacts, documents, entities, files, memories, plans, projects, skills, tasks,
)
IGNORED_METHODS = {"HEAD", "OPTIONS"}
BAD_IDS = [
    "abc",
    "1.5",
    "-1",
    "1_0",
    "99999999999999999999",
    "2147483648",
    "9" * 5000,
]
BAD_BODIES = [
    b"{bad",
    b"",
    b"[1, 2]",
    b"null",
    b'"abc"',
    b"\xff\xfe\xfd",
    b"[" * 100_000,
]
# Raw JSON literals that are not a usable integer (or do not fit the database column)
BAD_INT_JSON = [
    b"null",
    b'"abc"',
    b"[1]",
    b'{"a": 1}',
    b"Infinity",
    b"NaN",
    b"100000000000000000000",
    b"2147483648",
    b"1" + b"0" * 5000,
]
JSON_HEADERS = {"content-type": "application/json"}


def _inventory() -> list[tuple[str, str]]:
    """(method, path template) of every REST route registered by the covered modules."""
    server = FastMCP("route-inventory")
    for module in API_MODULES:
        module.register(server)
    found = set()
    for route in server.http_app().routes:
        path = getattr(route, "path", "")
        if path.startswith("/api/v1/"):
            found.update((method, path) for method in route.methods - IGNORED_METHODS)
    return sorted(found)


ROUTES = _inventory()
ROUTES_WITH_IDS = [(m, p) for m, p in ROUTES if "{" in p]
ROUTES_WITH_BODY = [(m, p) for m, p in ROUTES if m in {"POST", "PUT"}]


def _concrete(path: str, bad_param_index: int | None = None, bad_value: str = "1") -> str:
    """Fill the path template with ``1`` except for one parameter set to ``bad_value``."""
    counter = iter(range(path.count("{")))
    return re.sub(
        r"\{[^}]+\}",
        lambda _: bad_value if next(counter) == bad_param_index else "1",
        path,
    )


@pytest.fixture
async def client(sqlite_app):
    """HTTP client that reports unhandled handler exceptions as 500 responses, like a server."""
    async with Client(sqlite_app):
        transport = ASGITransport(app=sqlite_app.http_app(), raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as http:
            yield http


@pytest.fixture
async def todo_task(client):
    """A todo task in an active plan."""
    project = (await client.post(
        "/api/v1/projects",
        json={"name": "malformed-requests", "description": "p", "project_type": "development"},
    )).json()
    plan = (await client.post(
        "/api/v1/plans", json={"title": "plan", "project_id": project["id"]},
    )).json()
    activated = await client.put(f"/api/v1/plans/{plan['id']}", json={"status": "active"})
    assert activated.status_code == 200
    created = await client.post("/api/v1/tasks", json={"title": "task", "plan_id": plan["id"]})
    assert created.status_code == 201
    return created.json()


def test_inventory_covers_the_rest_api():
    """Guard the sweeps below: they must actually see the routes."""
    assert len(ROUTES_WITH_IDS) > 50
    assert len(ROUTES_WITH_BODY) > 25


class TestPathIds:
    """Path ids that cannot name a resource are 404, not 500."""

    async def test_every_id_route_rejects_bad_ids(self, client):
        failures = []
        for method, template in ROUTES_WITH_IDS:
            for index in range(template.count("{")):
                for bad in BAD_IDS:
                    path = _concrete(template, index, bad)
                    response = await client.request(method, path, json={})
                    if response.status_code != 404 or not response.json()["error"].startswith("Invalid "):
                        failures.append(f"{method} {path[:80]} -> {response.status_code}")
        assert not failures, "\n".join(failures)

    async def test_entity_search_is_not_swallowed_as_an_entity_id(self, client):
        response = await client.get("/api/v1/entities/search")
        assert response.status_code == 404

    async def test_valid_missing_id_is_still_a_plain_not_found(self, client):
        response = await client.get("/api/v1/projects/999999")
        assert response.status_code == 404
        assert response.json() == {"error": "Project not found"}

    async def test_leading_zero_id_is_accepted(self, client):
        project = (await client.post(
            "/api/v1/projects",
            json={"name": "zero", "description": "p", "project_type": "development"},
        )).json()
        response = await client.get(f"/api/v1/projects/00{project['id']}")
        assert response.status_code == 200


class TestJsonBodies:
    """Invalid, empty, non-object and deeply nested JSON bodies are 400, not 500."""

    async def test_every_body_route_rejects_bad_bodies(self, client):
        failures = []
        for method, template in ROUTES_WITH_BODY:
            path = _concrete(template)
            for body in BAD_BODIES:
                response = await client.request(method, path, content=body, headers=JSON_HEADERS)
                if response.status_code != 400 or "error" not in response.json():
                    failures.append(f"{method} {path} body={body[:20]!r} -> {response.status_code}")
        assert not failures, "\n".join(failures)

    async def test_non_object_body_message(self, client):
        response = await client.post("/api/v1/projects", content=b"[1, 2]")
        assert response.status_code == 400
        assert response.json() == {"error": "Request body must be a JSON object"}

    async def test_invalid_json_message(self, client):
        response = await client.post("/api/v1/projects", content=b"{bad")
        assert response.status_code == 400
        assert response.json() == {"error": "Invalid JSON body"}

    async def test_valid_object_body_still_works(self, client):
        response = await client.post(
            "/api/v1/projects",
            json={"name": "ok", "description": "p", "project_type": "development"},
        )
        assert response.status_code == 201


class TestTaskAndPlanQueryParameters:
    async def test_task_list_rejects_bad_parameters(self, client):
        for plan_id in ("abc", "1.5", "99999999999999999999"):
            response = await client.get("/api/v1/tasks", params={"plan_id": plan_id})
            assert response.status_code == 400, plan_id
            assert "plan_id" in response.json()["error"]

    async def test_task_list_rejects_bad_state_and_lists_valid_values(self, client):
        response = await client.get("/api/v1/tasks", params={"plan_id": 1, "state": "bogus"})
        assert response.status_code == 400
        error = response.json()["error"]
        assert "state" in error
        assert "todo" in error
        assert "cancelled" in error

    async def test_task_list_rejects_bad_priority_and_lists_valid_values(self, client):
        response = await client.get("/api/v1/tasks", params={"plan_id": 1, "priority": "bogus"})
        assert response.status_code == 400
        error = response.json()["error"]
        assert "priority" in error
        assert "P0" in error

    async def test_task_list_still_filters(self, client, todo_task):
        response = await client.get(
            "/api/v1/tasks",
            params={"plan_id": todo_task["plan_id"], "state": "todo", "priority": "P2"},
        )
        assert response.status_code == 200
        assert response.json()["total"] == 1

    async def test_plan_list_rejects_bad_project_id(self, client):
        for project_id in ("abc", "99999999999999999999"):
            response = await client.get("/api/v1/plans", params={"project_id": project_id})
            assert response.status_code == 400, project_id
            assert "project_id" in response.json()["error"]


class TestTaskBodies:
    async def test_transition_rejects_bad_version(self, client, todo_task):
        for version in BAD_INT_JSON:
            response = await client.post(
                f"/api/v1/tasks/{todo_task['id']}/transition",
                content=b'{"state": "doing", "version": ' + version + b"}",
            )
            assert response.status_code == 400, (version[:20], response.text[:200])

    async def test_claim_rejects_bad_version(self, client, todo_task):
        for version in BAD_INT_JSON:
            response = await client.post(
                f"/api/v1/tasks/{todo_task['id']}/claim",
                content=b'{"agent_id": "agent-1", "version": ' + version + b"}",
            )
            assert response.status_code == 400, (version[:20], response.text[:200])

    async def test_add_dependency_rejects_bad_task_id(self, client, todo_task):
        for dependency in BAD_INT_JSON:
            response = await client.post(
                f"/api/v1/tasks/{todo_task['id']}/dependencies",
                content=b'{"depends_on_task_id": ' + dependency + b"}",
            )
            assert response.status_code == 400, (dependency[:20], response.text[:200])

    async def test_transition_rejects_non_string_state(self, client, todo_task):
        response = await client.post(
            f"/api/v1/tasks/{todo_task['id']}/transition",
            json={"state": ["doing"], "version": todo_task["version"]},
        )
        assert response.status_code == 400

    async def test_claim_and_transition_still_work(self, client, todo_task):
        claimed = await client.post(
            f"/api/v1/tasks/{todo_task['id']}/claim",
            json={"agent_id": "agent-1", "version": todo_task["version"]},
        )
        assert claimed.status_code == 200
        done = await client.post(
            f"/api/v1/tasks/{todo_task['id']}/transition",
            json={"state": "done", "version": str(claimed.json()["version"])},
        )
        assert done.status_code == 200


class TestClaimAgentId:
    """agent_id must be a real string of 1..TASK_AGENT_MAX_LENGTH characters."""

    async def test_invalid_agent_id_is_rejected_and_task_untouched(self, client, todo_task):
        url = f"/api/v1/tasks/{todo_task['id']}"
        for agent_id in (None, "", "   ", 123, ["a"], {"x": 1}, True, "a" * 201):
            response = await client.post(
                f"{url}/claim", json={"agent_id": agent_id, "version": todo_task["version"]},
            )
            assert response.status_code == 400, (agent_id, response.text[:200])
            assert "error" in response.json()

            task = (await client.get(url)).json()
            assert task["state"] == "todo", agent_id
            assert task["assigned_agent"] is None, agent_id
            assert task["version"] == todo_task["version"], agent_id

    async def test_missing_agent_id_is_rejected(self, client, todo_task):
        response = await client.post(
            f"/api/v1/tasks/{todo_task['id']}/claim", json={"version": todo_task["version"]},
        )
        assert response.status_code == 400

    async def test_max_length_agent_id_is_accepted(self, client, todo_task):
        response = await client.post(
            f"/api/v1/tasks/{todo_task['id']}/claim",
            json={"agent_id": "a" * 200, "version": todo_task["version"]},
        )
        assert response.status_code == 200
        assert response.json()["assigned_agent"] == "a" * 200

    async def test_valid_agent_id_is_trimmed(self, client, todo_task):
        response = await client.post(
            f"/api/v1/tasks/{todo_task['id']}/claim",
            json={"agent_id": " agent-1 ", "version": todo_task["version"]},
        )
        assert response.status_code == 200
        assert response.json()["assigned_agent"] == "agent-1"

    async def test_mcp_claim_task_shares_the_validation(self, mcp_client):
        async def call(tool, args):
            return await mcp_client.call_tool(
                "execute_forgetful_tool", {"tool_name": tool, "arguments": args},
            )

        project = (await call("create_project", {
            "name": "mcp-claim", "description": "p", "project_type": "development",
        })).data["id"]
        plan = (await call("create_plan", {"project_id": project, "title": "p"})).data["id"]
        await call("update_plan", {"plan_id": plan, "status": "active"})
        task = (await call("create_task", {"plan_id": plan, "title": "t"})).data

        for agent_id in ("", "   ", "a" * 201):
            with pytest.raises(ToolError):
                await call("claim_task", {
                    "task_id": task["id"], "agent_id": agent_id, "version": task["version"],
                })

        stored = (await call("get_task", {"task_id": task["id"]})).data
        assert stored["state"] == "todo"
        assert stored["assigned_agent"] is None
