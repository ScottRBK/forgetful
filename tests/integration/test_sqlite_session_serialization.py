"""Shared-connection serialization and cancellation against native SQLite."""
import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.bootstrap import create_repositories
from app.config.settings import settings
from app.models.plan_models import PlanCreate, TaskCreate, TaskUpdate
from app.models.project_models import ProjectCreate
from app.models.user_models import UserCreate
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def memory_adapter(monkeypatch):
    monkeypatch.setattr(settings, "SQLITE_MEMORY", True)
    adapter = SqliteDatabaseAdapter()
    try:
        yield adapter
    finally:
        await adapter.dispose()


def session_for(adapter, kind):
    method = getattr(adapter, kind)
    return method() if kind == "system_session" else method(uuid4())


@pytest.mark.parametrize("kind", ["session", "system_session", "snapshot_session"])
async def test_cancelled_memory_waiter_and_holder_release_connection(memory_adapter, kind):
    async def scenario():
        entered = asyncio.Event()
        wait = asyncio.Event()
        never = asyncio.Event()

        async def holding():
            async with session_for(memory_adapter, kind) as session:
                assert await session.scalar(text("SELECT 1")) == 1
                entered.set()
                await never.wait()

        async def waiting():
            await wait.wait()
            async with session_for(memory_adapter, "snapshot_session"):
                pytest.fail("waiter entered while holder still owned the connection")

        # Both tasks are created outside any session, as independent requests are.
        waiter = asyncio.create_task(waiting())
        holder = asyncio.create_task(holding())
        try:
            await entered.wait()
            wait.set()
            await asyncio.sleep(0)
            waiter.cancel()
            with pytest.raises(asyncio.CancelledError):
                await waiter
            holder.cancel()
            with pytest.raises(asyncio.CancelledError):
                await holder
            for next_kind in ["session", "system_session", "snapshot_session"]:
                async with session_for(memory_adapter, next_kind) as session:
                    assert await session.scalar(text("SELECT 1")) == 1
        finally:
            for task in (waiter, holder):
                if not task.done():
                    task.cancel()
            await asyncio.gather(waiter, holder, return_exceptions=True)

    await asyncio.wait_for(scenario(), timeout=5)


async def test_nested_memory_session_fails_without_deadlock(memory_adapter):
    async def nested():
        async with memory_adapter.system_session():
            pass

    async def scenario():
        async with memory_adapter.snapshot_session(uuid4()):
            with pytest.raises(RuntimeError, match="Nested SQLite"):
                await nested()
            # Child tasks inherit the holder's context; they must not hang either.
            with pytest.raises(RuntimeError, match="Nested SQLite"):
                await asyncio.create_task(nested())
        await nested()

    await asyncio.wait_for(scenario(), timeout=5)


async def test_all_memory_session_types_share_one_guard(memory_adapter):
    async def scenario():
        active = 0
        peak = 0

        async def use(kind):
            nonlocal active, peak
            async with session_for(memory_adapter, kind) as session:
                active += 1
                peak = max(peak, active)
                try:
                    assert await session.scalar(text("SELECT 1")) == 1
                    await asyncio.sleep(0)
                finally:
                    active -= 1

        await asyncio.gather(*(use(kind) for kind in [
            "session", "system_session", "snapshot_session",
            "snapshot_session", "session", "system_session",
        ]))
        assert peak == 1

    await asyncio.wait_for(scenario(), timeout=5)


async def test_empty_task_update_preserves_memory_repository_contract(memory_adapter, monkeypatch):
    monkeypatch.setattr(settings, "DATABASE", "SQLite")
    monkeypatch.setattr(settings, "PLANNING_ENABLED", True)

    async def scenario():
        await memory_adapter.init_db()
        repos = create_repositories(memory_adapter, None, None)
        key = uuid4().hex
        owner = await repos["user"].create_user(UserCreate(
            external_id=f"session-owner-{key}", name="Session owner", email=f"{key}@example.test",
        ))
        project = await repos["project"].create_project(owner.id, ProjectCreate(
            name="Session regression", description="Native task session test", project_type="development",
        ))
        plan = await repos["plan"].create_plan(owner.id, PlanCreate(
            project_id=project.id, title="Session regression plan",
        ))
        repository = repos["task"]
        task = await repository.create_task(owner.id, TaskCreate(plan_id=plan.id, title="Original task"))
        before = await repository.get_task_by_id(owner.id, task.id)
        unchanged = await repository.update_task(owner.id, task.id, TaskUpdate())
        assert unchanged == before
        assert unchanged.version == before.version
        assert unchanged.updated_at == before.updated_at
        assert await repository.update_task(owner.id, task.id + 1000, TaskUpdate()) is None
        assert await repository.update_task(uuid4(), task.id, TaskUpdate()) is None
        updated = await repository.update_task(owner.id, task.id, TaskUpdate(title="Updated task"))
        assert updated.title == "Updated task"
        assert await repository.get_task_by_id(owner.id, task.id) == updated
        async with memory_adapter.session(owner.id) as session:
            assert await session.scalar(text("SELECT 1")) == 1

    await asyncio.wait_for(scenario(), timeout=5)
