"""Committed link changes emit activity before advisory plugin work (real SQLite)."""

import asyncio
from uuid import uuid4

import pytest
from memory_link_plugin_helpers import link_runtime as link_runtime
from memory_link_plugin_helpers import memory_arguments

from app.bootstrap import build_runtime, dispose_runtime
from app.config.settings import settings
from app.events import EventBus
from app.exceptions import WritePluginRejectedError
from app.models.activity_models import ActionType, EntityType
from app.models.memory_models import MemoryCreate
from app.models.user_models import UserCreate
from app.models.write_plugin_models import WriteDecision
from app.protocols.write_plugin_protocol import MemoryLinkPlugin, MemoryPlugin
from app.services.memory_link_service import MemoryLinkService
from app.services.write_plugin_service import WritePluginService


@pytest.fixture
async def event_store(link_runtime, monkeypatch):
    runtime = await build_runtime()
    bus = EventBus()
    try:
        user = await runtime.services.user.get_or_create_user(UserCreate(
            external_id=settings.DEFAULT_USER_ID, name=settings.DEFAULT_USER_NAME,
            email=settings.DEFAULT_USER_EMAIL,
        ))
        service = runtime.services.memory
        memories = []
        for title in ("source", "target", "other"):
            result = await service.create_memory(user.id, MemoryCreate(**memory_arguments(title)))
            memories.append(result.memory)
        emitted, delivered, timeline = [], [], []
        original_emit = service._emit_event

        async def record_emission(**kwargs):
            # Record at the producer, before the real asynchronous bus dispatch.
            emitted.append(kwargs)
            timeline.append("event")
            await original_emit(**kwargs)

        async def collect(event):
            delivered.append(event)

        bus.subscribe("*.*", collect)
        service._event_bus = bus
        monkeypatch.setattr(service, "_emit_event", record_emission)
        yield runtime, user, memories, bus, emitted, delivered, timeline
    finally:
        await bus.wait_for_pending(timeout=5)
        await dispose_runtime(runtime)


def install(service, *, before=None, after=None):
    service._link_plugin = MemoryLinkService(
        service.memory_repo,
        MemoryLinkPlugin(before_save=before or {}, after_save=after or {}),
    )


async def mutate(service, user_id, source_id, target_id, operation):
    if operation == "link":
        return await service.link_memories(user_id, source_id, [target_id])
    if operation == "unlink_batch":
        return await service.unlink_memories_batch(user_id, source_id, [target_id])
    return await service.unlink_memories(user_id, source_id, target_id)


async def reap(task, release):
    release.set()
    if not task.done():
        task.cancel()
    await asyncio.gather(task, return_exceptions=True)


def assert_link_payload(row, user_id, source_id, target_id, action):
    pair = {"source_id": source_id, "target_id": target_id}
    assert row == {
        "user_id": user_id, "entity_type": EntityType.LINK, "entity_id": 0,
        "action": action, "snapshot": pair, "metadata": pair,
    }


@pytest.mark.parametrize("operation", ["link", "unlink", "unlink_batch"])
async def test_manual_event_precedes_after_request_cancellation(event_store, operation):
    runtime, user, (source, target, _), bus, emitted, delivered, _ = event_store
    service = runtime.services.memory
    if operation != "link":
        await service.memory_repo.create_links_batch(user.id, source.id, [target.id])
    entered, release = asyncio.Event(), asyncio.Event()

    async def after(request):
        entered.set()
        await release.wait()

    install(service, after={"link": after, "unlink": after})
    task = asyncio.create_task(mutate(service, user.id, source.id, target.id, operation))
    try:
        await asyncio.wait_for(entered.wait(), timeout=5)
        saved = await service.memory_repo.get_memory_by_id(user.id, source.id)
        assert (target.id in saved.linked_memory_ids) == (operation == "link")
        assert len(emitted) == 1
        action = ActionType.CREATED if operation == "link" else ActionType.DELETED
        assert_link_payload(emitted[0], user.id, source.id, target.id, action)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await bus.wait_for_pending(timeout=5)
        assert len(delivered) == 1
        assert delivered[0].snapshot == emitted[0]["snapshot"]
        assert (target.id in (await service.memory_repo.get_memory_by_id(
            user.id, source.id,
        )).linked_memory_ids) == (operation == "link")
    finally:
        await reap(task, release)


@pytest.mark.parametrize("first", ["link", "unlink"])
async def test_blocked_after_does_not_reverse_concurrent_events(event_store, first):
    runtime, user, (source, target, _), bus, emitted, delivered, _ = event_store
    service = runtime.services.memory
    if first == "unlink":
        await service.memory_repo.create_links_batch(user.id, source.id, [target.id])
    entered, release = asyncio.Event(), asyncio.Event()

    async def block(request):
        entered.set()
        await release.wait()

    async def allow(request):
        return None

    second = "unlink" if first == "link" else "link"
    install(service, after={first: block, second: allow})
    task = asyncio.create_task(mutate(service, user.id, source.id, target.id, first))
    try:
        await asyncio.wait_for(entered.wait(), timeout=5)
        await mutate(service, user.id, source.id, target.id, second)
        expected = [ActionType.CREATED, ActionType.DELETED]
        if first == "unlink":
            expected.reverse()
        assert [row["action"] for row in emitted] == expected
        for row, action in zip(emitted, expected, strict=True):
            assert_link_payload(row, user.id, source.id, target.id, action)
        release.set()
        await asyncio.wait_for(task, timeout=5)
        await bus.wait_for_pending(timeout=5)
        assert len(emitted) == len(delivered) == 2
        saved = await service.memory_repo.get_memory_by_id(user.id, source.id)
        assert (target.id in saved.linked_memory_ids) == (second == "link")
    finally:
        await reap(task, release)


async def test_automatic_created_event_precedes_after_request_cancellation(event_store, monkeypatch):
    runtime, user, _, bus, emitted, delivered, _ = event_store
    service = runtime.services.memory
    entered, release = asyncio.Event(), asyncio.Event()
    source_ids = []

    async def after(request):
        source_ids.append(request.pairs[0].source.id)
        entered.set()
        await release.wait()

    install(service, after={"link": after})
    monkeypatch.setattr(settings, "MEMORY_NUM_AUTO_LINK", 5)
    task = asyncio.create_task(service.create_memory(
        user.id, MemoryCreate(**memory_arguments("auto cancelled")),
    ))
    try:
        await asyncio.wait_for(entered.wait(), timeout=5)
        saved = await service.memory_repo.get_memory_by_id(user.id, source_ids[0])
        assert saved.linked_memory_ids
        assert len(emitted) == 1
        assert emitted[0]["entity_type"] == EntityType.MEMORY
        assert emitted[0]["action"] == ActionType.CREATED
        assert set(emitted[0]["snapshot"]["linked_memory_ids"]) == set(saved.linked_memory_ids)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await bus.wait_for_pending(timeout=5)
        assert len(emitted) == len(delivered) == 1
        assert set((await service.memory_repo.get_memory_by_id(
            user.id, saved.id,
        )).linked_memory_ids) == set(saved.linked_memory_ids)
    finally:
        await reap(task, release)


@pytest.mark.parametrize("case", ["changed", "empty", "rejected", "inactive", "unregistered", "off"])
async def test_automatic_created_exactly_once_and_after_order(event_store, monkeypatch, case):
    runtime, user, _, bus, emitted, delivered, timeline = event_store
    service = runtime.services.memory
    if case == "empty":
        suffix = uuid4().hex
        user = await runtime.services.user.get_or_create_user(UserCreate(
            external_id=f"empty-{suffix}", name="Empty corpus", email=f"{suffix}@example.test",
        ))

    async def link_after(request):
        timeline.append("link-after")

    memory_after_ids = []

    async def memory_after(request):
        timeline.append("memory-after")
        memory_after_ids.append(list(request.saved.linked_memory_ids))

    async def reject(request):
        return WriteDecision(outcome="reject", message="Synthetic automatic rejection")

    install(service, before={"link": reject} if case == "rejected" else {},
            after={"link": link_after})
    if case == "inactive":
        service._link_plugin = None
    elif case == "unregistered":
        install(service, after={"unlink": link_after})
    service._write_plugin = WritePluginService(MemoryPlugin(after_save={"create": memory_after}))
    monkeypatch.setattr(settings, "MEMORY_NUM_AUTO_LINK", 0 if case == "off" else 5)
    result = await service.create_memory(user.id, MemoryCreate(**memory_arguments("auto normal")))
    assert len(emitted) == 1
    assert emitted[0]["entity_type"] == EntityType.MEMORY
    assert emitted[0]["action"] == ActionType.CREATED
    assert set(emitted[0]["snapshot"]["linked_memory_ids"]) == set(result.memory.linked_memory_ids)
    assert timeline == (["event", "link-after", "memory-after"] if case == "changed"
                        else ["event", "memory-after"])
    assert memory_after_ids == [emitted[0]["snapshot"]["linked_memory_ids"]]
    if case in {"empty", "rejected", "off"}:
        assert result.memory.linked_memory_ids == []
    if case == "rejected":
        assert result.plugin_warnings
        assert result.link_outcomes and all(item.status == "rejected" for item in result.link_outcomes)
    if case == "empty":
        assert result.link_outcomes == []
    await bus.wait_for_pending(timeout=5)
    assert len(delivered) == 1
    saved = await service.memory_repo.get_memory_by_id(user.id, result.memory.id)
    assert set(saved.linked_memory_ids) == set(result.memory.linked_memory_ids)


@pytest.mark.parametrize("operation", ["link", "unlink"])
async def test_event_callback_failure_propagates_before_after(event_store, monkeypatch, operation):
    runtime, user, (source, target, _), _, _, _, _ = event_store
    service = runtime.services.memory
    if operation == "unlink":
        await service.memory_repo.create_links_batch(user.id, source.id, [target.id])
    after_calls = []

    async def after(request):
        after_calls.append(request)

    async def failed_emit(**kwargs):
        raise RuntimeError("Synthetic event emission failed")

    install(service, after={operation: after})
    monkeypatch.setattr(service, "_emit_event", failed_emit)
    with pytest.raises(RuntimeError, match="Synthetic event emission failed"):
        await mutate(service, user.id, source.id, target.id, operation)
    assert after_calls == []
    saved = await service.memory_repo.get_memory_by_id(user.id, source.id)
    assert (target.id in saved.linked_memory_ids) == (operation == "link")


async def test_duplicates_noop_and_enforce_rejection_emit_no_invented_events(event_store):
    runtime, user, (source, target, other), bus, emitted, delivered, _ = event_store
    service = runtime.services.memory
    after_calls = []

    async def after(request):
        after_calls.append(request)

    install(service, after={"link": after, "unlink": after})
    result = await service.link_memories(user.id, source.id, [target.id, target.id, source.id])
    assert result.created_ids == [target.id]
    await service.link_memories(user.id, source.id, [target.id])
    await service.unlink_memories(user.id, source.id, other.id)
    await service.unlink_memories_batch(user.id, source.id, [target.id, target.id])
    await service.unlink_memories(user.id, source.id, target.id)
    assert [row["action"] for row in emitted] == [ActionType.CREATED, ActionType.DELETED]
    assert len(after_calls) == 2

    async def reject(request):
        return WriteDecision(outcome="reject", message="Synthetic manual rejection")

    install(service, before={"link": reject}, after={"link": after})
    with pytest.raises(WritePluginRejectedError):
        await service.link_memories(user.id, source.id, [target.id, other.id])
    assert (await service.memory_repo.get_memory_by_id(user.id, source.id)).linked_memory_ids == []
    assert len(emitted) == len(after_calls) == 2
    await bus.wait_for_pending(timeout=5)
    assert len(delivered) == 2


async def test_no_event_bus_is_noop_not_plugin_failure(event_store):
    runtime, user, (source, target, _), _, emitted, delivered, _ = event_store
    service = runtime.services.memory
    service._event_bus = None
    seen = []

    async def after(request):
        seen.append(request)

    install(service, after={"link": after})
    result = await service.link_memories(user.id, source.id, [target.id])
    assert result.created_ids == [target.id] and result.plugin_warnings == []
    assert len(seen) == len(emitted) == 1
    assert delivered == []
    assert (await service.memory_repo.get_memory_by_id(user.id, source.id)).linked_memory_ids == [target.id]
