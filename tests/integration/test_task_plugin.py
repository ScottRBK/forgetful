"""Task Plugin: registration, reject/warn, no-op skip, transitions, cascade."""

import asyncio
import uuid

import pytest
from pydantic import ValidationError

from app.exceptions import WritePluginRejectedError, WritePluginUnavailableError
from app.models.plan_models import (
    PlanCreate,
    PlanStatus,
    PlanUpdate,
    Task,
    TaskCreate,
    TaskState,
    TaskUpdate,
)
from app.models.write_plugin_models import (
    PluginWarning,
    TaskClaimSubmission,
    TaskDeletedRequest,
    TaskDeleteSubmission,
    TaskSavedRequest,
    TaskTransitionSubmission,
    TaskWriteRequest,
    WriteDecision,
)
from app.protocols.write_plugin_protocol import TaskPlugin
from app.services.task_write_plugin_service import TaskWritePluginService

_USER = uuid.uuid4()


def candidate(**changes) -> TaskCreate:
    base = {"title": "Write the thing", "plan_id": 1, "description": None}
    base.update(changes)
    return TaskCreate(**base)


def _decider(decision):
    async def handler(request):
        return decision

    return handler


def _raiser():
    async def handler(request):
        raise RuntimeError("SECRET")

    return handler


def _service(handler, mode="enforce", timeout_seconds=5.0, phase="before_save"):
    return TaskWritePluginService(
        TaskPlugin(**{phase: {"create": handler, "update": handler, "delete": handler}}),
        mode=mode, timeout_seconds=timeout_seconds,
    )


def _write_request(operation="create"):
    return TaskWriteRequest(
        operation=operation, user_id=_USER, submitted=candidate(),
        previous=None, proposed=candidate(),
    )


def _task(**changes) -> Task:
    from datetime import UTC, datetime

    now = datetime.now(UTC)
    base = {
        "id": 1, "plan_id": 1, "title": "Write the thing", "state": TaskState.TODO,
        "created_at": now, "updated_at": now,
    }
    base.update(changes)
    return Task(**base)


def _saved_request():
    return TaskSavedRequest(operation="create", user_id=_USER, saved=_task(), previous=None)


def _deleted_request():
    return TaskDeletedRequest(user_id=_USER, deleted_task_id=1, previous=_task())


# --- registration -----------------------------------------------------------


def test_registration_freezes_the_mapping_and_rejects_bad_operations():
    handlers = {"create": _decider(WriteDecision(outcome="allow"))}
    plugin = TaskPlugin(before_save=handlers)
    handlers["bogus"] = handlers["create"]
    assert "bogus" not in plugin.before_save
    with pytest.raises(ValueError, match="unsupported task operation"):
        TaskPlugin(before_save={"bogus": handlers["create"]})


def test_registration_requires_async_handlers():
    def sync_handler(request):
        return WriteDecision(outcome="allow")

    with pytest.raises(ValueError, match="must be async"):
        TaskPlugin(before_save={"create": sync_handler})


def test_registration_rejects_wrong_arity():
    async def two_args(request, extra):
        return WriteDecision(outcome="allow")

    with pytest.raises(ValueError, match="one context argument"):
        TaskPlugin(before_save={"create": two_args})


# --- reject / warn / allow --------------------------------------------------


async def test_reject_raises_in_enforce_mode():
    service = _service(_decider(WriteDecision(outcome="reject", message="Nope")))
    with pytest.raises(WritePluginRejectedError, match="Nope"):
        await service.before_save(_write_request())


async def test_reject_downgrades_to_warning_in_warn_mode():
    service = _service(
        _decider(WriteDecision(outcome="reject", message="Nope")), mode="warn",
    )
    warnings = await service.before_save(_write_request())
    assert [(w.outcome, w.message) for w in warnings] == [("warn", "Nope")]


async def test_warn_returns_warning_in_both_modes():
    for mode in ("warn", "enforce"):
        service = _service(
            _decider(WriteDecision(outcome="warn", message="Careful", code="c1")), mode=mode,
        )
        warnings = await service.before_save(_write_request())
        assert warnings[0].code == "c1"


async def test_allow_returns_no_warnings():
    service = _service(_decider(WriteDecision(outcome="allow")))
    assert await service.before_save(_write_request()) == []


# --- unavailable / timeout --------------------------------------------------


async def test_handler_error_is_unavailable_in_enforce_mode():
    service = _service(_raiser())
    with pytest.raises(WritePluginUnavailableError, match="Task Write Plugin unavailable"):
        await service.before_save(_write_request())


async def test_handler_error_becomes_warning_in_warn_mode():
    warnings = await _service(_raiser(), mode="warn").before_save(_write_request())
    assert warnings[0].code == "WRITE_PLUGIN_UNAVAILABLE"


async def test_handler_timeout_counts_as_unavailable():
    async def slow(request):
        await asyncio.sleep(5)
        return WriteDecision(outcome="allow")

    service = _service(slow, timeout_seconds=0.01)
    with pytest.raises(WritePluginUnavailableError):
        await service.before_save(_write_request())


async def test_after_save_failure_stays_advisory():
    service = _service(_raiser(), phase="after_save")
    warnings = await service.after_save(_saved_request())
    assert warnings[0].code == "TASK_PLUGIN_AFTER_SAVE_UNAVAILABLE"


async def test_after_save_delete_message_differs():
    service = _service(_raiser(), phase="after_save")
    warnings = await service.after_save(_deleted_request())
    assert "deleted" in warnings[0].message


# --- settings trio ----------------------------------------------------------


def test_settings_trio_defaults():
    from app.config.settings import Settings

    fresh = Settings()
    assert fresh.TASK_WRITE_PLUGIN == ""
    assert fresh.TASK_WRITE_PLUGIN_MODE == "enforce"
    assert fresh.TASK_WRITE_PLUGIN_TIMEOUT_SECONDS == 5.0


def test_settings_mode_is_constrained():
    from app.config.settings import Settings

    with pytest.raises(ValidationError):
        Settings(TASK_WRITE_PLUGIN_MODE="ignore")


def test_settings_timeout_must_be_positive():
    from app.config.settings import Settings

    with pytest.raises(ValidationError):
        Settings(TASK_WRITE_PLUGIN_TIMEOUT_SECONDS=0)


# --- service integration ----------------------------------------------------


async def _active_plan(plan_service, user_id, project_id=None):
    plan = (await plan_service.create_plan(
        user_id=user_id,
        plan_data=PlanCreate(title="Plugin plan", project_id=project_id, goal="test"),
    )).plan
    return (await plan_service.update_plan(
        user_id=user_id, plan_id=plan.id, plan_data=PlanUpdate(status=PlanStatus.ACTIVE),
    )).plan


def _service_with(store, handler, mode="enforce"):
    from app.services.task_service import TaskService

    return TaskService(
        store["task_service"].task_repo,
        plan_service=store["plan_service"],
        write_plugin=_service(handler, mode=mode),
    )


async def test_create_rejects_through_service(task_store):
    store, user_id, _db = task_store
    plan = await _active_plan(store["plan_service"], user_id, store["project_id"])
    service = _service_with(store, _decider(
        WriteDecision(outcome="reject", message="Blocked by policy."),
    ))

    with pytest.raises(WritePluginRejectedError):
        await service.create_task(user_id, candidate(plan_id=plan.id, title="blocked task"))
    assert await service.list_tasks(user_id=user_id, plan_id=plan.id) == []


async def test_create_warns_through_service(task_store):
    store, user_id, _db = task_store
    plan = await _active_plan(store["plan_service"], user_id, store["project_id"])
    service = _service_with(store, _decider(
        WriteDecision(outcome="warn", message="Check the source.", code="source"),
    ))

    result = await service.create_task(user_id, candidate(plan_id=plan.id, title="warn task"))
    assert result.plugin_warnings[0].code == "source"
    assert result.task.id is not None


async def test_update_proposed_is_the_full_merged_record(task_store):
    """`proposed` describes the whole task metadata after the write."""
    store, user_id, _db = task_store
    seen = {}

    async def capture(request):
        seen["proposed"] = request.proposed
        return WriteDecision(outcome="allow")

    plan = await _active_plan(store["plan_service"], user_id, store["project_id"])
    created = await store["task_service"].create_task(
        user_id, candidate(plan_id=plan.id, title="Original", priority="P1"),
    )
    service = _service_with(store, capture)
    await service.update_task(
        user_id, created.task.id, TaskUpdate(description="New description"),
    )

    proposed = seen["proposed"]
    assert proposed.title == "Original"
    assert proposed.description == "New description"
    assert proposed.priority == created.task.priority
    assert proposed.plan_id == plan.id


async def test_update_noop_skips_plugin(task_store):
    store, user_id, _db = task_store
    calls = []

    async def counting(request):
        calls.append(request.operation)
        return WriteDecision(outcome="reject", message="Should not run")

    plan = await _active_plan(store["plan_service"], user_id, store["project_id"])
    created = await store["task_service"].create_task(
        user_id, candidate(plan_id=plan.id, title="Stable"),
    )
    service = _service_with(store, counting)
    result = await service.update_task(
        user_id, created.task.id, TaskUpdate(title="Stable", description=None),
    )

    assert calls == []
    assert result.plugin_warnings == []


async def test_transition_fires_the_plugin_with_the_new_state(task_store):
    """A state change is an update: the plugin sees the post-write task, including state."""
    store, user_id, _db = task_store
    seen = {}

    async def capture(request):
        seen["submitted"] = request.submitted
        seen["proposed"] = request.proposed
        return WriteDecision(outcome="allow")

    plan = await _active_plan(store["plan_service"], user_id, store["project_id"])
    created = await store["task_service"].create_task(
        user_id, candidate(plan_id=plan.id),
    )
    service = _service_with(store, capture)
    await service.transition_task(
        user_id, created.task.id, TaskState.DOING, created.task.version,
    )

    assert isinstance(seen["submitted"], TaskTransitionSubmission)
    assert seen["submitted"].state is TaskState.DOING
    proposed = seen["proposed"]
    assert isinstance(proposed, Task)
    assert proposed.state is TaskState.DOING
    assert proposed.version == created.task.version + 1


async def test_transition_can_be_rejected_before_it_commits(task_store):
    store, user_id, _db = task_store
    plan = await _active_plan(store["plan_service"], user_id, store["project_id"])
    created = await store["task_service"].create_task(
        user_id, candidate(plan_id=plan.id),
    )
    service = _service_with(store, _decider(
        WriteDecision(outcome="reject", message="Not yet."),
    ))

    with pytest.raises(WritePluginRejectedError):
        await service.transition_task(
            user_id, created.task.id, TaskState.DOING, created.task.version,
        )
    unchanged = await service.get_task(user_id, created.task.id)
    assert unchanged.state is TaskState.TODO
    assert unchanged.version == created.task.version


async def test_claim_fires_the_plugin_with_the_agent(task_store):
    store, user_id, _db = task_store
    seen = {}

    async def capture(request):
        seen["submitted"] = request.submitted
        seen["proposed"] = request.proposed
        return WriteDecision(outcome="allow")

    plan = await _active_plan(store["plan_service"], user_id, store["project_id"])
    created = await store["task_service"].create_task(
        user_id, candidate(plan_id=plan.id),
    )
    service = _service_with(store, capture)
    await service.claim_task(
        user_id, created.task.id, agent_id="agent-7", expected_version=created.task.version,
    )

    assert isinstance(seen["submitted"], TaskClaimSubmission)
    assert seen["submitted"].agent_id == "agent-7"
    proposed = seen["proposed"]
    assert proposed.state is TaskState.DOING
    assert proposed.assigned_agent == "agent-7"


async def test_claim_can_be_rejected(task_store):
    store, user_id, _db = task_store
    plan = await _active_plan(store["plan_service"], user_id, store["project_id"])
    created = await store["task_service"].create_task(
        user_id, candidate(plan_id=plan.id),
    )
    service = _service_with(store, _decider(
        WriteDecision(outcome="reject", message="No claims."),
    ))

    with pytest.raises(WritePluginRejectedError):
        await service.claim_task(
            user_id, created.task.id, agent_id="agent-7",
            expected_version=created.task.version,
        )
    unchanged = await service.get_task(user_id, created.task.id)
    assert unchanged.state is TaskState.TODO
    assert unchanged.assigned_agent is None


async def test_delete_runs_before_and_after(task_store):
    store, user_id, _db = task_store
    calls = []

    async def before(request):
        calls.append(("before", request.operation))
        return WriteDecision(outcome="allow")

    async def after(request):
        calls.append(("after", request.operation))
        return None

    plugin = TaskPlugin(before_save={"delete": before}, after_save={"delete": after})
    plan = await _active_plan(store["plan_service"], user_id, store["project_id"])
    created = await store["task_service"].create_task(
        user_id, candidate(plan_id=plan.id),
    )
    from app.services.task_service import TaskService

    service = TaskService(
        store["task_service"].task_repo, plan_service=store["plan_service"],
        write_plugin=TaskWritePluginService(plugin),
    )
    result = await service.delete_task(user_id, created.task.id)

    assert result.success is True
    assert calls == [("before", "delete"), ("after", "delete")]


async def test_delete_rejected_leaves_task(task_store):
    store, user_id, _db = task_store
    plan = await _active_plan(store["plan_service"], user_id, store["project_id"])
    created = await store["task_service"].create_task(
        user_id, candidate(plan_id=plan.id),
    )
    service = _service_with(store, _decider(
        WriteDecision(outcome="reject", message="Keep it"),
    ))
    with pytest.raises(WritePluginRejectedError):
        await service.delete_task(user_id, created.task.id)
    still_there = await service.get_task(user_id, created.task.id)
    assert still_there.id == created.task.id


async def test_delete_missing_task_skips_the_plugin(task_store):
    store, user_id, _db = task_store
    calls = []

    async def counting(request):
        calls.append(request.operation)
        return WriteDecision(outcome="reject", message="Should not run")

    service = _service_with(store, counting)
    result = await service.delete_task(user_id, 4242)

    assert result.success is False
    assert result.plugin_warnings == []
    assert calls == []


async def test_delete_submission_carries_the_task_id(task_store):
    store, user_id, _db = task_store
    seen = {}

    async def capture(request):
        seen["submitted"] = request.submitted
        seen["proposed"] = request.proposed
        return WriteDecision(outcome="allow")

    plan = await _active_plan(store["plan_service"], user_id, store["project_id"])
    created = await store["task_service"].create_task(
        user_id, candidate(plan_id=plan.id),
    )
    service = _service_with(store, capture)
    await service.delete_task(user_id, created.task.id)

    assert isinstance(seen["submitted"], TaskDeleteSubmission)
    assert seen["submitted"].task_id == created.task.id
    assert seen["proposed"] is None


async def test_before_handler_mutation_does_not_reach_the_stored_task(task_store):
    store, user_id, _db = task_store

    async def tamper(request):
        request.proposed.title = "injected"
        return WriteDecision(outcome="allow")

    plan = await _active_plan(store["plan_service"], user_id, store["project_id"])
    service = _service_with(store, tamper)
    result = await service.create_task(user_id, candidate(plan_id=plan.id, title="clean"))

    assert result.task.title == "clean"


async def test_after_save_warning_survives_create(task_store):
    store, user_id, _db = task_store

    async def after(request):
        return PluginWarning(message="Indexer notified.", code="indexer")

    from app.services.task_service import TaskService

    plan = await _active_plan(store["plan_service"], user_id, store["project_id"])
    service = TaskService(
        store["task_service"].task_repo, plan_service=store["plan_service"],
        write_plugin=TaskWritePluginService(TaskPlugin(after_save={"create": after})),
    )
    result = await service.create_task(user_id, candidate(plan_id=plan.id))
    assert result.plugin_warnings[0].code == "indexer"


# --- dependencies and cascade ----------------------------------------------


async def test_delete_removes_dependency_rows_in_both_directions(task_store):
    """Deleting a task cascades dependency edges, including ones other tasks held."""
    store, user_id, _db = task_store
    plan = await _active_plan(store["plan_service"], user_id, store["project_id"])
    blocker = await store["task_service"].create_task(
        user_id, candidate(plan_id=plan.id, title="Blocker"),
    )
    dependent = await store["task_service"].create_task(
        user_id, candidate(plan_id=plan.id, title="Dependent"),
    )
    await store["task_service"].add_dependency(
        user_id, dependent.task.id, blocker.task.id,
    )
    assert (await store["task_service"].get_task(
        user_id, dependent.task.id,
    )).dependency_ids == [blocker.task.id]

    calls = []

    async def record(request):
        calls.append(request.operation)
        return WriteDecision(outcome="allow")

    deleted = await _service_with(store, record).delete_task(user_id, blocker.task.id)

    assert deleted.success is True
    # Only the deleted task fired; the dependent task's edge vanished silently.
    assert calls == ["delete"]
    remaining = await store["task_service"].get_task(user_id, dependent.task.id)
    assert remaining.dependency_ids == []
    assert remaining.state is TaskState.TODO


async def test_dependency_changes_do_not_fire_the_plugin(task_store):
    store, user_id, _db = task_store
    calls = []

    async def record(request):
        calls.append(request.operation)
        return WriteDecision(outcome="allow")

    plan = await _active_plan(store["plan_service"], user_id, store["project_id"])
    service = _service_with(store, record)
    first = await service.create_task(user_id, candidate(plan_id=plan.id, title="One"))
    second = await service.create_task(user_id, candidate(plan_id=plan.id, title="Two"))
    calls.clear()

    await service.add_dependency(user_id, second.task.id, first.task.id)
    await service.remove_dependency(user_id, second.task.id, first.task.id)

    assert calls == []


async def test_plan_delete_removes_tasks_without_firing_the_task_plugin(task_store):
    """Deleting a plan cascades its tasks at the database level."""
    store, user_id, _db = task_store
    calls = []

    async def record(request):
        calls.append(request.operation)
        return WriteDecision(outcome="allow")

    plan = await _active_plan(store["plan_service"], user_id, store["project_id"])
    created = await store["task_service"].create_task(
        user_id, candidate(plan_id=plan.id),
    )
    calls.clear()

    assert (await store["plan_service"].delete_plan(user_id, plan.id)).success

    assert calls == [], "a plan cascade must not run the task plugin"
    assert await store["task_service"].task_repo.get_task_by_id(
        user_id, created.task.id,
    ) is None


# --- null policy (must match the behaviour before this feature) -------------


async def test_explicit_null_still_clears_a_nullable_field(task_store):
    """description is nullable: an explicit null clears it, as it did before.

    Dropping nulls before change detection would silently ignore this request.
    """
    store, user_id, _db = task_store
    plan = await _active_plan(store["plan_service"], user_id, store["project_id"])
    created = await store["task_service"].create_task(
        user_id, candidate(plan_id=plan.id, description="clear me"),
    )

    result = await store["task_service"].update_task(
        user_id, created.task.id, TaskUpdate(description=None),
    )

    assert result.task.description is None
    refreshed = await store["task_service"].get_task(user_id, created.task.id)
    assert refreshed.description is None


async def test_explicit_null_on_a_required_field_still_fails(task_store):
    """title is NOT NULL: an explicit null must still reach the repository and fail.

    Silently treating it as "unchanged" would accept a write the database rejects.
    """
    from sqlalchemy.exc import SQLAlchemyError

    store, user_id, _db = task_store
    plan = await _active_plan(store["plan_service"], user_id, store["project_id"])
    created = await store["task_service"].create_task(
        user_id, candidate(plan_id=plan.id, title="keep me"),
    )

    with pytest.raises(SQLAlchemyError):
        await store["task_service"].update_task(
            user_id, created.task.id, TaskUpdate(title=None),
        )

    refreshed = await store["task_service"].get_task(user_id, created.task.id)
    assert refreshed.title == "keep me"


async def test_null_on_a_required_field_is_not_accepted_with_a_plugin(task_store):
    """A registered plugin must not turn a rejected write into a successful one."""
    from pydantic import ValidationError
    from sqlalchemy.exc import SQLAlchemyError

    store, user_id, _db = task_store
    plan = await _active_plan(store["plan_service"], user_id, store["project_id"])
    created = await store["task_service"].create_task(
        user_id, candidate(plan_id=plan.id, title="keep me too"),
    )
    calls = []

    async def allow(request):
        calls.append(request.operation)
        return WriteDecision(outcome="allow")

    service = _service_with(store, allow)
    with pytest.raises((SQLAlchemyError, ValidationError)):
        await service.update_task(user_id, created.task.id, TaskUpdate(title=None))

    refreshed = await service.get_task(user_id, created.task.id)
    assert refreshed.title == "keep me too"
