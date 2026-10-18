"""PostgreSQL end-to-end tests for task dependency, criteria and plan-state invariants.

These cover the guarantees that depend on the PostgreSQL repository SQL (constraint
names, advisory locking, guarded UPDATE statements) and on real concurrent connections.
"""

import asyncio
from dataclasses import dataclass
from uuid import UUID

import pytest
import pytest_asyncio

from app.exceptions import ConflictError, CyclicDependencyError
from app.models.plan_models import PlanCreate, PlanStatus, PlanUpdate, TaskCreate
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
