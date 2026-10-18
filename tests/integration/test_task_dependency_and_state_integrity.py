"""Integration tests for task dependency, criteria and plan-state invariants.

Drives TaskService against the in-memory stub repositories. Every test asserts the
invariant that must hold regardless of the storage backend; backend-specific atomicity
(SQL guards, locking) is covered by the SQLite and PostgreSQL end-to-end suites.
"""

import asyncio
from uuid import uuid4

import pytest

from app.exceptions import ConflictError, CyclicDependencyError, NotFoundError
from app.models.plan_models import (
    CriterionCreate,
    PlanCreate,
    PlanStatus,
    PlanUpdate,
    TaskCreate,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _active_plan(plan_service, user_id, title="Plan"):
    plan = await plan_service.create_plan(
        user_id=user_id,
        plan_data=PlanCreate(title=title, project_id=1, goal="test"),
    )
    return await plan_service.update_plan(
        user_id=user_id, plan_id=plan.id, plan_data=PlanUpdate(status=PlanStatus.ACTIVE),
    )


async def _task(task_service, user_id, plan_id, title="task", **extra):
    return await task_service.create_task(
        user_id=user_id, task_data=TaskCreate(title=title, plan_id=plan_id, **extra),
    )


# ---------------------------------------------------------------------------
# create_task is all-or-nothing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_task_with_cross_plan_dependency_persists_nothing(test_task_service):
    task_service, plan_service = test_task_service
    user_id = uuid4()
    plan_a = await _active_plan(plan_service, user_id, "A")
    plan_b = await _active_plan(plan_service, user_id, "B")
    foreign = await _task(task_service, user_id, plan_b.id, "foreign")

    with pytest.raises(ValueError, match="same plan"):
        await _task(
            task_service, user_id, plan_a.id, "X",
            dependency_ids=[foreign.id],
            criteria=[CriterionCreate(description="c")],
        )

    assert await task_service.list_tasks(user_id=user_id, plan_id=plan_a.id) == []
    assert task_service.task_repo._criteria.get(user_id, {}) == {}


@pytest.mark.asyncio
async def test_create_task_with_unknown_dependency_persists_nothing(test_task_service):
    task_service, plan_service = test_task_service
    user_id = uuid4()
    plan = await _active_plan(plan_service, user_id)

    with pytest.raises(NotFoundError):
        await _task(task_service, user_id, plan.id, "X", dependency_ids=[999])

    assert await task_service.list_tasks(user_id=user_id, plan_id=plan.id) == []


@pytest.mark.asyncio
async def test_create_task_validates_every_dependency_before_persisting(test_task_service):
    """A valid first dependency must not leave an edge or task behind when a later one fails."""
    task_service, plan_service = test_task_service
    user_id = uuid4()
    plan = await _active_plan(plan_service, user_id)
    good = await _task(task_service, user_id, plan.id, "good")

    with pytest.raises(NotFoundError):
        await _task(task_service, user_id, plan.id, "X", dependency_ids=[good.id, 999])

    assert [t.title for t in await task_service.list_tasks(user_id=user_id, plan_id=plan.id)] == ["good"]
    assert task_service.task_repo._dependencies.get(user_id, {}) == {}


@pytest.mark.asyncio
async def test_create_task_rejects_duplicate_dependency_ids_without_persisting(test_task_service):
    task_service, plan_service = test_task_service
    user_id = uuid4()
    plan = await _active_plan(plan_service, user_id)
    prereq = await _task(task_service, user_id, plan.id, "prereq")

    with pytest.raises(ValueError, match="more than once"):
        await _task(task_service, user_id, plan.id, "X", dependency_ids=[prereq.id, prereq.id])

    assert [t.title for t in await task_service.list_tasks(user_id=user_id, plan_id=plan.id)] == ["prereq"]


@pytest.mark.asyncio
async def test_create_task_rolls_back_when_a_later_step_fails(test_task_service):
    """An unexpected repository failure after the task row exists must not leave an orphan."""
    task_service, plan_service = test_task_service
    user_id = uuid4()
    plan = await _active_plan(plan_service, user_id)
    prereq = await _task(task_service, user_id, plan.id, "prereq")

    async def boom(*args, **kwargs):
        raise RuntimeError("database went away")

    task_service.task_repo.add_dependency = boom

    with pytest.raises(RuntimeError, match="database went away"):
        await _task(
            task_service, user_id, plan.id, "X",
            dependency_ids=[prereq.id],
            criteria=[CriterionCreate(description="c")],
        )

    assert [t.title for t in await task_service.list_tasks(user_id=user_id, plan_id=plan.id)] == ["prereq"]
    assert task_service.task_repo._criteria.get(user_id, {}) == {}


# ---------------------------------------------------------------------------
# Duplicate dependency edges are a clean conflict
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_dependency_twice_is_a_conflict(test_task_service):
    task_service, plan_service = test_task_service
    user_id = uuid4()
    plan = await _active_plan(plan_service, user_id)
    a = await _task(task_service, user_id, plan.id, "a")
    b = await _task(task_service, user_id, plan.id, "b")
    await task_service.add_dependency(user_id=user_id, task_id=a.id, depends_on_task_id=b.id)

    with pytest.raises(ConflictError, match="already depends"):
        await task_service.add_dependency(user_id=user_id, task_id=a.id, depends_on_task_id=b.id)

    assert (await task_service.get_task(user_id=user_id, task_id=a.id)).dependency_ids == [b.id]


# ---------------------------------------------------------------------------
# Cycle check and edge insert are one atomic step
# ---------------------------------------------------------------------------


def _yield_before(method):
    """Wrap a repository coroutine so concurrent callers interleave at every await."""
    async def wrapper(*args, **kwargs):
        await asyncio.sleep(0)
        return await method(*args, **kwargs)

    return wrapper


@pytest.mark.asyncio
async def test_concurrent_opposite_dependencies_cannot_form_a_cycle(test_task_service):
    task_service, plan_service = test_task_service
    user_id = uuid4()
    plan = await _active_plan(plan_service, user_id)
    a = await _task(task_service, user_id, plan.id, "a")
    b = await _task(task_service, user_id, plan.id, "b")
    repo = task_service.task_repo
    for name in ("get_task_by_id", "get_dependencies", "add_dependency"):
        setattr(repo, name, _yield_before(getattr(repo, name)))

    results = await asyncio.gather(
        task_service.add_dependency(user_id=user_id, task_id=a.id, depends_on_task_id=b.id),
        task_service.add_dependency(user_id=user_id, task_id=b.id, depends_on_task_id=a.id),
        return_exceptions=True,
    )

    failures = [r for r in results if isinstance(r, Exception)]
    assert len(failures) == 1 and isinstance(failures[0], CyclicDependencyError), results
    a_deps = await repo.get_dependencies(user_id, a.id)
    b_deps = await repo.get_dependencies(user_id, b.id)
    assert len(a_deps) + len(b_deps) == 1
