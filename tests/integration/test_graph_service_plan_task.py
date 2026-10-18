"""Integration tests for GraphService plan/task additions and TaskService.list_tasks_for_user.

Covers:
- GraphService.parse_node_id for plan/task forms
- GraphService._validate_center_node for plan/task with and without services
- TaskService.list_tasks_for_user filter behaviour (None / empty / specific list)
"""

from uuid import uuid4

import pytest

from app.exceptions import NotFoundError
from app.models.plan_models import (
    PlanCreate,
    PlanStatus,
    PlanUpdate,
    TaskCreate,
)
from app.services.graph_service import GraphService

# ---- parse_node_id ----

def test_parse_node_id_plan():
    assert GraphService.parse_node_id("plan_5") == ("plan", 5)


def test_parse_node_id_task():
    assert GraphService.parse_node_id("task_42") == ("task", 42)


def test_parse_node_id_invalid_plan_format():
    with pytest.raises(ValueError):
        GraphService.parse_node_id("plan_abc")


def test_parse_node_id_invalid_prefix():
    with pytest.raises(ValueError):
        GraphService.parse_node_id("plans_5")


# ---- _validate_center_node ----

class _StubMemoryRepo:
    pass


class _StubEntityRepo:
    pass


def _make_graph_service(plan_service=None, task_service=None):
    return GraphService(
        memory_repo=_StubMemoryRepo(),
        entity_repo=_StubEntityRepo(),
        plan_service=plan_service,
        task_service=task_service,
    )


@pytest.mark.asyncio
async def test_validate_center_node_plan_no_service():
    svc = _make_graph_service(plan_service=None)
    with pytest.raises(NotFoundError):
        await svc._validate_center_node(uuid4(), "plan", 1)


@pytest.mark.asyncio
async def test_validate_center_node_task_no_service():
    svc = _make_graph_service(task_service=None)
    with pytest.raises(NotFoundError):
        await svc._validate_center_node(uuid4(), "task", 1)


class _FakePlanService:
    def __init__(self, exists=True):
        self.exists = exists

    async def get_plan(self, user_id, plan_id, track_read=True):
        return object() if self.exists else None

    async def list_plans(self, user_id, **kwargs):
        return []


class _FakeTaskService:
    def __init__(self, exists=True):
        self.exists = exists

    async def get_task(self, user_id, task_id):
        return object() if self.exists else None

    async def list_tasks_for_user(self, user_id, plan_ids=None):
        return []


@pytest.mark.asyncio
async def test_validate_center_node_plan_not_found():
    svc = _make_graph_service(plan_service=_FakePlanService(exists=False))
    with pytest.raises(NotFoundError):
        await svc._validate_center_node(uuid4(), "plan", 99)


@pytest.mark.asyncio
async def test_validate_center_node_task_not_found():
    svc = _make_graph_service(task_service=_FakeTaskService(exists=False))
    with pytest.raises(NotFoundError):
        await svc._validate_center_node(uuid4(), "task", 99)


@pytest.mark.asyncio
async def test_validate_center_node_plan_ok():
    svc = _make_graph_service(plan_service=_FakePlanService(exists=True))
    await svc._validate_center_node(uuid4(), "plan", 1)


@pytest.mark.asyncio
async def test_validate_center_node_task_ok():
    svc = _make_graph_service(task_service=_FakeTaskService(exists=True))
    await svc._validate_center_node(uuid4(), "task", 1)


def test_constructor_backwards_compatible_without_plan_task():
    svc = GraphService(memory_repo=_StubMemoryRepo(), entity_repo=_StubEntityRepo())
    assert svc.plan_service is None
    assert svc.task_service is None


# ---- TaskService.list_tasks_for_user ----

async def _seed_plan_with_tasks(plan_service, task_service, user_id, project_id, n_tasks):
    plan = await plan_service.create_plan(
        user_id=user_id,
        plan_data=PlanCreate(title=f"Plan-{project_id}", project_id=project_id),
    )
    plan = await plan_service.update_plan(
        user_id=user_id, plan_id=plan.id,
        plan_data=PlanUpdate(status=PlanStatus.ACTIVE),
    )
    for i in range(n_tasks):
        await task_service.create_task(
            user_id=user_id,
            task_data=TaskCreate(title=f"task-{i}", plan_id=plan.id),
        )
    return plan.id


@pytest.mark.asyncio
async def test_list_tasks_for_user_none_returns_all(test_task_service):
    task_service, plan_service = test_task_service
    user_id = uuid4()
    p1 = await _seed_plan_with_tasks(plan_service, task_service, user_id, 1, 2)
    p2 = await _seed_plan_with_tasks(plan_service, task_service, user_id, 2, 3)

    tasks = await task_service.list_tasks_for_user(user_id=user_id, plan_ids=None)
    assert len(tasks) == 5
    assert {t.plan_id for t in tasks} == {p1, p2}


@pytest.mark.asyncio
async def test_list_tasks_for_user_empty_list_short_circuits(test_task_service):
    task_service, plan_service = test_task_service
    user_id = uuid4()
    await _seed_plan_with_tasks(plan_service, task_service, user_id, 1, 2)

    tasks = await task_service.list_tasks_for_user(user_id=user_id, plan_ids=[])
    assert tasks == []


@pytest.mark.asyncio
async def test_list_tasks_for_user_specific_plans(test_task_service):
    task_service, plan_service = test_task_service
    user_id = uuid4()
    p1 = await _seed_plan_with_tasks(plan_service, task_service, user_id, 1, 2)
    p2 = await _seed_plan_with_tasks(plan_service, task_service, user_id, 2, 3)
    _p3 = await _seed_plan_with_tasks(plan_service, task_service, user_id, 3, 1)

    tasks = await task_service.list_tasks_for_user(user_id=user_id, plan_ids=[p1, p2])
    assert len(tasks) == 5
    assert all(t.plan_id in {p1, p2} for t in tasks)


@pytest.mark.asyncio
async def test_list_tasks_for_user_unknown_plan_id_silently_ignored(test_task_service):
    task_service, plan_service = test_task_service
    user_id = uuid4()
    p1 = await _seed_plan_with_tasks(plan_service, task_service, user_id, 1, 2)

    tasks = await task_service.list_tasks_for_user(user_id=user_id, plan_ids=[p1, 9999])
    assert len(tasks) == 2
    assert all(t.plan_id == p1 for t in tasks)


@pytest.mark.asyncio
async def test_list_tasks_for_user_tenant_isolation(test_task_service):
    task_service, plan_service = test_task_service
    user_a = uuid4()
    user_b = uuid4()
    p_a = await _seed_plan_with_tasks(plan_service, task_service, user_a, 1, 2)

    # user B asks for user A's plan_id — must see nothing
    tasks = await task_service.list_tasks_for_user(user_id=user_b, plan_ids=[p_a])
    assert tasks == []


@pytest.mark.asyncio
async def test_list_tasks_for_user_zero_tasks(test_task_service):
    task_service, _plan_service = test_task_service
    user_id = uuid4()
    tasks = await task_service.list_tasks_for_user(user_id=user_id, plan_ids=None)
    assert tasks == []


@pytest.mark.asyncio
async def test_list_tasks_for_user_returns_task_summary(test_task_service):
    from app.models.plan_models import TaskSummary
    task_service, plan_service = test_task_service
    user_id = uuid4()
    await _seed_plan_with_tasks(plan_service, task_service, user_id, 1, 1)

    tasks = await task_service.list_tasks_for_user(user_id=user_id)
    assert len(tasks) == 1
    assert isinstance(tasks[0], TaskSummary)
