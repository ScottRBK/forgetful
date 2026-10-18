"""SQLite end-to-end tests for task dependency, criteria and plan-state invariants.

Exercises the full stack (MCP tools / REST routes -> TaskService -> SqliteTaskRepository)
on in-memory SQLite, plus file-backed SQLite where real concurrent connections matter.
"""

from dataclasses import dataclass
from uuid import UUID

import pytest
from fastmcp.exceptions import ToolError

from app.config.settings import settings
from app.exceptions import ConflictError
from app.models.plan_models import PlanCreate, PlanStatus, PlanUpdate, TaskCreate
from app.models.project_models import ProjectCreate, ProjectType
from app.models.user_models import UserCreate
from app.repositories.sqlite.plan_repository import SqlitePlanRepository
from app.repositories.sqlite.project_repository import SqliteProjectRepository
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter
from app.repositories.sqlite.task_repository import SqliteTaskRepository
from app.repositories.sqlite.user_repository import SqliteUserRepository
from app.services.plan_service import PlanService
from app.services.task_service import TaskService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@dataclass
class Stack:
    """Real services over a real SQLite database, for tests that need the repository."""

    user_id: UUID
    project_id: int
    plan_id: int
    plan_service: PlanService
    task_service: TaskService
    task_repo: SqliteTaskRepository

    async def new_task(self, title, **extra):
        return await self.task_service.create_task(
            self.user_id, TaskCreate(title=title, plan_id=self.plan_id, **extra),
        )


async def _build_stack(monkeypatch, *, db_path=None):
    monkeypatch.setattr(settings, "DATABASE", "SQLite")
    monkeypatch.setattr(settings, "SQLITE_MEMORY", db_path is None)
    if db_path is not None:
        monkeypatch.setattr(settings, "SQLITE_PATH", str(db_path))
    adapter = SqliteDatabaseAdapter()
    await adapter.init_db()
    user = await SqliteUserRepository(db_adapter=adapter).create_user(
        UserCreate(external_id="integrity-user", name="u", email="u@example.com"),
    )
    project = await SqliteProjectRepository(db_adapter=adapter).create_project(
        user.id, ProjectCreate(name="p", description="d", project_type=ProjectType.DEVELOPMENT),
    )
    plan_service = PlanService(SqlitePlanRepository(db_adapter=adapter), event_bus=None)
    task_repo = SqliteTaskRepository(db_adapter=adapter)
    task_service = TaskService(task_repo, plan_service=plan_service, event_bus=None)
    plan = await plan_service.create_plan(
        user.id, PlanCreate(title="plan", project_id=project.id, goal="g"),
    )
    await plan_service.update_plan(user.id, plan.id, PlanUpdate(status=PlanStatus.ACTIVE))
    stack = Stack(user.id, project.id, plan.id, plan_service, task_service, task_repo)
    return adapter, stack


@pytest.fixture
async def stack(monkeypatch):
    """In-memory SQLite (one shared connection)."""
    adapter, built = await _build_stack(monkeypatch)
    yield built
    await adapter.dispose()


@pytest.fixture
async def file_stack(monkeypatch, tmp_path):
    """File-backed SQLite: every session gets its own connection, like production."""
    adapter, built = await _build_stack(monkeypatch, db_path=tmp_path / "integrity.db")
    yield built
    await adapter.dispose()


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


# ---------------------------------------------------------------------------
# Duplicate dependency edges are a clean conflict
# ---------------------------------------------------------------------------


async def test_rest_duplicate_dependency_is_a_conflict(http_client):
    (plan_id,) = await _rest_project_and_plans(http_client)
    a = await _rest_task(http_client, plan_id, "a")
    b = await _rest_task(http_client, plan_id, "b")
    url = f"/api/v1/tasks/{a['id']}/dependencies"
    first = await http_client.post(url, json={"depends_on_task_id": b["id"]})
    assert first.status_code == 201, first.text

    second = await http_client.post(url, json={"depends_on_task_id": b["id"]})

    assert second.status_code == 409, second.text
    assert "already depends" in second.json()["error"]


async def test_mcp_duplicate_dependency_does_not_leak_database_error(mcp_client):
    project_id = await _mcp_project(mcp_client, "dup-dependency")
    plan_id = await _mcp_active_plan(mcp_client, project_id)
    a = (await _tool(mcp_client, "create_task", plan_id=plan_id, title="a")).data["id"]
    b = (await _tool(mcp_client, "create_task", plan_id=plan_id, title="b")).data["id"]
    await _tool(mcp_client, "add_dependency", task_id=a, depends_on_task_id=b)

    with pytest.raises(ToolError) as excinfo:
        await _tool(mcp_client, "add_dependency", task_id=a, depends_on_task_id=b)

    message = str(excinfo.value)
    assert "already depends" in message
    assert "IntegrityError" not in message and "INSERT INTO" not in message


async def test_repository_maps_unique_violation_to_conflict(stack):
    """Backstop for two writers racing past the service-level duplicate check."""
    a = await stack.new_task("a")
    b = await stack.new_task("b")
    await stack.task_repo.add_dependency(stack.user_id, a.id, b.id)

    with pytest.raises(ConflictError, match="already depends"):
        await stack.task_repo.add_dependency(stack.user_id, a.id, b.id)

    assert await stack.task_repo.get_dependencies(stack.user_id, a.id) == [b.id]
