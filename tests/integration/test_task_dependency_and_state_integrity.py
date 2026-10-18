"""Integration tests for task dependency, criteria and plan-state invariants.

Drives TaskService against the in-memory stub repositories. Every test asserts the
invariant that must hold regardless of the storage backend; backend-specific atomicity
(SQL guards, locking) is covered by the SQLite and PostgreSQL end-to-end suites.
"""

import asyncio
from uuid import uuid4

import pytest

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
from app.services.task_service import TaskService
from tests.integration.conftest import CollectingEventBus

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


async def _move(task_service, user_id, task, state):
    """Transition using the task's current version and return the refreshed task."""
    current = await task_service.get_task(user_id=user_id, task_id=task.id)
    return await task_service.transition_task(
        user_id=user_id, task_id=task.id, new_state=state, expected_version=current.version,
    )


async def _finish(task_service, user_id, task):
    await _move(task_service, user_id, task, TaskState.DOING)
    return await _move(task_service, user_id, task, TaskState.DONE)


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


class _NoCountList(list):
    """List that fails if a caller uses the quadratic list.count() on it."""

    def count(self, value):  # noqa: ARG002
        raise AssertionError("duplicate detection must be linear, not a count() per item")


@pytest.mark.asyncio
async def test_duplicate_dependency_check_is_linear_and_reports_sorted_ids(test_task_service):
    task_service, plan_service = test_task_service
    user_id = uuid4()
    plan = await _active_plan(plan_service, user_id)
    # model_construct skips validation so the service receives the instrumented list as is.
    task_data = TaskCreate.model_construct(
        title="X", plan_id=plan.id, dependency_ids=_NoCountList([9, 3, 9, 4, 3, 9]),
    )

    with pytest.raises(ValueError, match=r"more than once: \[3, 9\]"):
        await task_service.create_task(user_id=user_id, task_data=task_data)

    assert await task_service.list_tasks(user_id=user_id, plan_id=plan.id) == []


@pytest.mark.asyncio
async def test_create_task_rolls_back_when_cancelled_mid_create(test_task_service):
    """A cancelled request (client disconnect) must not leave the half-built task behind."""
    task_service, plan_service = test_task_service
    user_id = uuid4()
    plan = await _active_plan(plan_service, user_id)

    async def cancelled(*args, **kwargs):
        raise asyncio.CancelledError

    task_service.task_repo.create_criterion = cancelled

    with pytest.raises(asyncio.CancelledError):
        await _task(
            task_service, user_id, plan.id, "X", criteria=[CriterionCreate(description="c")],
        )

    assert await task_service.list_tasks(user_id=user_id, plan_id=plan.id) == []


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


# ---------------------------------------------------------------------------
# Dependencies are re-validated on DONE and edges respect the task state
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_doing_task_cannot_finish_while_a_late_prerequisite_is_unfinished(test_task_service):
    task_service, plan_service = test_task_service
    user_id = uuid4()
    plan = await _active_plan(plan_service, user_id)
    dependent = await _task(task_service, user_id, plan.id, "dependent")
    prerequisite = await _task(task_service, user_id, plan.id, "prerequisite")
    await _move(task_service, user_id, dependent, TaskState.DOING)
    await task_service.add_dependency(
        user_id=user_id, task_id=dependent.id, depends_on_task_id=prerequisite.id,
    )

    with pytest.raises(DependencyNotMetError):
        await _move(task_service, user_id, dependent, TaskState.DONE)

    await _finish(task_service, user_id, prerequisite)
    done = await _move(task_service, user_id, dependent, TaskState.DONE)
    assert done.state == TaskState.DONE


@pytest.mark.asyncio
async def test_dependent_cannot_finish_after_its_prerequisite_is_reopened(test_task_service):
    task_service, plan_service = test_task_service
    user_id = uuid4()
    plan = await _active_plan(plan_service, user_id)
    prerequisite = await _task(task_service, user_id, plan.id, "A")
    dependent = await _task(task_service, user_id, plan.id, "B", dependency_ids=[prerequisite.id])
    await _finish(task_service, user_id, prerequisite)
    await _move(task_service, user_id, dependent, TaskState.DOING)
    await _move(task_service, user_id, prerequisite, TaskState.TODO)

    with pytest.raises(DependencyNotMetError, match="not done"):
        await _move(task_service, user_id, dependent, TaskState.DONE)

    assert (await task_service.get_task(user_id=user_id, task_id=dependent.id)).state == TaskState.DOING


@pytest.mark.asyncio
async def test_done_task_cannot_gain_a_dependency(test_task_service):
    task_service, plan_service = test_task_service
    user_id = uuid4()
    plan = await _active_plan(plan_service, user_id)
    finished = await _task(task_service, user_id, plan.id, "finished")
    other = await _task(task_service, user_id, plan.id, "other")
    await _finish(task_service, user_id, finished)

    with pytest.raises(InvalidStateTransitionError, match="completed task"):
        await task_service.add_dependency(
            user_id=user_id, task_id=finished.id, depends_on_task_id=other.id,
        )

    assert (await task_service.get_task(user_id=user_id, task_id=finished.id)).dependency_ids == []


# ---------------------------------------------------------------------------
# Criteria of a completed task are frozen, like add_criterion already enforces
# ---------------------------------------------------------------------------


async def _done_task_with_met_criterion(task_service, user_id, plan_id):
    task = await _task(task_service, user_id, plan_id, "t", criteria=[CriterionCreate(description="holds")])
    criterion = task.criteria[0]
    await task_service.update_criterion(user_id, criterion.id, CriterionUpdate(met=True))
    await _finish(task_service, user_id, task)
    return task, criterion


@pytest.mark.asyncio
async def test_criterion_of_a_done_task_cannot_be_unmet_or_edited(test_task_service):
    task_service, plan_service = test_task_service
    user_id = uuid4()
    plan = await _active_plan(plan_service, user_id)
    task, criterion = await _done_task_with_met_criterion(task_service, user_id, plan.id)

    for change in (CriterionUpdate(met=False), CriterionUpdate(description="rewritten")):
        with pytest.raises(InvalidStateTransitionError, match="completed task"):
            await task_service.update_criterion(user_id, criterion.id, change)

    current = await task_service.get_task(user_id=user_id, task_id=task.id)
    assert current.state == TaskState.DONE
    assert [(c.description, c.met) for c in current.criteria] == [("holds", True)]


@pytest.mark.asyncio
async def test_criterion_of_a_done_task_cannot_be_deleted(test_task_service):
    task_service, plan_service = test_task_service
    user_id = uuid4()
    plan = await _active_plan(plan_service, user_id)
    task, criterion = await _done_task_with_met_criterion(task_service, user_id, plan.id)

    with pytest.raises(InvalidStateTransitionError, match="completed task"):
        await task_service.delete_criterion(user_id, criterion.id)

    assert len((await task_service.get_task(user_id=user_id, task_id=task.id)).criteria) == 1


@pytest.mark.asyncio
async def test_criteria_are_editable_again_after_the_task_is_reopened(test_task_service):
    task_service, plan_service = test_task_service
    user_id = uuid4()
    plan = await _active_plan(plan_service, user_id)
    task, criterion = await _done_task_with_met_criterion(task_service, user_id, plan.id)
    await _move(task_service, user_id, task, TaskState.TODO)

    updated = await task_service.update_criterion(user_id, criterion.id, CriterionUpdate(met=False))

    assert updated.met is False
    assert await task_service.delete_criterion(user_id, criterion.id) is True


@pytest.mark.asyncio
async def test_unknown_criterion_keeps_its_not_found_behaviour(test_task_service):
    task_service, _ = test_task_service
    user_id = uuid4()

    with pytest.raises(NotFoundError):
        await task_service.update_criterion(user_id, 999, CriterionUpdate(met=True))
    assert await task_service.delete_criterion(user_id, 999) is False


# ---------------------------------------------------------------------------
# Criterion and dependency mutations are announced as task updates
# ---------------------------------------------------------------------------


@pytest.fixture
def evented_task_service(mock_task_repository, test_plan_service):
    bus = CollectingEventBus()
    service = TaskService(mock_task_repository, plan_service=test_plan_service, event_bus=bus)
    return service, test_plan_service, bus


def _task_updates(bus, task_id):
    return [
        e for e in bus.collected_events
        if e.entity_type == EntityType.TASK and e.action == ActionType.UPDATED and e.entity_id == task_id
    ]


@pytest.mark.asyncio
async def test_criterion_and_dependency_mutations_emit_task_updated(evented_task_service):
    service, plan_service, bus = evented_task_service
    user_id = uuid4()
    plan = await _active_plan(plan_service, user_id)
    task = await _task(service, user_id, plan.id, "t")
    prerequisite = await _task(service, user_id, plan.id, "prerequisite")
    bus.collected_events.clear()

    criterion = await service.add_criterion(user_id, task.id, CriterionCreate(description="holds"))
    await service.update_criterion(user_id, criterion.id, CriterionUpdate(met=True))
    await service.add_dependency(user_id, task.id, prerequisite.id)
    await service.remove_dependency(user_id, task.id, prerequisite.id)
    await service.delete_criterion(user_id, criterion.id)

    events = _task_updates(bus, task.id)
    assert len(events) == len(bus.collected_events) == 5
    added, met, linked, unlinked, deleted = events
    assert added.changes["criterion"]["old"] is None
    assert added.changes["criterion"]["new"]["description"] == "holds"
    assert [c["met"] for c in added.snapshot["criteria"]] == [False]
    assert met.changes["criterion"]["old"]["met"] is False
    assert met.changes["criterion"]["new"]["met"] is True
    assert [c["met"] for c in met.snapshot["criteria"]] == [True]
    assert linked.changes == {"dependency": {"old": None, "new": prerequisite.id}}
    assert linked.snapshot["dependency_ids"] == [prerequisite.id]
    assert unlinked.changes == {"dependency": {"old": prerequisite.id, "new": None}}
    assert unlinked.snapshot["dependency_ids"] == []
    assert deleted.changes["criterion"]["new"] is None
    assert deleted.snapshot["criteria"] == []


@pytest.mark.asyncio
async def test_no_task_event_for_noop_or_rejected_mutations(evented_task_service):
    service, plan_service, bus = evented_task_service
    user_id = uuid4()
    plan = await _active_plan(plan_service, user_id)
    task = await _task(service, user_id, plan.id, "t", criteria=[CriterionCreate(description="holds")])
    other = await _task(service, user_id, plan.id, "other")
    bus.collected_events.clear()

    await service.update_criterion(user_id, task.criteria[0].id, CriterionUpdate(met=False))
    assert await service.remove_dependency(user_id, task.id, other.id) is False
    assert await service.delete_criterion(user_id, 999) is False
    with pytest.raises(CyclicDependencyError):
        await service.add_dependency(user_id, task.id, task.id)

    assert bus.collected_events == []


# ---------------------------------------------------------------------------
# Plan status follows task reopening and gates task work
# ---------------------------------------------------------------------------


async def _plan_status(plan_service, user_id, plan_id):
    return (await plan_service.get_plan(user_id=user_id, plan_id=plan_id)).status


async def _completed_plan(task_service, plan_service, user_id):
    """An active plan whose two tasks are finished, so it auto-completed."""
    plan = await _active_plan(plan_service, user_id)
    first = await _task(task_service, user_id, plan.id, "first")
    second = await _task(task_service, user_id, plan.id, "second")
    await _finish(task_service, user_id, first)
    await _finish(task_service, user_id, second)
    assert await _plan_status(plan_service, user_id, plan.id) == PlanStatus.COMPLETED
    return plan, first, second


@pytest.mark.asyncio
async def test_reopening_a_done_task_reopens_the_completed_plan(test_task_service):
    task_service, plan_service = test_task_service
    user_id = uuid4()
    plan, first, _second = await _completed_plan(task_service, plan_service, user_id)

    reopened = await _move(task_service, user_id, first, TaskState.TODO)

    assert reopened.state == TaskState.TODO
    assert await _plan_status(plan_service, user_id, plan.id) == PlanStatus.ACTIVE
    claimed = await task_service.claim_task(
        user_id=user_id, task_id=first.id, agent_id="agent", expected_version=reopened.version,
    )
    assert claimed.state == TaskState.DOING
    await _move(task_service, user_id, first, TaskState.DONE)
    assert await _plan_status(plan_service, user_id, plan.id) == PlanStatus.COMPLETED


@pytest.mark.asyncio
async def test_reinstating_a_cancelled_task_reopens_the_completed_plan(test_task_service):
    task_service, plan_service = test_task_service
    user_id = uuid4()
    plan = await _active_plan(plan_service, user_id)
    finished = await _task(task_service, user_id, plan.id, "finished")
    dropped = await _task(task_service, user_id, plan.id, "dropped")
    await _finish(task_service, user_id, finished)
    await _move(task_service, user_id, dropped, TaskState.CANCELLED)
    assert await _plan_status(plan_service, user_id, plan.id) == PlanStatus.COMPLETED

    await _move(task_service, user_id, dropped, TaskState.TODO)

    assert await _plan_status(plan_service, user_id, plan.id) == PlanStatus.ACTIVE


@pytest.mark.asyncio
async def test_failed_reopen_leaves_the_plan_completed(test_task_service):
    task_service, plan_service = test_task_service
    user_id = uuid4()
    plan, first, _second = await _completed_plan(task_service, plan_service, user_id)

    with pytest.raises(ConflictError):
        await task_service.transition_task(
            user_id=user_id, task_id=first.id, new_state=TaskState.TODO, expected_version=1,
        )

    assert await _plan_status(plan_service, user_id, plan.id) == PlanStatus.COMPLETED


@pytest.mark.asyncio
async def test_unfinished_task_cannot_be_started_in_a_completed_plan(test_task_service):
    task_service, plan_service = test_task_service
    user_id = uuid4()
    plan = await _active_plan(plan_service, user_id)
    task = await _task(task_service, user_id, plan.id, "late")
    await plan_service.update_plan(
        user_id=user_id, plan_id=plan.id, plan_data=PlanUpdate(status=PlanStatus.COMPLETED),
    )

    with pytest.raises(InvalidStateTransitionError, match="completed status"):
        await task_service.claim_task(user_id=user_id, task_id=task.id, agent_id="a", expected_version=1)
    with pytest.raises(InvalidStateTransitionError, match="completed status"):
        await _move(task_service, user_id, task, TaskState.DOING)

    assert (await task_service.get_task(user_id=user_id, task_id=task.id)).state == TaskState.TODO


@pytest.mark.asyncio
async def test_task_state_cannot_change_in_an_archived_plan(test_task_service):
    task_service, plan_service = test_task_service
    user_id = uuid4()
    plan = await _active_plan(plan_service, user_id)
    task = await _task(task_service, user_id, plan.id, "t")
    await plan_service.update_plan(
        user_id=user_id, plan_id=plan.id, plan_data=PlanUpdate(status=PlanStatus.ARCHIVED),
    )

    with pytest.raises(InvalidStateTransitionError, match="archived status"):
        await task_service.claim_task(user_id=user_id, task_id=task.id, agent_id="a", expected_version=1)
    with pytest.raises(InvalidStateTransitionError, match="archived status"):
        await _move(task_service, user_id, task, TaskState.CANCELLED)

    assert await _plan_status(plan_service, user_id, plan.id) == PlanStatus.ARCHIVED
