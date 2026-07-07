"""Integration tests for the bootstrap composition root (app/bootstrap.py)

Phase 1 of docs/dev/cli_plan.md: the adapter/repo/service/registry wiring is extracted
from main.lifespan() into build_runtime()/dispose_runtime() so the CLI and the server
share one composition root. These tests exercise the factory against in-memory SQLite.
"""
from app.bootstrap import build_runtime, dispose_runtime
from app.config.settings import settings
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
        memory, _ = await runtime.services.memory.create_memory(
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
        assert memory.id is not None
        assert memory.title == "Bootstrap smoke memory"
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
