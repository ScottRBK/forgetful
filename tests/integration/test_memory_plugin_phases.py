"""Memory Plugin phases through public service workflows and real isolated SQLite."""

import asyncio
import logging

import pytest
from test_memory_write_plugin import candidate
from test_memory_write_plugin import write_store as write_store

from app.config.settings import settings
from app.exceptions import (
    InvalidStateTransitionError,
    NotFoundError,
    WritePluginRejectedError,
)
from app.models.memory_models import MemoryUpdate
from app.models.write_plugin_models import PluginWarning, WriteDecision
from app.protocols.write_plugin_protocol import MemoryPlugin
from app.services.memory_service import MemoryService
from app.services.write_plugin_service import WritePluginService


async def test_after_create_sees_saved_links_and_scores_without_mutating_them(write_store):
    repo, user_id, _, bus = write_store
    observer = MemoryService(repo)
    neighbor = (await observer.create_memory(user_id, candidate(tags=["original"]))).memory
    seen, persisted, events = [], [], []

    async def before(request):
        return WriteDecision(outcome="warn", message="Check the source.")

    async def after(request):
        seen.append(request.model_copy(deep=True))
        persisted.append(await observer.get_memory(request.user_id, request.saved.id))
        request.saved.tags.append("plugin mutation")
        request.saved.linked_memory_ids.clear()
        request.similar_memories[0].tags.append("neighbor mutation")
        return PluginWarning(message="Possible duplicate.", code="near_duplicate")

    async def collect(event):
        events.append(event)

    bus.subscribe("memory.*", collect)
    plugin = MemoryPlugin(before_save={"create": before}, after_save={"create": after})
    service = MemoryService(repo, bus, WritePluginService(plugin))

    created = await service.create_memory(user_id, candidate())
    await service.update_memory(user_id, created.memory.id, MemoryUpdate(importance=8))
    await bus.wait_for_pending()

    assert [warning.message for warning in created.plugin_warnings] == [
        "Check the source.", "Possible duplicate.",
    ]
    assert len(seen) == 1
    assert seen[0].operation == "create"
    assert seen[0].user_id == user_id
    assert seen[0].previous is None
    # SQLite reads naive UTC timestamps; the create result retains its UTC timezone.
    snapshots = [seen[0].saved.model_dump(), persisted[0].model_dump()]
    for snapshot in snapshots:
        snapshot["created_at"] = snapshot["created_at"].replace(tzinfo=None)
        snapshot["updated_at"] = snapshot["updated_at"].replace(tzinfo=None)
    assert snapshots[0] == snapshots[1]
    assert seen[0].saved.id == created.memory.id
    assert seen[0].saved.linked_memory_ids == [neighbor.id]
    assert [(match.id, match.similarity) for match in seen[0].similar_memories] == [
        (neighbor.id, pytest.approx(1.0)),
    ]
    assert created.memory.tags == []
    assert created.memory.linked_memory_ids == [neighbor.id]
    assert created.similar_memories[0].tags == ["original"]
    assert (await service.get_memory(user_id, neighbor.id)).tags == ["original"]
    assert events[0].snapshot["tags"] == []


@pytest.mark.parametrize("mode", ["warn", "enforce"])
@pytest.mark.parametrize("failure", ["error", "timeout", "reject", "mutated"])
async def test_after_failure_warns_without_failing_saved_create(write_store, mode, failure, caplog):
    repo, user_id, _, bus = write_store
    logging.getLogger("app.services.write_plugin_service").disabled = False
    events = []

    async def after(request):
        if failure == "error":
            raise RuntimeError("SECRET memory content")
        if failure == "timeout":
            await asyncio.sleep(10)
        if failure == "reject":
            return {"outcome": "reject", "message": "SECRET memory content"}
        warning = PluginWarning(message="Valid originally")
        warning.message = " "
        return warning

    async def collect(event):
        events.append(event)

    bus.subscribe("memory.*", collect)
    plugin = MemoryPlugin(after_save={"create": after})
    service = MemoryService(
        repo, bus, WritePluginService(plugin, mode=mode, timeout_seconds=0.01),
    )

    result = await service.create_memory(user_id, candidate())
    await bus.wait_for_pending()

    assert result.plugin_warnings == [PluginWarning(
        message="Memory saved, but after-save plugin unavailable.",
        code="MEMORY_PLUGIN_AFTER_SAVE_UNAVAILABLE",
    )]
    assert (await service.get_memory(user_id, result.memory.id)).title == "A useful memory"
    assert [event.action for event in events] == ["created"]
    assert "after_save" in caplog.text
    assert "SECRET" not in caplog.text


@pytest.mark.parametrize("auto_links", [0, 5])
async def test_after_create_distinguishes_uncomputed_and_empty_similarity(
    write_store, monkeypatch, auto_links,
):
    repo, user_id, embeddings, _ = write_store
    monkeypatch.setattr(settings, "MEMORY_NUM_AUTO_LINK", auto_links)
    seen = []

    async def after(request):
        seen.append(request)

    service = MemoryService(repo, write_plugin=WritePluginService(
        MemoryPlugin(after_save={"create": after}),
    ))

    result = await service.create_memory(user_id, candidate())

    assert seen[0].similar_memories == (None if auto_links == 0 else [])
    assert result.plugin_warnings == []
    assert len(embeddings.requests) == 1


async def test_invalid_lifecycle_operations_skip_both_phases_and_preserve_ownership(write_store):
    from app.models.user_models import UserCreate
    from app.repositories.sqlite.user_repository import SqliteUserRepository
    from app.services.user_service import UserService

    repo, user_id, _, _ = write_store
    other = await UserService(SqliteUserRepository(repo.db_adapter)).get_or_create_user(
        UserCreate(external_id="other", name="Other", email="other@example.com"),
    )
    observer = MemoryService(repo)
    owned = (await observer.create_memory(user_id, candidate())).memory
    foreign = (await observer.create_memory(other.id, candidate())).memory
    seen = []

    async def check(request):
        seen.append(request)
        return WriteDecision(outcome="allow")

    async def after(request):
        seen.append(request)

    plugin = MemoryPlugin(
        before_save=dict.fromkeys(("update", "obsolete", "restore"), check),
        after_save=dict.fromkeys(("update", "obsolete", "restore"), after),
    )
    service = MemoryService(repo, write_plugin=WritePluginService(plugin))

    with pytest.raises(InvalidStateTransitionError):
        await service.unobsolete_memory(user_id, owned.id)
    for missing_id in (99999, foreign.id):
        with pytest.raises(NotFoundError):
            await service.mark_memory_obsolete(user_id, missing_id, "Old fact")
        with pytest.raises(NotFoundError):
            await service.unobsolete_memory(user_id, missing_id)
        with pytest.raises(NotFoundError):
            await service.update_memory(user_id, missing_id, MemoryUpdate(importance=8))
    with pytest.raises(NotFoundError, match="Superseding memory"):
        await service.mark_memory_obsolete(user_id, owned.id, "Old fact", foreign.id)

    assert seen == []
    assert not (await observer.get_memory(user_id, owned.id)).is_obsolete
    assert not (await observer.get_memory(other.id, foreign.id)).is_obsolete


async def test_after_create_similarity_is_scoped_to_the_current_user(write_store):
    from app.models.user_models import UserCreate
    from app.repositories.sqlite.user_repository import SqliteUserRepository
    from app.services.user_service import UserService

    repo, user_id, _, _ = write_store
    other = await UserService(SqliteUserRepository(repo.db_adapter)).get_or_create_user(
        UserCreate(external_id="other", name="Other", email="other@example.com"),
    )
    observer = MemoryService(repo)
    await observer.create_memory(other.id, candidate())
    seen = []

    async def after(request):
        seen.append(request)

    service = MemoryService(repo, write_plugin=WritePluginService(
        MemoryPlugin(after_save={"create": after}),
    ))

    created = await service.create_memory(user_id, candidate())

    assert seen[0].user_id == user_id
    assert seen[0].similar_memories == []
    assert created.memory.linked_memory_ids == []


async def test_external_cancellation_after_save_propagates_but_write_remains(write_store):
    repo, user_id, _, _ = write_store
    entered = asyncio.Event()

    async def after(request):
        entered.set()
        await asyncio.Event().wait()

    service = MemoryService(repo, write_plugin=WritePluginService(
        MemoryPlugin(after_save={"create": after}),
    ))

    task = asyncio.create_task(service.create_memory(user_id, candidate()))
    try:
        async with asyncio.timeout(5):
            await entered.wait()
    finally:
        task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    _, total = await service.list_memories(user_id)
    assert total == 1


async def test_after_update_receives_previous_and_saved_but_skips_noops(write_store):
    repo, user_id, embeddings, _ = write_store
    seen = []

    async def after(request):
        seen.append(request.model_copy(deep=True))
        request.previous.tags.append("previous mutation")
        request.saved.tags.append("saved mutation")
        return PluginWarning(message="Review the update.")

    service = MemoryService(repo, write_plugin=WritePluginService(
        MemoryPlugin(after_save={"update": after}),
    ))
    created = (await service.create_memory(user_id, candidate())).memory

    changed = await service.update_memory(user_id, created.id, MemoryUpdate(importance=8))
    noop = await service.update_memory(user_id, created.id, MemoryUpdate(importance=8))
    null = await service.update_memory(user_id, created.id, MemoryUpdate(tags=None))

    assert changed.plugin_warnings == [PluginWarning(message="Review the update.")]
    assert noop.plugin_warnings == null.plugin_warnings == []
    assert len(seen) == 1
    assert seen[0].operation == "update"
    assert seen[0].previous.importance == 7
    assert seen[0].saved.importance == 8
    assert seen[0].similar_memories is None
    assert changed.memory.tags == []
    assert len(embeddings.requests) == 1
    assert (await service.get_memory(user_id, created.id)).tags == []


@pytest.mark.parametrize("operation", ["obsolete", "restore"])
async def test_lifecycle_rejection_sees_proposed_state_and_prevents_mutation(
    write_store, operation,
):
    repo, user_id, embeddings, bus = write_store
    observer = MemoryService(repo)
    memory = (await observer.create_memory(user_id, candidate(tags=["original"]))).memory
    replacement = (await observer.create_memory(user_id, candidate(title="Replacement"))).memory
    if operation == "restore":
        await observer.mark_memory_obsolete(user_id, memory.id, "Old fact", replacement.id)
    before = await observer.get_memory(user_id, memory.id)
    seen, events = [], []

    async def check(request):
        seen.append(request.model_copy(deep=True))
        request.previous.tags.append("mutation")
        request.proposed.obsolete_reason = "mutation"
        request.submitted.reason = "mutation"
        return WriteDecision(outcome="reject", message="Keep this state.")

    async def collect(event):
        events.append(event)

    bus.subscribe("memory.*", collect)
    service = MemoryService(repo, bus, WritePluginService(
        MemoryPlugin(before_save={operation: check}),
    ))

    with pytest.raises(WritePluginRejectedError, match="Keep this state"):
        if operation == "obsolete":
            await service.mark_memory_obsolete(user_id, memory.id, "Old fact", replacement.id)
        else:
            await service.unobsolete_memory(user_id, memory.id)
    await bus.wait_for_pending()

    assert len(seen) == 1
    request = seen[0]
    assert request.operation == operation
    assert request.user_id == user_id
    assert request.previous.model_dump() == before.model_dump()
    assert request.submitted.memory_id == memory.id
    assert request.proposed.is_obsolete is (operation == "obsolete")
    assert request.proposed.obsolete_reason == ("Old fact" if operation == "obsolete" else None)
    assert request.proposed.superseded_by == (replacement.id if operation == "obsolete" else None)
    assert (await service.get_memory(user_id, memory.id)).model_dump() == before.model_dump()
    assert events == []
    assert len(embeddings.requests) == 2


@pytest.mark.parametrize("operation", ["obsolete", "restore"])
@pytest.mark.parametrize("after_fails", [False, True])
async def test_lifecycle_warnings_and_saved_snapshots(write_store, operation, after_fails):
    repo, user_id, embeddings, bus = write_store
    observer = MemoryService(repo)
    memory = (await observer.create_memory(user_id, candidate(tags=["original"]))).memory
    if operation == "restore":
        await observer.mark_memory_obsolete(user_id, memory.id, "Old fact")
    before = await observer.get_memory(user_id, memory.id)
    seen, events = [], []

    async def check(request):
        request.proposed.obsolete_reason = "Ignored mutation"
        return WriteDecision(outcome="reject", message="Consider keeping this state.")

    async def after(request):
        seen.append(request.model_copy(deep=True))
        request.saved.tags.append("Ignored mutation")
        request.previous.tags.append("Ignored previous mutation")
        if after_fails:
            raise RuntimeError("SECRET")
        return PluginWarning(message="Review this lifecycle change.")

    async def collect(event):
        events.append(event)

    bus.subscribe("memory.*", collect)
    service = MemoryService(repo, bus, WritePluginService(
        MemoryPlugin(before_save={operation: check}, after_save={operation: after}), mode="warn",
    ))

    if operation == "obsolete":
        result = await service.mark_memory_obsolete(user_id, memory.id, "Old fact")
    else:
        result = await service.unobsolete_memory(user_id, memory.id)
    await bus.wait_for_pending()

    assert result.success is True
    assert [warning.message for warning in result.plugin_warnings] == [
        "Consider keeping this state.",
        "Memory saved, but after-save plugin unavailable." if after_fails
        else "Review this lifecycle change.",
    ]
    assert seen[0].previous.model_dump() == before.model_dump()
    assert seen[0].saved.is_obsolete is (operation == "obsolete")
    assert seen[0].saved.obsolete_reason == ("Old fact" if operation == "obsolete" else None)
    assert (seen[0].saved.obsoleted_at is None) is (operation == "restore")
    assert seen[0].similar_memories is None
    saved = await service.get_memory(user_id, memory.id)
    assert saved.model_dump() == seen[0].saved.model_dump()
    assert [event.action for event in events] == [
        "deleted" if operation == "obsolete" else "updated",
    ]
    assert len(embeddings.requests) == 1


@pytest.mark.parametrize("operation", ["obsolete", "restore"])
async def test_lifecycle_wait_preserves_concurrent_edits_and_refreshes_previous(
    write_store, operation,
):
    repo, user_id, _, _ = write_store
    observer = MemoryService(repo)
    memory = (await observer.create_memory(user_id, candidate())).memory
    if operation == "restore":
        await observer.mark_memory_obsolete(user_id, memory.id, "Old fact")
    paused, release = asyncio.Event(), asyncio.Event()
    seen = []

    async def check(request):
        paused.set()
        await release.wait()
        return WriteDecision(outcome="allow")

    async def after(request):
        seen.append(request)

    service = MemoryService(repo, write_plugin=WritePluginService(MemoryPlugin(
        before_save={operation: check}, after_save={operation: after},
    )))

    async with asyncio.timeout(5), asyncio.TaskGroup() as tasks:
        pending = tasks.create_task(
            service.mark_memory_obsolete(user_id, memory.id, "Old fact")
            if operation == "obsolete" else service.unobsolete_memory(user_id, memory.id),
        )
        await paused.wait()
        try:
            await observer.update_memory(
                user_id, memory.id, MemoryUpdate(content="Concurrent edit"),
            )
        finally:
            release.set()

    assert pending.result().success
    assert seen[0].previous.content == "Concurrent edit"
    assert seen[0].saved.content == "Concurrent edit"
    assert (await service.get_memory(user_id, memory.id)).content == "Concurrent edit"


async def test_restore_losing_race_keeps_core_error_and_skips_after_handler(write_store):
    repo, user_id, _, _ = write_store
    observer = MemoryService(repo)
    memory = (await observer.create_memory(user_id, candidate())).memory
    await observer.mark_memory_obsolete(user_id, memory.id, "Old fact")
    seen = []

    async def check(request):
        await observer.unobsolete_memory(user_id, memory.id)
        return WriteDecision(outcome="allow")

    async def after(request):
        seen.append(request)

    service = MemoryService(repo, write_plugin=WritePluginService(MemoryPlugin(
        before_save={"restore": check}, after_save={"restore": after},
    )))

    with pytest.raises(InvalidStateTransitionError):
        await service.unobsolete_memory(user_id, memory.id)

    assert seen == []
    assert not (await service.get_memory(user_id, memory.id)).is_obsolete
