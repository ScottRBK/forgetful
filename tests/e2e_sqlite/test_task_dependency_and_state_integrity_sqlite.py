"""SQLite end-to-end tests for task dependency, criteria and plan-state invariants.

Exercises the full stack (MCP tools / REST routes -> TaskService -> SqliteTaskRepository)
on in-memory SQLite, plus file-backed SQLite where real concurrent connections matter.
"""

import asyncio
from dataclasses import dataclass
from uuid import UUID

import pytest
from fastmcp.exceptions import ToolError

from app.config.settings import settings
from app.events import EventBus
from app.exceptions import (
    ConflictError,
    CyclicDependencyError,
    DependencyNotMetError,
    InvalidStateTransitionError,
    NotFoundError,
)
from app.models.activity_models import ActionType, EntityType
from app.models.plan_models import (
    CriterionCreate,
    CriterionUpdate,
    PlanCreate,
    PlanStatus,
    PlanUpdate,
    TaskCreate,
    TaskState,
)
from app.models.project_models import ProjectCreate, ProjectType
from app.models.user_models import UserCreate
from app.repositories.sqlite.activity_repository import SqliteActivityRepository
from app.repositories.sqlite.plan_repository import SqlitePlanRepository
from app.repositories.sqlite.project_repository import SqliteProjectRepository
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter
from app.repositories.sqlite.task_repository import SqliteTaskRepository
from app.repositories.sqlite.user_repository import SqliteUserRepository
from app.services.activity_service import ActivityService
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
    bus: EventBus | None = None
    activity: ActivityService | None = None

    async def new_task(self, title, **extra):
        return await self.task_service.create_task(
            self.user_id, TaskCreate(title=title, plan_id=self.plan_id, **extra),
        )


async def _build_stack(monkeypatch, *, db_path=None, with_events=False):
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
    bus = activity = None
    if with_events:
        bus = EventBus()
        activity = ActivityService(SqliteActivityRepository(db_adapter=adapter))
        bus.subscribe("*.*", activity.handle_event)  # same wiring as app/bootstrap.py
    plan_service = PlanService(SqlitePlanRepository(db_adapter=adapter), event_bus=bus)
    task_repo = SqliteTaskRepository(db_adapter=adapter)
    task_service = TaskService(task_repo, plan_service=plan_service, event_bus=bus)
    plan = await plan_service.create_plan(
        user.id, PlanCreate(title="plan", project_id=project.id, goal="g"),
    )
    await plan_service.update_plan(user.id, plan.id, PlanUpdate(status=PlanStatus.ACTIVE))
    stack = Stack(user.id, project.id, plan.id, plan_service, task_service, task_repo, bus, activity)
    return adapter, stack


@pytest.fixture
async def stack(monkeypatch):
    """In-memory SQLite (one shared connection)."""
    adapter, built = await _build_stack(monkeypatch)
    yield built
    await adapter.dispose()


@pytest.fixture
async def evented_stack(monkeypatch):
    """In-memory SQLite with the real EventBus persisting activity, as bootstrap wires it."""
    adapter, built = await _build_stack(monkeypatch, with_events=True)
    yield built
    await built.bus.wait_for_pending()
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


# ---------------------------------------------------------------------------
# Cycle check and edge insert are one atomic step
# ---------------------------------------------------------------------------


async def test_repository_rejects_edge_that_closes_a_cycle_and_persists_nothing(stack):
    a = await stack.new_task("a")
    b = await stack.new_task("b")
    c = await stack.new_task("c")
    repo = stack.task_repo
    await repo.add_dependency(stack.user_id, a.id, b.id)
    await repo.add_dependency(stack.user_id, b.id, c.id)

    with pytest.raises(CyclicDependencyError):
        await repo.add_dependency(stack.user_id, c.id, a.id)
    with pytest.raises(CyclicDependencyError):
        await repo.add_dependency(stack.user_id, a.id, a.id)

    assert await repo.get_dependencies(stack.user_id, c.id) == []
    assert await repo.get_dependencies(stack.user_id, a.id) == [b.id]


async def test_service_serialises_concurrent_opposite_dependencies(stack):
    """In-memory SQLite shares one connection, so the service has to order the writers."""
    a = await stack.new_task("A")
    b = await stack.new_task("B")

    results = await asyncio.gather(
        stack.task_service.add_dependency(stack.user_id, a.id, b.id),
        stack.task_service.add_dependency(stack.user_id, b.id, a.id),
        return_exceptions=True,
    )

    failures = [r for r in results if isinstance(r, Exception)]
    assert len(failures) == 1 and isinstance(failures[0], CyclicDependencyError), results
    a_deps = await stack.task_repo.get_dependencies(stack.user_id, a.id)
    b_deps = await stack.task_repo.get_dependencies(stack.user_id, b.id)
    assert len(a_deps) + len(b_deps) == 1
    # The surviving prerequisite can still be worked on (no deadlock).
    prerequisite = b if a_deps else a
    claimed = await stack.task_service.claim_task(
        stack.user_id, prerequisite.id, "agent", expected_version=1,
    )
    assert claimed.state == "doing"


async def test_repository_alone_keeps_concurrent_opposite_edges_acyclic(file_stack):
    """Two real connections race past the service: only the repository can stop the cycle."""
    stack = file_stack
    repo = stack.task_repo
    for round_number in range(8):
        a = await stack.new_task(f"A{round_number}")
        b = await stack.new_task(f"B{round_number}")

        results = await asyncio.gather(
            repo.add_dependency(stack.user_id, a.id, b.id),
            repo.add_dependency(stack.user_id, b.id, a.id),
            return_exceptions=True,
        )

        failures = [r for r in results if isinstance(r, Exception)]
        assert len(failures) == 1 and isinstance(failures[0], CyclicDependencyError), results
        a_deps = await repo.get_dependencies(stack.user_id, a.id)
        b_deps = await repo.get_dependencies(stack.user_id, b.id)
        assert len(a_deps) + len(b_deps) == 1


# ---------------------------------------------------------------------------
# Dependencies are re-validated on DONE and edges respect the task state
# ---------------------------------------------------------------------------


async def _rest_transition(http_client, task_id, state):
    current = (await http_client.get(f"/api/v1/tasks/{task_id}")).json()
    return await http_client.post(
        f"/api/v1/tasks/{task_id}/transition", json={"state": state, "version": current["version"]},
    )


async def test_rest_task_cannot_finish_with_an_unfinished_prerequisite(http_client):
    (plan_id,) = await _rest_project_and_plans(http_client)
    dependent = await _rest_task(http_client, plan_id, "dependent")
    prerequisite = await _rest_task(http_client, plan_id, "prerequisite")
    assert (await _rest_transition(http_client, dependent["id"], "doing")).status_code == 200
    added = await http_client.post(
        f"/api/v1/tasks/{dependent['id']}/dependencies",
        json={"depends_on_task_id": prerequisite["id"]},
    )
    assert added.status_code == 201, added.text

    blocked = await _rest_transition(http_client, dependent["id"], "done")

    assert blocked.status_code == 422, blocked.text
    assert "not done" in blocked.json()["error"]
    assert (await http_client.get(f"/api/v1/tasks/{dependent['id']}")).json()["state"] == "doing"


async def test_rest_done_task_cannot_gain_a_dependency(http_client):
    (plan_id,) = await _rest_project_and_plans(http_client)
    finished = await _rest_task(http_client, plan_id, "finished")
    other = await _rest_task(http_client, plan_id, "other")
    assert (await _rest_transition(http_client, finished["id"], "doing")).status_code == 200
    assert (await _rest_transition(http_client, finished["id"], "done")).status_code == 200

    r = await http_client.post(
        f"/api/v1/tasks/{finished['id']}/dependencies", json={"depends_on_task_id": other["id"]},
    )

    assert r.status_code == 422, r.text
    listed = (await http_client.get(f"/api/v1/tasks?plan_id={plan_id}")).json()["tasks"]
    assert next(t for t in listed if t["id"] == finished["id"])["blocked"] is False


# ---------------------------------------------------------------------------
# State transitions re-check their preconditions inside the atomic UPDATE
# ---------------------------------------------------------------------------


def _run_after(service, method_name, action):
    """Make `action` run right after the service validated, i.e. in the check-then-act window."""
    original = getattr(service, method_name)

    async def wrapper(*args, **kwargs):
        result = await original(*args, **kwargs)
        await action()
        return result

    setattr(service, method_name, wrapper)


async def test_done_is_refused_when_a_criterion_lands_after_validation(stack):
    task = await stack.new_task("t", criteria=[CriterionCreate(description="c1")])
    criterion = task.criteria[0]
    await stack.task_service.update_criterion(
        stack.user_id, criterion.id, CriterionUpdate(met=True),
    )
    doing = await stack.task_service.claim_task(stack.user_id, task.id, "agent", expected_version=1)

    async def another_agent_adds_a_criterion():
        await stack.task_repo.create_criterion(
            stack.user_id, task.id, CriterionCreate(description="added in the race window"),
        )

    _run_after(stack.task_service, "_validate_all_criteria_met", another_agent_adds_a_criterion)

    with pytest.raises(InvalidStateTransitionError, match="criteria not met"):
        await stack.task_service.transition_task(
            stack.user_id, task.id, TaskState.DONE, expected_version=doing.version,
        )

    current = await stack.task_service.get_task(stack.user_id, task.id)
    assert (current.state, current.version) == (TaskState.DOING, doing.version)


async def test_done_is_refused_when_a_criterion_is_unmet_after_validation(stack):
    task = await stack.new_task("t", criteria=[CriterionCreate(description="c1")])
    await stack.task_service.update_criterion(
        stack.user_id, task.criteria[0].id, CriterionUpdate(met=True),
    )
    doing = await stack.task_service.claim_task(stack.user_id, task.id, "agent", expected_version=1)

    async def another_agent_unmeets_the_criterion():
        await stack.task_repo.update_criterion(
            stack.user_id, task.criteria[0].id, CriterionUpdate(met=False),
        )

    _run_after(stack.task_service, "_validate_all_criteria_met", another_agent_unmeets_the_criterion)

    with pytest.raises(InvalidStateTransitionError):
        await stack.task_service.transition_task(
            stack.user_id, task.id, TaskState.DONE, expected_version=doing.version,
        )

    assert (await stack.task_service.get_task(stack.user_id, task.id)).state == TaskState.DOING


async def test_claim_is_refused_when_a_dependency_lands_after_validation(stack):
    prerequisite = await stack.new_task("prerequisite")
    task = await stack.new_task("t")

    async def another_agent_adds_a_dependency():
        await stack.task_repo.add_dependency(stack.user_id, task.id, prerequisite.id)

    _run_after(stack.task_service, "_validate_dependencies_met", another_agent_adds_a_dependency)

    with pytest.raises(DependencyNotMetError, match="not done"):
        await stack.task_service.claim_task(stack.user_id, task.id, "agent", expected_version=1)

    current = await stack.task_service.get_task(stack.user_id, task.id)
    assert (current.state, current.assigned_agent, current.version) == (TaskState.TODO, None, 1)


async def test_repository_transition_guards_and_error_precedence(stack):
    repo = stack.task_repo
    prerequisite = await stack.new_task("prerequisite")
    task = await stack.new_task("t", criteria=[CriterionCreate(description="c1")], dependency_ids=[prerequisite.id])

    with pytest.raises(DependencyNotMetError):
        await repo.transition_task_state(stack.user_id, task.id, TaskState.DOING, expected_version=1)
    with pytest.raises(ConflictError, match="Version conflict"):
        await repo.transition_task_state(stack.user_id, task.id, TaskState.DOING, expected_version=7)
    with pytest.raises(NotFoundError):
        await repo.transition_task_state(stack.user_id, 9999, TaskState.DOING, expected_version=1)
    # Moves that carry no precondition are unaffected.
    waiting = await repo.transition_task_state(stack.user_id, task.id, TaskState.WAITING, expected_version=1)
    assert waiting.state == TaskState.WAITING

    done_prerequisite = await repo.transition_task_state(
        stack.user_id, prerequisite.id, TaskState.DONE, expected_version=1,
    )
    assert done_prerequisite.state == TaskState.DONE  # no criteria, no dependencies: allowed
    doing = await repo.transition_task_state(
        stack.user_id, task.id, TaskState.DOING, expected_version=waiting.version,
    )
    with pytest.raises(InvalidStateTransitionError, match="criteria not met"):
        await repo.transition_task_state(
            stack.user_id, task.id, TaskState.DONE, expected_version=doing.version,
        )
    await repo.update_criterion(stack.user_id, task.criteria[0].id, CriterionUpdate(met=True))
    finished = await repo.transition_task_state(
        stack.user_id, task.id, TaskState.DONE, expected_version=doing.version,
    )
    assert finished.state == TaskState.DONE


# ---------------------------------------------------------------------------
# Criteria of a completed task are frozen, like add_criterion already enforces
# ---------------------------------------------------------------------------


async def test_unmeeting_a_criterion_of_a_done_task_is_rejected_over_mcp(mcp_client):
    project_id = await _mcp_project(mcp_client, "frozen-criteria")
    plan_id = await _mcp_active_plan(mcp_client, project_id)
    task = (await _tool(mcp_client, "create_task", plan_id=plan_id, title="t")).data
    criterion = (await _tool(
        mcp_client, "add_criterion", task_id=task["id"], description="must hold",
    )).data
    await _tool(mcp_client, "verify_criterion", criterion_id=criterion["id"], met=True)
    claimed = (await _tool(
        mcp_client, "claim_task", task_id=task["id"], agent_id="agent-1", version=task["version"],
    )).data
    await _tool(mcp_client, "transition_task", task_id=task["id"], state="done", version=claimed["version"])

    with pytest.raises(ToolError, match="completed task"):
        await _tool(mcp_client, "verify_criterion", criterion_id=criterion["id"], met=False)

    final = (await _tool(mcp_client, "get_task", task_id=task["id"])).data
    assert final["state"] == "done"
    assert [c["met"] for c in final["criteria"]] == [True]


async def test_rest_criterion_changes_on_a_done_task_are_unprocessable(http_client):
    (plan_id,) = await _rest_project_and_plans(http_client)
    task = await _rest_task(http_client, plan_id, "t")
    added = await http_client.post(f"/api/v1/tasks/{task['id']}/criteria", json={"description": "holds"})
    criterion_id = added.json()["id"]
    assert (await http_client.put(f"/api/v1/criteria/{criterion_id}", json={"met": True})).status_code == 200
    assert (await _rest_transition(http_client, task["id"], "doing")).status_code == 200
    assert (await _rest_transition(http_client, task["id"], "done")).status_code == 200

    unmet = await http_client.put(f"/api/v1/criteria/{criterion_id}", json={"met": False})
    deleted = await http_client.delete(f"/api/v1/criteria/{criterion_id}")

    assert unmet.status_code == 422, unmet.text
    assert deleted.status_code == 422, deleted.text
    final = (await http_client.get(f"/api/v1/tasks/{task['id']}")).json()
    assert [c["met"] for c in final["criteria"]] == [True]


# ---------------------------------------------------------------------------
# Criterion and dependency mutations are announced as task updates
# ---------------------------------------------------------------------------


async def test_criterion_and_dependency_mutations_reach_the_activity_log(evented_stack):
    stack = evented_stack
    service = stack.task_service
    task = await stack.new_task("t")
    prerequisite = await stack.new_task("prerequisite")
    await stack.bus.wait_for_pending()
    baseline = (await stack.activity.get_activity(user_id=stack.user_id, limit=100)).events

    criterion = await service.add_criterion(stack.user_id, task.id, CriterionCreate(description="holds"))
    await service.update_criterion(stack.user_id, criterion.id, CriterionUpdate(met=True))
    await service.add_dependency(stack.user_id, task.id, prerequisite.id)
    await service.remove_dependency(stack.user_id, task.id, prerequisite.id)
    await service.delete_criterion(stack.user_id, criterion.id)
    await stack.bus.wait_for_pending()

    events = (await stack.activity.get_activity(user_id=stack.user_id, limit=100)).events
    new_events = [e for e in events if e.id not in {b.id for b in baseline}]
    assert len(new_events) == 5
    assert {(e.entity_type, e.action, e.entity_id) for e in new_events} == {
        (EntityType.TASK, ActionType.UPDATED, task.id),
    }
    assert sorted(next(iter(e.changes)) for e in new_events) == ["criterion"] * 3 + ["dependency"] * 2
    added = next(
        e for e in new_events
        if "criterion" in e.changes and e.changes["criterion"]["old"] is None
    )
    assert added.changes["criterion"]["new"]["description"] == "holds"
    assert [c["description"] for c in added.snapshot["criteria"]] == ["holds"]
    linked = next(
        e for e in new_events
        if "dependency" in e.changes and e.changes["dependency"]["old"] is None
    )
    assert linked.snapshot["dependency_ids"] == [prerequisite.id]


# ---------------------------------------------------------------------------
# Plan status follows task reopening and gates task work
# ---------------------------------------------------------------------------


async def test_rest_reopening_a_task_reactivates_the_completed_plan(http_client):
    (plan_id,) = await _rest_project_and_plans(http_client)
    first = await _rest_task(http_client, plan_id, "first")
    second = await _rest_task(http_client, plan_id, "second")
    for task in (first, second):
        assert (await _rest_transition(http_client, task["id"], "doing")).status_code == 200
        assert (await _rest_transition(http_client, task["id"], "done")).status_code == 200
    assert (await http_client.get(f"/api/v1/plans/{plan_id}")).json()["status"] == "completed"

    reopened = await _rest_transition(http_client, first["id"], "todo")

    assert reopened.status_code == 200, reopened.text
    assert (await http_client.get(f"/api/v1/plans/{plan_id}")).json()["status"] == "active"
    claim = await http_client.post(
        f"/api/v1/tasks/{first['id']}/claim",
        json={"agent_id": "agent", "version": reopened.json()["version"]},
    )
    assert claim.status_code == 200, claim.text
    assert claim.json()["state"] == "doing"


async def test_rest_work_on_a_manually_completed_plan_is_unprocessable(http_client):
    (plan_id,) = await _rest_project_and_plans(http_client)
    task = await _rest_task(http_client, plan_id, "unfinished")
    done = await http_client.put(f"/api/v1/plans/{plan_id}", json={"status": "completed"})
    assert done.status_code == 200, done.text

    claim = await http_client.post(
        f"/api/v1/tasks/{task['id']}/claim", json={"agent_id": "agent", "version": task["version"]},
    )
    transition = await _rest_transition(http_client, task["id"], "doing")
    create = await http_client.post("/api/v1/tasks", json={"plan_id": plan_id, "title": "new"})

    assert (claim.status_code, transition.status_code, create.status_code) == (422, 422, 422)
    assert (await http_client.get(f"/api/v1/tasks/{task['id']}")).json()["state"] == "todo"
