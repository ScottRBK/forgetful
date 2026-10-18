"""Integration tests for the bootstrap composition root (app/bootstrap.py)

Phase 1 of docs/dev/cli_plan.md: the adapter/repo/service/registry wiring is extracted
from main.lifespan() into build_runtime()/dispose_runtime() so the CLI and the server
share one composition root. These tests exercise the factory against in-memory SQLite.
"""
import asyncio
from types import SimpleNamespace

from app.bootstrap import Runtime, build_runtime, dispose_runtime
from app.config.settings import settings
from app.events.event_bus import EventBus
from app.models.activity_models import ActivityEvent
from app.models.memory_models import MemoryCreate
from app.models.user_models import UserCreate


async def test_build_runtime_wires_registry_and_memory_service(sqlite_runtime_settings):
    """build_runtime() returns a usable runtime: populated registry + working services."""
    runtime = await build_runtime()

    try:
        assert len(runtime.registry.list_all_tools()) > 0

        user = await runtime.services.user.get_or_create_user(
            user=UserCreate(
                external_id=settings.DEFAULT_USER_ID,
                name=settings.DEFAULT_USER_NAME,
                email=settings.DEFAULT_USER_EMAIL,
            ),
        )
        write_result = await runtime.services.memory.create_memory(
            user_id=user.id,
            memory_data=MemoryCreate(
                title="Bootstrap smoke memory",
                content="Created through a runtime wired by app.bootstrap.build_runtime",
                context="Verifying the composition root wires services end-to-end",
                keywords=["bootstrap", "factory"],
                tags=["testing"],
                importance=5,
            ),
        )
        memory = write_result.memory
        assert memory.id is not None
        assert memory.title == "Bootstrap smoke memory"
        ctx = SimpleNamespace(
            fastmcp=SimpleNamespace(auth=None, user_service=runtime.services.user),
        )
        rebuilt = await runtime.registry.execute(
            "rebuild_embeddings", {"memory_ids": [memory.id]}, ctx=ctx,
        )
        assert rebuilt == {"rebuilt_ids": [memory.id], "skipped_ids": [], "failed": []}
    finally:
        await dispose_runtime(runtime)


async def test_skills_flag_off_omits_skill_service_and_tools(sqlite_runtime_settings):
    """SKILLS_ENABLED=false -> services.skill is None and no skill tools registered."""
    settings.SKILLS_ENABLED = False

    runtime = await build_runtime()

    try:
        assert runtime.services.skill is None
        tool_names = {meta.name for meta in runtime.registry.list_all_tools()}
        assert "create_skill" not in tool_names
    finally:
        await dispose_runtime(runtime)


async def test_skills_flag_on_wires_skill_service_and_tools(sqlite_runtime_settings):
    """SKILLS_ENABLED=true -> services.skill wired and skill tools registered."""
    settings.SKILLS_ENABLED = True

    runtime = await build_runtime()

    try:
        assert runtime.services.skill is not None
        tool_names = {meta.name for meta in runtime.registry.list_all_tools()}
        assert "create_skill" in tool_names
    finally:
        await dispose_runtime(runtime)


async def test_dispose_runtime_is_idempotent(sqlite_runtime_settings):
    """dispose_runtime() closes the DB adapter and tolerates being called twice."""
    runtime = await build_runtime()

    await dispose_runtime(runtime)
    await dispose_runtime(runtime)


async def test_dispose_runtime_drains_in_flight_event_handlers():
    """Pending fire-and-forget activity tasks must complete before dispose returns.

    The CLI is one-shot: asyncio.run() tears the loop down right after dispose, so
    any handler task still pending at that point would be cancelled and its
    activity write silently lost.
    """
    handled = []

    async def slow_handler(event):
        await asyncio.sleep(0.05)
        handled.append(event)

    bus = EventBus()
    bus.subscribe("*.*", slow_handler)
    await bus.emit(ActivityEvent(entity_type="memory", action="created", snapshot={}))

    class _StubAdapter:
        async def dispose(self):
            pass

    runtime = Runtime(
        db_adapter=_StubAdapter(),
        repos={},
        services=None,
        registry=None,
        permitted_tools=set(),
        instance_scopes=frozenset(),
        event_bus=bus,
    )
    await dispose_runtime(runtime)

    assert handled, "event handler task was not drained before dispose returned"
