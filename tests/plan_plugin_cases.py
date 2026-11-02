"""The same Plan Plugin persistence contracts run on native SQLite and PostgreSQL."""

import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.bootstrap import create_repositories
from app.config.settings import settings
from app.exceptions import (
    ConflictError,
    InvalidStateTransitionError,
    NotFoundError,
    PlanPluginRejectedError,
    PlanPluginStateChangedError,
)
from app.models.plan_models import (
    PlanCreate,
    PlanStatus,
    PlanUpdate,
    TaskCreate,
    TaskState,
)
from app.models.project_models import ProjectCreate
from app.models.user_models import UserCreate
from app.models.write_plugin_models import PluginWarning, WriteDecision
from app.protocols.plan_plugin_protocol import PlanPlugin
from app.services.plan_service import PlanService
from app.services.plan_write_plugin_service import PlanWritePluginService
from app.services.project_service import ProjectService
from app.services.task_service import TaskService


@pytest.fixture
async def plan_store(reference_db, monkeypatch):
    monkeypatch.setattr(settings, "PLANNING_ENABLED", True)
    repos = create_repositories(reference_db, None, None)
    key = uuid4().hex
    user = await repos["user"].create_user(UserCreate(
        external_id=f"plan-policy-{key}", name="Synthetic plan policy user", email=f"{key}@example.test",
    ))
    project = await repos["project"].create_project(user.id, ProjectCreate(
        name="Synthetic plan policy project", description="Native persistence tests", project_type="development",
    ))
    state = SimpleNamespace(before=[], after=[], decision="allow", after_failure=False, pause=None)

    async def before(context):
        state.before.append(context.model_copy(deep=True))
        if state.pause is not None:
            await state.pause(context)
        if state.decision == "error":
            raise RuntimeError("SYNTHETIC_PRIVATE_ERROR")
        return WriteDecision(
            outcome=state.decision, message="Synthetic plan policy", code="PLAN_TEST",
        )

    async def after(context):
        state.after.append(context.model_copy(deep=True))
        if state.after_failure:
            raise RuntimeError("SYNTHETIC_PRIVATE_ERROR")
        return PluginWarning(message="Synthetic after warning", code="PLAN_AFTER")

    plugin = PlanPlugin(
        before_save=dict.fromkeys(("create", "update", "delete"), before),
        after_save=dict.fromkeys(("create", "update", "delete"), after),
    )
    runner = PlanWritePluginService(plugin)
    service = PlanService(repos["plan"], plan_plugin=runner, project_repo=repos["project"])
    jobs = []

    def spawn(awaitable):
        job = asyncio.create_task(awaitable)
        jobs.append(job)
        return job

    try:
        yield SimpleNamespace(
            repos=repos, user=user, project=project, state=state, plugin=plugin,
            plans=service, tasks=TaskService(repos["task"], service), spawn=spawn,
        )
    finally:
        for job in jobs:
            if not job.done():
                job.cancel()
        if jobs:
            await asyncio.gather(*jobs, return_exceptions=True)


async def active_plan(store):
    created = await store.plans.create_plan(store.user.id, PlanCreate(
        project_id=store.project.id, title="Native plan", status=PlanStatus.ACTIVE,
    ))
    store.state.before.clear()
    store.state.after.clear()
    return created.plan


class TestPlanPluginPersistence:
    async def test_crud_snapshots_and_confirmed_delete(self, plan_store):
        s = plan_store
        result = await s.plans.create_plan(s.user.id, PlanCreate(
            project_id=s.project.id, title="Original", external_ref="native:1",
        ))
        plan = result.plan
        assert result.plugin_warnings[0].code == "PLAN_AFTER"
        assert len(s.state.before) == len(s.state.after) == 1
        assert s.state.before[0].previous is None
        updated = await s.plans.update_plan(s.user.id, plan.id, PlanUpdate(title="Updated"))
        assert updated.plan.title == "Updated"
        assert s.state.after[-1].previous.title == "Original"
        assert (await s.repos["plan"].get_plan_by_id(s.user.id, plan.id)).title == "Updated"
        deleted = await s.plans.delete_plan(s.user.id, plan.id)
        assert deleted.success
        assert s.state.after[-1].deleted_plan_id == plan.id
        assert not hasattr(s.state.after[-1], "saved")
        assert await s.repos["plan"].get_plan_by_id(s.user.id, plan.id) is None
        assert [ctx.operation for ctx in s.state.before] == ["create", "update", "delete"]
        assert [ctx.operation for ctx in s.state.after] == ["create", "update", "delete"]

    async def test_core_ownership_and_external_reference_stay_authoritative(self, plan_store):
        s = plan_store
        result = await s.plans.create_plan(s.user.id, PlanCreate(
            project_id=s.project.id, title="Owned", external_ref="native:unique",
        ))
        before_count, after_count = len(s.state.before), len(s.state.after)
        with pytest.raises(NotFoundError, match=f"Project {s.project.id} not found"):
            await s.plans.create_plan(uuid4(), PlanCreate(project_id=s.project.id, title="Foreign"))
        assert len(s.state.before) == before_count
        other_user = uuid4()
        assert (await s.plans.update_plan(other_user, result.plan.id, PlanUpdate(title="Foreign"))).plan is None
        assert not (await s.plans.delete_plan(other_user, result.plan.id)).success
        assert len(s.state.before) == before_count and len(s.state.after) == after_count
        with pytest.raises(ConflictError):
            await s.plans.create_plan(s.user.id, PlanCreate(
                project_id=s.project.id, title="Duplicate", external_ref="native:unique",
            ))
        assert len(s.state.before) == before_count + 1
        assert len(s.state.after) == after_count
        assert (await s.plans.get_plan(s.user.id, result.plan.id)).title == "Owned"

    async def test_rejection_and_after_failure_preserve_persisted_outcomes(self, plan_store):
        s = plan_store
        plan = await active_plan(s)
        s.state.decision = "reject"
        with pytest.raises(PlanPluginRejectedError):
            await s.plans.update_plan(s.user.id, plan.id, PlanUpdate(title="Rejected"))
        with pytest.raises(PlanPluginRejectedError):
            await s.plans.delete_plan(s.user.id, plan.id)
        assert (await s.plans.get_plan(s.user.id, plan.id)).title == "Native plan"
        assert s.state.after == []
        s.state.decision = "allow"
        s.state.after_failure = True
        result = await s.plans.update_plan(s.user.id, plan.id, PlanUpdate(title="Persisted"))
        assert result.plugin_warnings[0].code == "PLAN_PLUGIN_AFTER_SAVE_UNAVAILABLE"
        assert (await s.plans.get_plan(s.user.id, plan.id)).title == "Persisted"
        deleted = await s.plans.delete_plan(s.user.id, plan.id)
        assert deleted.success and deleted.plugin_warnings[0].code == "PLAN_PLUGIN_AFTER_SAVE_UNAVAILABLE"
        assert await s.repos["plan"].get_plan_by_id(s.user.id, plan.id) is None

    async def test_noop_missing_and_invalid_transition_dispatch_nothing(self, plan_store, monkeypatch):
        s = plan_store
        plan = await active_plan(s)
        monkeypatch.setattr(settings, "ENFORCE_ENV_OVERWRITE", True)
        monkeypatch.setattr(settings, "ENCODING_AGENT", "must-not-inject")
        result = await s.plans.update_plan(s.user.id, plan.id, PlanUpdate())
        assert result.plan.encoding_agent == plan.encoding_agent
        assert (await s.plans.update_plan(s.user.id, -1, PlanUpdate(title="Missing"))).plan is None
        assert not (await s.plans.delete_plan(s.user.id, -1)).success
        await s.repos["plan"].update_plan(s.user.id, plan.id, PlanUpdate(status=PlanStatus.DRAFT))
        with pytest.raises(InvalidStateTransitionError):
            await s.plans.update_plan(s.user.id, plan.id, PlanUpdate(status=PlanStatus.COMPLETED))
        assert s.state.before == s.state.after == []

    async def test_before_await_rechecks_transition_and_preserves_concurrent_patch(self, plan_store):
        s = plan_store
        plan = await active_plan(s)
        entered, release = asyncio.Event(), asyncio.Event()

        async def pause(context):
            entered.set()
            await release.wait()

        s.state.pause = pause
        work = s.spawn(s.plans.update_plan(s.user.id, plan.id, PlanUpdate(goal="New goal")))
        await asyncio.wait_for(entered.wait(), timeout=10)
        await s.repos["plan"].update_plan(s.user.id, plan.id, PlanUpdate(title="Concurrent title"))
        release.set()
        result = await work
        assert result.plan.title == "Concurrent title" and result.plan.goal == "New goal"
        assert s.state.after[-1].previous.title == "Concurrent title"

        entered.clear()
        release.clear()
        s.state.after.clear()
        work = s.spawn(s.plans.update_plan(s.user.id, plan.id, PlanUpdate(status=PlanStatus.COMPLETED)))
        await asyncio.wait_for(entered.wait(), timeout=10)
        await s.repos["plan"].update_plan(s.user.id, plan.id, PlanUpdate(status=PlanStatus.ARCHIVED))
        release.set()
        with pytest.raises(PlanPluginStateChangedError):
            await work
        assert (await s.plans.get_plan(s.user.id, plan.id)).status == PlanStatus.ARCHIVED
        assert s.state.after == []

    async def test_lost_delete_race_has_no_after_success(self, plan_store):
        s = plan_store
        plan = await active_plan(s)

        async def remove(context):
            assert await s.repos["plan"].delete_plan(s.user.id, plan.id)

        s.state.pause = remove
        result = await s.plans.delete_plan(s.user.id, plan.id)
        assert not result.success
        assert len(s.state.before) == 1 and s.state.after == []

    @pytest.mark.parametrize("cascade", ["plan", "project"])
    async def test_cascades_do_not_dispatch_per_task_or_indirect_plan(self, plan_store, cascade):
        s = plan_store
        plan = await active_plan(s)
        task = await s.tasks.create_task(s.user.id, TaskCreate(plan_id=plan.id, title="Cascaded task"))
        s.state.before.clear()
        s.state.after.clear()
        if cascade == "plan":
            assert (await s.plans.delete_plan(s.user.id, plan.id)).success
            assert [x.operation for x in s.state.before] == ["delete"]
        else:
            assert await ProjectService(s.repos["project"]).delete_project(s.user.id, s.project.id)
            assert s.state.before == []
        assert await s.repos["plan"].get_plan_by_id(s.user.id, plan.id) is None
        assert await s.repos["task"].get_task_by_id(s.user.id, task.id) is None

    @pytest.mark.parametrize("path", ["transition", "delete"])
    @pytest.mark.parametrize("policy,mode,code", [
        ("reject", "enforce", "plan_auto_completion_rejected"),
        ("error", "enforce", "plan_auto_completion_unavailable"),
        ("reject", "warn", "PLAN_TEST"),
        ("allow", "enforce", "PLAN_AFTER"),
    ])
    async def test_task_commit_survives_secondary_policy_outcome(self, plan_store, path, policy, mode, code):
        s = plan_store
        plan = await active_plan(s)
        target = await s.tasks.create_task(s.user.id, TaskCreate(plan_id=plan.id, title="Target"))
        blocker = await s.tasks.create_task(s.user.id, TaskCreate(plan_id=plan.id, title="Blocker"))
        doing = await s.tasks.transition_task(s.user.id, target.id, TaskState.DOING, target.version)
        if path == "delete":
            done = await s.tasks.transition_task(s.user.id, target.id, TaskState.DONE, doing.task.version)
            assert done.task.state == TaskState.DONE
        else:
            await s.repos["task"].delete_task(s.user.id, blocker.id)
        s.plans._plan_plugin = PlanWritePluginService(s.plugin, mode=mode)
        s.state.decision = policy
        if path == "delete":
            result = await s.tasks.delete_task(s.user.id, blocker.id)
            assert result.success
            assert await s.repos["task"].get_task_by_id(s.user.id, blocker.id) is None
        else:
            result = await s.tasks.transition_task(s.user.id, target.id, TaskState.DONE, doing.task.version)
            saved = await s.repos["task"].get_task_by_id(s.user.id, target.id)
            assert result.task.version == saved.version == doing.task.version + 1
            assert saved.state == TaskState.DONE
        assert result.plugin_warnings[0].code == code
        expected = PlanStatus.ACTIVE if mode == "enforce" and policy != "allow" else PlanStatus.COMPLETED
        assert (await s.plans.get_plan(s.user.id, plan.id)).status == expected
        assert len(s.state.before) == 1 and s.state.before[0].automatic
        assert len(s.state.after) == (expected == PlanStatus.COMPLETED)
        if s.state.after:
            assert s.state.after[0].automatic
        if expected == PlanStatus.COMPLETED:
            counts = (len(s.state.before), len(s.state.after))
            assert await s.tasks._check_plan_auto_completion(s.user.id, plan.id) == []
            assert (len(s.state.before), len(s.state.after)) == counts

    async def test_concurrent_completions_do_not_promise_atomic_dispatch(self, plan_store):
        s = plan_store
        plan = await active_plan(s)
        task = await s.tasks.create_task(s.user.id, TaskCreate(plan_id=plan.id, title="Done seed"))
        doing = await s.repos["task"].transition_task_state(s.user.id, task.id, TaskState.DOING, task.version)
        await s.repos["task"].transition_task_state(s.user.id, task.id, TaskState.DONE, doing.version)
        barrier = asyncio.Barrier(2)

        async def pause(context):
            await asyncio.wait_for(barrier.wait(), timeout=10)

        s.state.pause = pause
        results = await asyncio.gather(
            s.tasks._check_plan_auto_completion(s.user.id, plan.id),
            s.tasks._check_plan_auto_completion(s.user.id, plan.id),
        )
        assert len(s.state.before) == 2
        assert 1 <= len(s.state.after) <= 2
        assert (await s.plans.get_plan(s.user.id, plan.id)).status == PlanStatus.COMPLETED
        assert len(results) == 2


    @pytest.mark.parametrize("control", ["empty", "all_cancelled", "non_active"])
    async def test_automatic_nontrigger_controls(self, plan_store, control):
        s = plan_store
        plan = await active_plan(s)
        if control != "empty":
            task = await s.tasks.create_task(s.user.id, TaskCreate(plan_id=plan.id, title="Control"))
            state = TaskState.CANCELLED if control == "all_cancelled" else TaskState.DONE
            if state == TaskState.DONE:
                doing = await s.repos["task"].transition_task_state(s.user.id, task.id, TaskState.DOING, task.version)
                version = doing.version
            else:
                version = task.version
            await s.repos["task"].transition_task_state(s.user.id, task.id, state, version)
        if control == "non_active":
            await s.repos["plan"].update_plan(s.user.id, plan.id, PlanUpdate(status=PlanStatus.ARCHIVED))
        assert await s.tasks._check_plan_auto_completion(s.user.id, plan.id) == []
        assert s.state.before == s.state.after == []

    async def test_unrelated_secondary_error_keeps_existing_postcommit_propagation(self, plan_store, monkeypatch):
        s = plan_store
        plan = await active_plan(s)
        task = await s.tasks.create_task(s.user.id, TaskCreate(plan_id=plan.id, title="Committed task"))
        doing = await s.tasks.transition_task(s.user.id, task.id, TaskState.DOING, task.version)

        async def fail(*args, **kwargs):
            raise RuntimeError("Synthetic unrelated repository failure")

        monkeypatch.setattr(s.plans, "update_plan", fail)
        with pytest.raises(RuntimeError, match="unrelated repository"):
            await s.tasks.transition_task(s.user.id, task.id, TaskState.DONE, doing.task.version)
        saved = await s.repos["task"].get_task_by_id(s.user.id, task.id)
        assert saved.state == TaskState.DONE and saved.version == doing.task.version + 1
        assert (await s.plans.get_plan(s.user.id, plan.id)).status == PlanStatus.ACTIVE

    async def test_cancelled_request_during_secondary_policy_keeps_primary_committed(self, plan_store):
        s = plan_store
        plan = await active_plan(s)
        task = await s.tasks.create_task(s.user.id, TaskCreate(plan_id=plan.id, title="Cancelled request"))
        doing = await s.tasks.transition_task(s.user.id, task.id, TaskState.DOING, task.version)
        entered = asyncio.Event()

        async def wait(context):
            entered.set()
            await asyncio.Event().wait()

        s.state.pause = wait
        work = s.spawn(s.tasks.transition_task(s.user.id, task.id, TaskState.DONE, doing.task.version))
        await asyncio.wait_for(entered.wait(), timeout=10)
        work.cancel()
        with pytest.raises(asyncio.CancelledError):
            await work
        saved = await s.repos["task"].get_task_by_id(s.user.id, task.id)
        assert saved.state == TaskState.DONE and saved.version == doing.task.version + 1
        assert (await s.plans.get_plan(s.user.id, plan.id)).status == PlanStatus.ACTIVE
        assert s.state.after == []


    async def test_handler_mutation_cannot_rewrite_saved_data(self, plan_store):
        s = plan_store

        async def mutate_before(context):
            context.user_id = uuid4()
            if context.proposed is not None:
                context.proposed.title = "Must not persist"
                context.proposed.project_id = -1
            if context.previous is not None:
                context.previous.title = "Must not leak into previous"
            return WriteDecision(outcome="allow")

        async def mutate_after(context):
            if hasattr(context, "saved"):
                context.saved.title = "Must not change result"
            return None

        plugin = PlanPlugin(
            before_save=dict.fromkeys(("create", "update", "delete"), mutate_before),
            after_save=dict.fromkeys(("create", "update", "delete"), mutate_after),
        )
        s.plans._plan_plugin = PlanWritePluginService(plugin)
        created = await s.plans.create_plan(s.user.id, PlanCreate(project_id=s.project.id, title="Core create"))
        assert created.plan.title == "Core create" and created.plan.project_id == s.project.id
        updated = await s.plans.update_plan(s.user.id, created.plan.id, PlanUpdate(title="Core update"))
        assert updated.plan.title == "Core update"
        assert (await s.repos["plan"].get_plan_by_id(s.user.id, created.plan.id)).title == "Core update"
        assert (await s.plans.delete_plan(s.user.id, created.plan.id)).success

    async def test_unregistered_create_needs_no_new_project_query(self, plan_store):
        s = plan_store

        async def update_only(context):
            return WriteDecision(outcome="allow")

        service = PlanService(s.repos["plan"], plan_plugin=PlanWritePluginService(
            PlanPlugin(before_save={"update": update_only}),
        ))
        # No injected ProjectRepository: an unregistered create must still use
        # the existing repository ownership check without a new service query.
        result = await service.create_plan(s.user.id, PlanCreate(project_id=s.project.id, title="No create handler"))
        assert result.plan.title == "No create handler" and result.plugin_warnings == []
