"""Real runtime/persistence policy phases and cancellation/latency contracts."""

import asyncio
import importlib
from contextlib import asynccontextmanager

import pytest
from memory_link_plugin_helpers import link_runtime as link_runtime
from memory_link_plugin_helpers import memory_arguments

from app.bootstrap import build_runtime, dispose_runtime
from app.config.settings import settings
from app.exceptions import WritePluginRejectedError, WritePluginUnavailableError
from app.models.memory_models import MemoryCreate
from app.models.user_models import UserCreate
from app.models.write_plugin_models import PluginWarning, WriteDecision
from app.protocols.write_plugin_protocol import MemoryLinkPlugin
from app.services.memory_link_service import MemoryLinkService


async def populate(runtime, tags):
    user = await runtime.services.user.get_or_create_user(UserCreate(
        external_id=settings.DEFAULT_USER_ID, name=settings.DEFAULT_USER_NAME,
        email=settings.DEFAULT_USER_EMAIL,
    ))
    service = runtime.services.memory
    result = []
    for index, item in enumerate([[], *tags]):
        created = await service.create_memory(
            user.id, MemoryCreate(**memory_arguments(f"Memory {index}", item)),
        )
        result.append(created.memory)
    return user, result


@pytest.mark.parametrize("mode", ["warn", "enforce"])
@pytest.mark.parametrize("marker", ["reject", "error", "timeout", "child_cancel"])
async def test_manual_all_pair_preflight_prevents_partial_writes(
    link_runtime, monkeypatch, mode, marker,
):
    monkeypatch.setattr(settings, "MEMORY_LINK_PLUGIN_MODE", mode)
    if marker == "timeout":
        monkeypatch.setattr(settings, "MEMORY_LINK_PLUGIN_TIMEOUT_SECONDS", 0.02)
    runtime = await build_runtime()
    try:
        user, (source, first, second) = await populate(runtime, [[], [marker]])
        service = runtime.services.memory
        if mode == "enforce":
            error = WritePluginRejectedError if marker == "reject" else WritePluginUnavailableError
            with pytest.raises(error):
                await service.link_memories(user.id, source.id, [first.id, second.id])
            assert (await service.get_memory(user.id, source.id)).linked_memory_ids == []
        else:
            result = await service.link_memories(user.id, source.id, [first.id, second.id])
            assert result.created_ids == [first.id, second.id]
            assert result.plugin_warnings
        module = importlib.import_module(link_runtime)
        assert len(module.before_calls) == 2
    finally:
        await dispose_runtime(runtime)


async def test_preflight_detachment_no_session_held_and_once_per_batch_after(link_runtime, monkeypatch):
    runtime = await build_runtime()
    try:
        user, (source, first, second) = await populate(runtime, [["mutate"], []])
        service = runtime.services.memory
        repo = service.memory_repo
        active = 0
        original = repo.db_adapter.session

        @asynccontextmanager
        async def tracked_session(*args, **kwargs):
            nonlocal active
            async with original(*args, **kwargs) as session:
                active += 1
                try:
                    yield session
                finally:
                    active -= 1

        monkeypatch.setattr(repo.db_adapter, "session", tracked_session)
        before_ids = []
        after = []

        async def before(request):
            assert active == 0
            # Independent persistence read during each handler proves the whole
            # batch preflight precedes writes, not just the first target.
            assert (await repo.get_memory_by_id(user.id, source.id)).linked_memory_ids == []
            before_ids.append(request.target.id)
            request.target.tags.clear()
            request.source.title = "Cannot rewrite persisted input"
            await asyncio.sleep(0)
            return WriteDecision(outcome="allow")

        async def saved(request):
            assert active == 0
            after.append(request)
            return PluginWarning(message="Check links", code="AFTER")

        service._link_plugin = MemoryLinkService(
            repo, MemoryLinkPlugin(before_save={"link": before}, after_save={"link": saved}),
        )
        result = await service.link_memories(user.id, source.id, [first.id, second.id])
        assert before_ids == [first.id, second.id]
        assert len(after) == 1 and len(after[0].pairs) == 2
        assert [item.status for item in after[0].outcomes] == ["created", "created"]
        assert result.plugin_warnings[0].code == "AFTER"
        assert (await service.get_memory(user.id, first.id)).tags == ["mutate"]
        assert (await service.get_memory(user.id, source.id)).title == source.title
    finally:
        await dispose_runtime(runtime)


@pytest.mark.parametrize("kind", ["failure", "child_cancel", "external_cancel", "malformed", "timeout"])
async def test_after_failure_keeps_committed_links_except_genuine_cancel(link_runtime, kind):
    runtime = await build_runtime()
    try:
        user, (source, target) = await populate(runtime, [[]])
        service = runtime.services.memory

        async def after(request):
            if kind == "failure":
                raise RuntimeError("SYNTHETIC_PRIVATE_ERROR")
            if kind == "malformed":
                return {"unknown": "SYNTHETIC_PRIVATE_ERROR"}
            if kind == "timeout":
                await asyncio.Event().wait()
            if kind == "external_cancel":
                asyncio.current_task().cancel()
                await asyncio.sleep(0)
            child = asyncio.create_task(asyncio.sleep(100))
            child.cancel()
            await child

        service._link_plugin = MemoryLinkService(
            service.memory_repo, MemoryLinkPlugin(after_save={"link": after}),
            timeout_seconds=0.02 if kind == "timeout" else 5.0,
        )
        task = asyncio.create_task(service.link_memories(user.id, source.id, [target.id]))
        if kind == "external_cancel":
            with pytest.raises(asyncio.CancelledError):
                await task
        else:
            result = await task
            assert result.created_ids == [target.id]
            assert result.plugin_warnings[0].code == "MEMORY_LINK_PLUGIN_AFTER_SAVE_UNAVAILABLE"
            assert "SYNTHETIC_PRIVATE_ERROR" not in str(result.response_fields())
        assert (await service.get_memory(user.id, source.id)).linked_memory_ids == [target.id]
    finally:
        await dispose_runtime(runtime)


async def test_registration_freezes_mappings_and_rejects_unknown_or_sync_handlers():
    async def handler(request):
        return WriteDecision(outcome="allow")
    mapping = {"link": handler}
    plugin = MemoryLinkPlugin(before_save=mapping)
    mapping.clear()
    assert plugin.before_save["link"] is handler
    with pytest.raises(TypeError):
        plugin.before_save["unlink"] = handler
    with pytest.raises(ValueError, match="unsupported"):
        MemoryLinkPlugin(before_save={"future": handler})
    with pytest.raises(ValueError, match="async"):
        MemoryLinkPlugin(after_save={"link": lambda request: None})


@pytest.mark.parametrize("reference", ["missing:object", "invalid reference", "builtins:object"])
async def test_bad_registration_fails_startup_before_resources(link_runtime, monkeypatch, reference):
    monkeypatch.setattr(settings, "MEMORY_LINK_PLUGIN", reference)
    called = []
    monkeypatch.setattr("app.bootstrap.get_embedding_adapter", lambda: called.append(True))
    with pytest.raises(ValueError, match="MEMORY_LINK_PLUGIN"):
        await build_runtime()
    assert called == []


@pytest.mark.parametrize("marker", ["reject", "error", "timeout", "child_cancel"])
async def test_automatic_policy_failure_is_advisory_and_after_order_is_truthful(
    link_runtime, monkeypatch, marker,
):
    from app.protocols.write_plugin_protocol import MemoryPlugin
    from app.services.write_plugin_service import WritePluginService

    if marker == "timeout":
        monkeypatch.setattr(settings, "MEMORY_LINK_PLUGIN_TIMEOUT_SECONDS", 0.02)
    runtime = await build_runtime()
    try:
        user, (allowed, blocked) = await populate(runtime, [[marker]])
        service = runtime.services.memory
        from app.events import EventBus
        bus = EventBus()
        events = []

        async def collect(event):
            events.append(event)

        bus.subscribe("memory.created", collect)
        service._event_bus = bus
        module = importlib.import_module(link_runtime)
        original_after = module.registration.after_save["link"]
        seen = []

        async def link_after(request):
            seen.append("link-after")
            assert {pair.target.id for pair in request.pairs} == {allowed.id}
            assert {item.status for item in request.outcomes} == {"created", "rejected"}
            return await original_after(request)

        async def memory_after(request):
            seen.append("memory-after")
            assert request.saved.linked_memory_ids == [allowed.id]

        service._link_plugin = MemoryLinkService(
            service.memory_repo, MemoryLinkPlugin(
                before_save=module.registration.before_save, after_save={"link": link_after},
            ), timeout_seconds=0.02 if marker == "timeout" else 5.0,
        )
        service._write_plugin = WritePluginService(MemoryPlugin(after_save={"create": memory_after}))
        monkeypatch.setattr(settings, "MEMORY_NUM_AUTO_LINK", 5)
        result = await service.create_memory(user.id, MemoryCreate(**memory_arguments("automatically linked")))
        assert result.memory.linked_memory_ids == [allowed.id]
        assert {item.target_id: item.status for item in result.link_outcomes} == {
            allowed.id: "created", blocked.id: "rejected",
        }
        assert result.plugin_warnings and "SYNTHETIC_PRIVATE_ERROR" not in str(result.plugin_warnings)
        assert seen == ["link-after", "memory-after"]
        await bus.wait_for_pending()
        assert len(events) == 1 and events[0].snapshot["linked_memory_ids"] == [allowed.id]
        assert (await service.get_memory(user.id, result.memory.id)).linked_memory_ids == [allowed.id]
        assert not hasattr(await service.get_memory(user.id, result.memory.id), "link_outcomes")
    finally:
        await dispose_runtime(runtime)


async def test_automatic_genuine_cancellation_propagates_after_memory_commit(link_runtime, monkeypatch):
    runtime = await build_runtime()
    try:
        user, _ = await populate(runtime, [])
        service = runtime.services.memory

        async def before(request):
            assert (await service.get_memory(user.id, request.source.id)).id == request.source.id
            asyncio.current_task().cancel()
            await asyncio.sleep(0)

        service._link_plugin = MemoryLinkService(
            service.memory_repo, MemoryLinkPlugin(before_save={"link": before}),
        )
        monkeypatch.setattr(settings, "MEMORY_NUM_AUTO_LINK", 5)
        task = asyncio.create_task(service.create_memory(
            user.id, MemoryCreate(**memory_arguments("persisted before cancellation")),
        ))
        with pytest.raises(asyncio.CancelledError):
            await task
        memories, total = await service.list_memories(user.id)
        assert total == 2
        saved = next(item for item in memories if item.title == "persisted before cancellation")
        assert saved.linked_memory_ids == []
    finally:
        await dispose_runtime(runtime)


async def test_targeted_rebuild_uses_same_automatic_link_policy_once(link_runtime, monkeypatch):
    runtime = await build_runtime()
    try:
        user, (source, allowed, blocked) = await populate(runtime, [[], ["reject"]])
        service = runtime.services.memory
        monkeypatch.setattr(settings, "MEMORY_NUM_AUTO_LINK", 5)
        module = importlib.import_module(link_runtime)
        rebuild = runtime.services.re_embedding
        result = await rebuild.rebuild_targeted(user.id, memory_ids=[source.id])
        assert result.rebuilt_ids == [source.id] and result.failed == []
        assert {item["target_id"]: item["status"] for item in result.link_outcomes} == {
            allowed.id: "created", blocked.id: "rejected",
        }
        assert all(item["source_id"] == source.id for item in result.link_outcomes)
        assert result.plugin_warnings
        assert len(module.before_calls) == 2 and len(module.after_calls) == 1
        assert (await service.get_memory(user.id, source.id)).linked_memory_ids == [allowed.id]
        assert (await service.get_memory(user.id, blocked.id)).linked_memory_ids == []
    finally:
        await dispose_runtime(runtime)
