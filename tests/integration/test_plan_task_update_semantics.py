"""Integration tests for plan and task update semantics with in-memory stubs.

An explicit null in a PATCH-style update means "unchanged", and updating a plan or task
that does not exist (or belongs to another user) raises NotFoundError instead of returning None.
"""

from uuid import uuid4

import pytest

from app.exceptions import NotFoundError
from app.models.plan_models import (
    PlanCreate,
    PlanStatus,
    PlanUpdate,
    TaskCreate,
    TaskPriority,
    TaskUpdate,
)

MISSING_ID = 999999


async def _create_active_plan(plan_service, user_id):
    plan = await plan_service.create_plan(
        user_id=user_id,
        plan_data=PlanCreate(
            title="Original", project_id=1, goal="Original goal", context="Original context",
            source_repo="owner/repo",
        ),
    )
    return await plan_service.update_plan(
        user_id=user_id, plan_id=plan.id, plan_data=PlanUpdate(status=PlanStatus.ACTIVE),
    )


# ---- Explicit nulls are dropped by the update models ----

def test_plan_update_drops_explicit_nulls():
    update = PlanUpdate(title=None, goal=None, status=None, source_repo=None, external_ref=None)

    assert update.model_fields_set == set()
    assert update.model_dump(exclude_unset=True) == {}


def test_plan_update_keeps_real_values_next_to_nulls():
    update = PlanUpdate.model_validate({"title": "Renamed", "goal": None})

    assert update.model_dump(exclude_unset=True) == {"title": "Renamed"}


def test_task_update_drops_explicit_nulls():
    update = TaskUpdate(title=None, description=None, priority=None, source_repo=None)

    assert update.model_fields_set == set()
    assert update.model_dump(exclude_unset=True) == {}


def test_task_update_keeps_real_values_next_to_nulls():
    update = TaskUpdate.model_validate({"priority": "P0", "description": None})

    assert update.model_dump(exclude_unset=True) == {"priority": TaskPriority.P0}


@pytest.mark.asyncio
async def test_update_plan_with_only_nulls_changes_nothing(test_plan_service):
    user_id = uuid4()
    plan = await test_plan_service.create_plan(
        user_id=user_id,
        plan_data=PlanCreate(title="Original", project_id=1, goal="Original goal"),
    )

    updated = await test_plan_service.update_plan(
        user_id=user_id,
        plan_id=plan.id,
        plan_data=PlanUpdate.model_validate({"title": None, "goal": None, "status": None}),
    )

    assert updated.title == "Original"
    assert updated.goal == "Original goal"
    assert updated.status == PlanStatus.DRAFT


@pytest.mark.asyncio
async def test_update_task_with_only_nulls_changes_nothing(test_task_service):
    task_service, plan_service = test_task_service
    user_id = uuid4()
    plan = await _create_active_plan(plan_service, user_id)
    task = await task_service.create_task(
        user_id=user_id,
        task_data=TaskCreate(
            title="Original", description="Original description", plan_id=plan.id,
            priority=TaskPriority.P1,
        ),
    )

    updated = await task_service.update_task(
        user_id=user_id,
        task_id=task.id,
        task_data=TaskUpdate.model_validate({"title": None, "description": None, "priority": None}),
    )

    assert updated.title == "Original"
    assert updated.description == "Original description"
    assert updated.priority == TaskPriority.P1


# ---- Updating a missing plan or task is a not-found error ----

@pytest.mark.asyncio
async def test_update_plan_missing_raises_not_found(test_plan_service):
    with pytest.raises(NotFoundError, match="Plan with id 999999 not found"):
        await test_plan_service.update_plan(
            user_id=uuid4(), plan_id=MISSING_ID, plan_data=PlanUpdate(title="x"),
        )


@pytest.mark.asyncio
async def test_update_plan_of_another_user_raises_not_found(test_plan_service):
    owner_id = uuid4()
    plan = await test_plan_service.create_plan(
        user_id=owner_id, plan_data=PlanCreate(title="Private", project_id=1),
    )

    with pytest.raises(NotFoundError):
        await test_plan_service.update_plan(
            user_id=uuid4(), plan_id=plan.id, plan_data=PlanUpdate(title="Hijacked"),
        )

    assert (await test_plan_service.get_plan(user_id=owner_id, plan_id=plan.id)).title == "Private"


@pytest.mark.asyncio
async def test_update_task_missing_raises_not_found(test_task_service):
    task_service, _ = test_task_service

    with pytest.raises(NotFoundError, match="Task with id 999999 not found"):
        await task_service.update_task(
            user_id=uuid4(), task_id=MISSING_ID, task_data=TaskUpdate(title="x"),
        )


@pytest.mark.asyncio
async def test_update_task_of_another_user_raises_not_found(test_task_service):
    task_service, plan_service = test_task_service
    owner_id = uuid4()
    plan = await _create_active_plan(plan_service, owner_id)
    task = await task_service.create_task(
        user_id=owner_id, task_data=TaskCreate(title="Private", plan_id=plan.id),
    )

    with pytest.raises(NotFoundError):
        await task_service.update_task(
            user_id=uuid4(), task_id=task.id, task_data=TaskUpdate(title="Hijacked"),
        )

    assert (await task_service.get_task(user_id=owner_id, task_id=task.id)).title == "Private"
