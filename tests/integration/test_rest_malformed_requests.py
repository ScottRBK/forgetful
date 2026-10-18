"""Integration tests (stubbed I/O) for claim_task agent_id validation."""
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.config.settings import settings
from app.models.plan_models import (
    PlanCreate,
    PlanStatus,
    PlanUpdate,
    TaskCreate,
    TaskState,
)


async def _todo_task(task_service, plan_service):
    user_id = uuid4()
    plan = await plan_service.create_plan(
        user_id=user_id, plan_data=PlanCreate(title="plan", project_id=1),
    )
    await plan_service.update_plan(
        user_id=user_id, plan_id=plan.id, plan_data=PlanUpdate(status=PlanStatus.ACTIVE),
    )
    task = await task_service.create_task(
        user_id=user_id, task_data=TaskCreate(title="task", plan_id=plan.id),
    )
    return user_id, task


@pytest.mark.parametrize(
    "agent_id",
    ["", "   ", "a" * (settings.TASK_AGENT_MAX_LENGTH + 1), None, 123, ["a"]],
    ids=["empty", "blank", "too-long", "none", "int", "list"],
)
async def test_claim_task_rejects_invalid_agent_id(test_task_service, agent_id):
    task_service, plan_service = test_task_service
    user_id, task = await _todo_task(task_service, plan_service)

    with pytest.raises(ValidationError):
        await task_service.claim_task(
            user_id=user_id, task_id=task.id, agent_id=agent_id, expected_version=task.version,
        )

    stored = await task_service.get_task(user_id=user_id, task_id=task.id)
    assert stored.state == TaskState.TODO
    assert stored.assigned_agent is None
    assert stored.version == task.version


async def test_claim_task_accepts_max_length_agent_id_and_trims_whitespace(test_task_service):
    task_service, plan_service = test_task_service
    user_id, task = await _todo_task(task_service, plan_service)

    claimed = await task_service.claim_task(
        user_id=user_id,
        task_id=task.id,
        agent_id=f"  {'a' * settings.TASK_AGENT_MAX_LENGTH}  ",
        expected_version=task.version,
    )

    assert claimed.state == TaskState.DOING
    assert claimed.assigned_agent == "a" * settings.TASK_AGENT_MAX_LENGTH
