"""PostgreSQL end-to-end tests for task dependency, criteria and plan-state invariants.

These cover the guarantees that depend on the PostgreSQL repository SQL (constraint
names, advisory locking, guarded UPDATE statements) and on real concurrent connections.
"""

import asyncio
from dataclasses import dataclass
from uuid import UUID

import pytest
import pytest_asyncio

from app.exceptions import (
    ConflictError,
    CyclicDependencyError,
    DependencyNotMetError,
    InvalidStateTransitionError,
    NotFoundError,
)
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

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.asyncio(loop_scope="session"),
]


@dataclass
class Stack:
    """Real services over the PostgreSQL repositories, for repository-level assertions."""

    user_id: UUID
    plan_id: int
    plan_service: object
    task_service: object

    @property
    def task_repo(self):
        return self.task_service.task_repo

    async def new_task(self, title, **extra):
        return await self.task_service.create_task(
            self.user_id, TaskCreate(title=title, plan_id=self.plan_id, **extra),
        )


@pytest_asyncio.fixture(loop_scope="session")
async def stack(postgres_app, mcp_client):
    """mcp_client is requested so the app lifespan has attached the services."""
    user = await postgres_app.user_service.get_or_create_user(
        UserCreate(external_id="integrity-e2e", name="u", email="u@example.com"),
    )
    project = await postgres_app.project_service.create_project(
        user.id, ProjectCreate(name="p", description="d", project_type=ProjectType.DEVELOPMENT),
    )
    plan = await postgres_app.plan_service.create_plan(
        user.id, PlanCreate(title="plan", project_id=project.id, goal="g"),
    )
    await postgres_app.plan_service.update_plan(user.id, plan.id, PlanUpdate(status=PlanStatus.ACTIVE))
    return Stack(user.id, plan.id, postgres_app.plan_service, postgres_app.task_service)


async def test_repository_maps_unique_violation_to_conflict(stack):
    a = await stack.new_task("a")
    b = await stack.new_task("b")
    await stack.task_repo.add_dependency(stack.user_id, a.id, b.id)

    with pytest.raises(ConflictError, match="already depends"):
        await stack.task_repo.add_dependency(stack.user_id, a.id, b.id)

    assert await stack.task_repo.get_dependencies(stack.user_id, a.id) == [b.id]


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


async def test_concurrent_opposite_edges_never_form_a_cycle_across_connections(stack):
    """Bypasses the service lock: the advisory lock + in-transaction re-check must hold."""
    repo = stack.task_repo
    for round_number in range(10):
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


async def test_concurrent_edges_around_a_longer_cycle_leave_it_acyclic(stack):
    """A->B, B->C are stored; C->A and a second writer racing on the same ring."""
    a = await stack.new_task("a")
    b = await stack.new_task("b")
    c = await stack.new_task("c")
    repo = stack.task_repo
    results = await asyncio.gather(
        repo.add_dependency(stack.user_id, a.id, b.id),
        repo.add_dependency(stack.user_id, b.id, c.id),
        repo.add_dependency(stack.user_id, c.id, a.id),
        return_exceptions=True,
    )

    failures = [r for r in results if isinstance(r, Exception)]
    assert len(failures) == 1 and isinstance(failures[0], CyclicDependencyError), results


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
