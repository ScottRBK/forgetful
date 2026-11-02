"""Behavior regressions runnable on the unmodified base without new-module imports.

The baseline lane uses this file only, with the original test tree. A missing
callback must fail an assertion, not collection or constructor/import setup.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.models.plan_models import PlanCreate, PlanUpdate


class RecordingPolicy:
    def __init__(self, reject=False):
        self.before = []
        self.after = []
        self.reject = reject

    def has_before(self, operation):
        return True

    def has_after(self, operation):
        return True

    async def before_save(self, request):
        self.before.append(request.model_copy(deep=True))
        if self.reject:
            raise SyntheticRejection("Synthetic policy rejection")
        return []

    async def after_save(self, request):
        self.after.append(request.model_copy(deep=True))
        return []


class SyntheticRejection(Exception):
    pass


def plan_value(result):
    # The behavior proof supports the old and new internal return contracts.
    return getattr(result, "plan", result)


def install_policy(service, policy):
    service._plan_plugin = policy
    service._project_repo = SimpleNamespace(get_project_by_id=AsyncMock(return_value=object()))


@pytest.mark.asyncio
async def test_create_dispatches_before_and_after(test_plan_service):
    policy = RecordingPolicy()
    install_policy(test_plan_service, policy)
    user = uuid4()
    saved = plan_value(await test_plan_service.create_plan(user, PlanCreate(title="Baseline create", project_id=1)))
    assert len(policy.before) == len(policy.after) == 1
    assert policy.before[0].operation == "create"
    assert policy.before[0].previous is None
    assert policy.after[0].saved.id == saved.id


@pytest.mark.asyncio
async def test_rejected_create_never_persists(test_plan_service):
    install_policy(test_plan_service, RecordingPolicy(reject=True))
    user = uuid4()
    with pytest.raises(SyntheticRejection):
        await test_plan_service.create_plan(user, PlanCreate(title="Rejected", project_id=1))
    assert await test_plan_service.list_plans(user) == []


@pytest.mark.asyncio
async def test_update_dispatches_detached_previous_and_saved(test_plan_service):
    user = uuid4()
    saved = plan_value(await test_plan_service.create_plan(user, PlanCreate(title="Previous", project_id=1)))
    policy = RecordingPolicy()
    install_policy(test_plan_service, policy)
    updated = plan_value(await test_plan_service.update_plan(user, saved.id, PlanUpdate(title="Current")))
    assert len(policy.before) == len(policy.after) == 1
    assert policy.before[0].previous.title == "Previous"
    assert policy.after[0].previous.title == "Previous"
    assert policy.after[0].saved.title == updated.title == "Current"


@pytest.mark.asyncio
async def test_delete_dispatches_confirmed_removal(test_plan_service):
    user = uuid4()
    saved = plan_value(await test_plan_service.create_plan(user, PlanCreate(title="Removed", project_id=1)))
    policy = RecordingPolicy()
    install_policy(test_plan_service, policy)
    result = await test_plan_service.delete_plan(user, saved.id)
    assert getattr(result, "success", result) is True
    assert len(policy.before) == len(policy.after) == 1
    assert policy.after[0].deleted_plan_id == saved.id
    assert not hasattr(policy.after[0], "saved")


@pytest.mark.asyncio
async def test_noop_and_missing_are_positive_controls(test_plan_service):
    user = uuid4()
    saved = plan_value(await test_plan_service.create_plan(user, PlanCreate(title="Unchanged", project_id=1)))
    policy = RecordingPolicy()
    install_policy(test_plan_service, policy)
    unchanged = plan_value(await test_plan_service.update_plan(user, saved.id, PlanUpdate()))
    missing = plan_value(await test_plan_service.update_plan(user, -1, PlanUpdate(title="Missing")))
    deleted = await test_plan_service.delete_plan(user, -1)
    assert unchanged.title == "Unchanged" and missing is None
    assert getattr(deleted, "success", deleted) is False
    assert policy.before == policy.after == []
