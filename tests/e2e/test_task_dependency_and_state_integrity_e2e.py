"""PostgreSQL end-to-end tests for task dependency, criteria and plan-state invariants.

These cover the guarantees that depend on the PostgreSQL repository SQL (constraint
names, advisory locking, guarded UPDATE statements) and on real concurrent connections.
"""

from dataclasses import dataclass
from uuid import UUID

import pytest
import pytest_asyncio

from app.exceptions import ConflictError
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
