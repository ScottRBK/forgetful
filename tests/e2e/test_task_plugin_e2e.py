"""Task Plugin behaviour against the real PostgreSQL backend.

The SQLite integration tier proves the plugin contract. This tier proves the same
behaviour on the Postgres repositories, where optimistic locking, state
transitions and dependency rows go through different code.

The e2e HTTP app builds services without write plugins, so these tests wire the
plugin onto the Postgres repositories directly rather than assuming transport
coverage implies backend coverage.
"""

import uuid

import pytest

from app.exceptions import WritePluginRejectedError, WritePluginUnavailableError
from app.models.plan_models import (
    PlanCreate,
    PlanStatus,
    PlanUpdate,
    TaskCreate,
    TaskState,
    TaskUpdate,
)
from app.models.project_models import ProjectCreate
from app.models.user_models import UserCreate
from app.models.write_plugin_models import PluginWarning, WriteDecision
from app.protocols.write_plugin_protocol import TaskPlugin
from app.repositories.postgres.plan_repository import PostgresPlanRepository
from app.repositories.postgres.project_repository import PostgresProjectRepository
from app.repositories.postgres.task_repository import PostgresTaskRepository
from app.repositories.postgres.user_repository import PostgresUserRepository
from app.services.plan_service import PlanService
from app.services.project_service import ProjectService
from app.services.task_service import TaskService
from app.services.task_write_plugin_service import TaskWritePluginService
from app.services.user_service import UserService

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.asyncio(loop_scope="session"),
]

SETTINGS_OVERRIDE = {"MEMORY_NUM_AUTO_LINK": 0}


class Recorder:
    """Records operations and returns a scripted decision."""

    def __init__(self, decision: WriteDecision | None = None, *, raises: bool = False):
        self.decision = decision or WriteDecision(outcome="allow")
        self.raises = raises
        self.calls: list[str] = []

    async def before(self, request):
        self.calls.append(request.operation)
        if self.raises:
            raise RuntimeError("SECRET")
        return self.decision

    async def after(self, request):
        self.calls.append(f"after:{request.operation}")
        return PluginWarning(message="Indexer notified.", code="indexer") if (
            getattr(request.saved, "title", "").startswith("after-warn")
        ) else None


async def _store(db_adapter, recorder: Recorder | None, mode="enforce"):
    """Postgres task stack with an optional plugin, plus an active plan."""
    user = await UserService(PostgresUserRepository(db_adapter)).get_or_create_user(
        UserCreate(
            external_id=f"task-plugin-{uuid.uuid4()}",
            name="Task plugin",
            email=f"tp-{uuid.uuid4()}@example.com",
        ),
    )
    project_service = ProjectService(PostgresProjectRepository(db_adapter))
    project = await project_service.create_project(user.id, ProjectCreate(
        name="Postgres task plugin project",
        description="Scoped to the plugin tests",
        project_type="development",
    ))
    plan_service = PlanService(PostgresPlanRepository(db_adapter))
    plan = (await plan_service.create_plan(
        user.id, PlanCreate(title="Plugin plan", project_id=project.id, goal="Ship"),
    )).plan
    plan = (await plan_service.update_plan(
        user.id, plan.id, PlanUpdate(status=PlanStatus.ACTIVE),
    )).plan

    plugin = None
    if recorder is not None:
        plugin = TaskWritePluginService(
            TaskPlugin(
                before_save={
                    "create": recorder.before, "update": recorder.before,
                    "delete": recorder.before,
                },
                after_save={"create": recorder.after, "update": recorder.after},
            ),
            mode=mode,
        )
    service = TaskService(
        PostgresTaskRepository(db_adapter), plan_service=plan_service, write_plugin=plugin,
    )
    return service, plan_service, user.id, plan


def candidate(plan_id: int, **changes) -> TaskCreate:
    base = {"title": "Postgres plugin task", "plan_id": plan_id}
    base.update(changes)
    return TaskCreate(**base)


async def test_postgres_allow_creates_without_warnings(
    db_adapter, clean_database, app_settings,
):
    recorder = Recorder()
    service, _plans, user_id, plan = await _store(db_adapter, recorder)

    result = await service.create_task(user_id, candidate(plan.id))

    assert result.plugin_warnings == []
    assert result.task.id is not None
    assert recorder.calls == ["create", "after:create"]


async def test_postgres_reject_blocks_the_write(db_adapter, clean_database, app_settings):
    recorder = Recorder(WriteDecision(outcome="reject", message="Blocked by policy."))
    service, _plans, user_id, plan = await _store(db_adapter, recorder)

    with pytest.raises(WritePluginRejectedError, match="Blocked by policy"):
        await service.create_task(user_id, candidate(plan.id))

    assert await service.list_tasks(user_id=user_id, plan_id=plan.id) == []


async def test_postgres_noop_update_skips_the_plugin(
    db_adapter, clean_database, app_settings,
):
    recorder = Recorder()
    service, _plans, user_id, plan = await _store(db_adapter, recorder)
    created = await service.create_task(user_id, candidate(plan.id, title="Stable"))

    recorder.calls.clear()
    result = await service.update_task(
        user_id, created.task.id, TaskUpdate(title="Stable", description=None),
    )

    assert recorder.calls == []
    assert result.plugin_warnings == []


async def test_postgres_transition_carries_the_new_state(
    db_adapter, clean_database, app_settings,
):
    seen = {}

    async def capture(request):
        seen["proposed"] = request.proposed
        return WriteDecision(outcome="allow")

    service, _plans, user_id, plan = await _store(db_adapter, None)
    created = await service.create_task(user_id, candidate(plan.id))
    service._write_plugin = TaskWritePluginService(
        TaskPlugin(before_save={"update": capture}),
    )

    await service.transition_task(
        user_id, created.task.id, TaskState.DOING, created.task.version,
    )

    proposed = seen["proposed"]
    assert proposed.state is TaskState.DOING
    assert proposed.version == created.task.version + 1


async def test_postgres_transition_can_be_rejected(
    db_adapter, clean_database, app_settings,
):
    service, _plans, user_id, plan = await _store(db_adapter, None)
    created = await service.create_task(user_id, candidate(plan.id))
    service._write_plugin = TaskWritePluginService(TaskPlugin(before_save={
        "update": Recorder(WriteDecision(outcome="reject", message="Not yet.")).before,
    }))

    with pytest.raises(WritePluginRejectedError):
        await service.transition_task(
            user_id, created.task.id, TaskState.DOING, created.task.version,
        )
    unchanged = await service.get_task(user_id, created.task.id)
    assert unchanged.state is TaskState.TODO


async def test_postgres_unavailable_before_save_blocks_in_enforce_mode(
    db_adapter, clean_database, app_settings,
):
    recorder = Recorder(raises=True)
    service, _plans, user_id, plan = await _store(db_adapter, recorder)

    with pytest.raises(WritePluginUnavailableError):
        await service.create_task(user_id, candidate(plan.id))

    assert await service.list_tasks(user_id=user_id, plan_id=plan.id) == []


async def test_postgres_delete_reject_leaves_the_task(
    db_adapter, clean_database, app_settings,
):
    created_service, _plans, user_id, plan = await _store(db_adapter, None)
    created = await created_service.create_task(user_id, candidate(plan.id))

    recorder = Recorder(WriteDecision(outcome="reject", message="Keep it"))
    service, _plans2, _user2, _plan2 = await _store(db_adapter, recorder)
    with pytest.raises(WritePluginRejectedError):
        await service.delete_task(user_id, created.task.id)

    still_there = await created_service.get_task(user_id, created.task.id)
    assert still_there.id == created.task.id


async def test_postgres_after_save_warning_survives(
    db_adapter, clean_database, app_settings,
):
    recorder = Recorder()
    service, _plans, user_id, plan = await _store(db_adapter, recorder)

    result = await service.create_task(user_id, candidate(plan.id, title="after-warn task"))

    assert result.plugin_warnings[0].code == "indexer"
