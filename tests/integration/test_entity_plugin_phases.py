"""Entity Plugin phases through EntityService and isolated SQLite."""

import asyncio
import logging

import pytest
from entity_plugin_helpers import candidate

from app.exceptions import (
    NotFoundError,
    WritePluginRejectedError,
    WritePluginUnavailableError,
)
from app.models.entity_models import EntityUpdate
from app.models.write_plugin_models import PluginWarning, WriteDecision
from app.protocols.write_plugin_protocol import EntityPlugin
from app.services.entity_service import EntityService
from app.services.entity_write_plugin_service import EntityWritePluginService


async def test_no_plugin_returns_empty_warnings(entity_store):
    repo, user_id, _ = entity_store
    service = EntityService(repo)
    result = await service.create_entity(user_id, candidate())
    assert result.plugin_warnings == []
    assert result.entity.name == "Acme Corp"


async def test_before_reject_blocks_create(entity_store):
    repo, user_id, _ = entity_store

    async def before(request):
        if "blocked" in request.proposed.tags:
            return WriteDecision(outcome="reject", message="Remove the blocked tag.")
        return WriteDecision(outcome="allow")

    service = EntityService(
        repo, write_plugin=EntityWritePluginService(EntityPlugin(before_save={"create": before})),
    )
    await service.create_entity(user_id, candidate())
    with pytest.raises(WritePluginRejectedError, match="Remove the blocked tag"):
        await service.create_entity(user_id, candidate(tags=["blocked"]))


@pytest.mark.parametrize("mode", ["warn", "enforce"])
@pytest.mark.parametrize("failure", ["error", "timeout", "reject", "mutated", "cancelled_child"])
async def test_after_failure_warns_without_failing_saved_create(entity_store, mode, failure, caplog):
    repo, user_id, _ = entity_store
    logging.getLogger("app.services.entity_write_plugin_service").disabled = False

    async def after(request):
        if failure == "error":
            raise RuntimeError("SECRET entity content")
        if failure == "timeout":
            await asyncio.sleep(10)
        if failure == "reject":
            return {"outcome": "reject", "message": "SECRET entity content"}
        if failure == "cancelled_child":
            child = asyncio.create_task(asyncio.sleep(10))
            child.cancel("SECRET entity content")
            await child
        warning = PluginWarning(message="Valid originally")
        warning.message = " "
        return warning

    service = EntityService(
        repo, write_plugin=EntityWritePluginService(
            EntityPlugin(after_save={"create": after}),
            mode=mode, timeout_seconds=0.01 if failure == "timeout" else 5,
        ),
    )
    result = await service.create_entity(user_id, candidate())
    assert result.plugin_warnings == [PluginWarning(
        message="Entity saved, but after-save plugin unavailable.",
        code="ENTITY_PLUGIN_AFTER_SAVE_UNAVAILABLE",
    )]
    assert (await service.get_entity(user_id, result.entity.id)).name == "Acme Corp"
    assert "after_save" in caplog.text
    if failure == "cancelled_child":
        assert "error_type=CancelledError" in caplog.text
    assert "SECRET" not in caplog.text


async def test_detached_snapshots_survive_handler_mutation(entity_store):
    repo, user_id, _ = entity_store
    seen = []

    async def before(request):
        seen.append(request.model_copy(deep=True))
        if request.proposed is not None:
            request.proposed.name = "mutated"
        return WriteDecision(outcome="allow")

    service = EntityService(
        repo, write_plugin=EntityWritePluginService(EntityPlugin(before_save={"create": before})),
    )
    result = await service.create_entity(user_id, candidate())
    assert seen[0].proposed.name == "Acme Corp"
    assert result.entity.name == "Acme Corp"


async def test_noop_update_skips_plugin(entity_store):
    repo, user_id, _ = entity_store
    calls = []

    async def before(request):
        calls.append(request)
        return WriteDecision(outcome="allow")

    service = EntityService(
        repo, write_plugin=EntityWritePluginService(EntityPlugin(before_save={"update": before})),
    )
    created = (await service.create_entity(user_id, candidate(notes="same"))).entity
    await service.update_entity(user_id, created.id, EntityUpdate(notes="same"))
    await service.update_entity(user_id, created.id, EntityUpdate(notes="same"))
    assert calls == []


async def test_delete_missing_skips_plugin(entity_store):
    repo, user_id, _ = entity_store
    calls = []

    async def before(request):
        calls.append(request)
        return WriteDecision(outcome="allow")

    service = EntityService(
        repo, write_plugin=EntityWritePluginService(EntityPlugin(before_save={"delete": before})),
    )
    result = await service.delete_entity(user_id, 99999)
    assert result.deleted is False
    assert result.plugin_warnings == []
    assert calls == []


async def test_delete_after_receives_previous_not_saved_object(entity_store):
    repo, user_id, _ = entity_store
    seen = []

    async def after(request):
        seen.append(request)
        assert request.deleted_entity_id == created_id
        assert request.previous.name == "Acme Corp"
        return None

    service = EntityService(
        repo, write_plugin=EntityWritePluginService(EntityPlugin(after_save={"delete": after})),
    )
    created_id = (await service.create_entity(user_id, candidate())).entity.id
    result = await service.delete_entity(user_id, created_id)
    assert result.deleted is True
    assert len(seen) == 1


async def test_update_not_found_raises(entity_store):
    repo, user_id, _ = entity_store
    service = EntityService(repo)
    with pytest.raises(NotFoundError):
        await service.update_entity(user_id, 99999, EntityUpdate(notes="nope"))


@pytest.mark.parametrize("mode", ["warn", "enforce"])
async def test_before_warn_returns_warning_and_persists(entity_store, mode):
    repo, user_id, bus = entity_store
    events = []

    async def collect(event):
        events.append(event)

    bus.subscribe("entity.*", collect)

    async def before(request):
        return WriteDecision(outcome="warn", message="Check the source.", code="source")

    service = EntityService(
        repo, bus, EntityWritePluginService(
            EntityPlugin(before_save={"create": before}), mode=mode,
        ),
    )
    result = await service.create_entity(user_id, candidate())
    assert result.plugin_warnings[0].message == "Check the source."
    saved = await service.get_entity(user_id, result.entity.id)
    assert "plugin_warnings" not in saved.model_dump()
    await bus.wait_for_pending()
    assert len(events) == 1
    assert "plugin_warnings" not in events[0].snapshot


async def test_warn_mode_downgrades_reject_and_persists(entity_store):
    repo, user_id, _ = entity_store

    async def before(request):
        return WriteDecision(outcome="reject", message="Check the source.", code="source")

    service = EntityService(
        repo, write_plugin=EntityWritePluginService(
            EntityPlugin(before_save={"create": before}), mode="warn",
        ),
    )
    result = await service.create_entity(user_id, candidate())
    assert result.plugin_warnings[0].outcome == "warn"
    assert result.plugin_warnings[0].code == "source"
    _, total = await service.list_entities(user_id)
    assert total == 1


@pytest.mark.parametrize("mode", ["warn", "enforce"])
@pytest.mark.parametrize("failure", ["error", "bad_result", "blank", "mutated", "timeout"])
async def test_before_unavailable_is_generic_and_mode_controls_persistence(
    entity_store, mode, failure, caplog,
):
    repo, user_id, _ = entity_store
    logging.getLogger("app.services.entity_write_plugin_service").disabled = False

    async def before(request):
        if failure == "error":
            raise RuntimeError("SECRET entity content")
        if failure == "timeout":
            await asyncio.sleep(10)
        if failure == "blank":
            return {"outcome": "reject", "message": "  "}
        if failure == "mutated":
            decision = WriteDecision(outcome="allow")
            decision.outcome = "invalid"
            return decision
        return {"outcome": "invalid", "message": "SECRET entity content"}

    service = EntityService(
        repo, write_plugin=EntityWritePluginService(
            EntityPlugin(before_save={"create": before}),
            mode=mode, timeout_seconds=0.01,
        ),
    )
    if mode == "enforce":
        with pytest.raises(
            WritePluginUnavailableError, match=r"^Entity Write Plugin unavailable\.$",
        ):
            await service.create_entity(user_id, candidate())
    else:
        result = await service.create_entity(user_id, candidate())
        assert result.plugin_warnings[0].message == "Entity Write Plugin unavailable."
        assert result.plugin_warnings[0].code == "WRITE_PLUGIN_UNAVAILABLE"
    _, total = await service.list_entities(user_id)
    assert total == (1 if mode == "warn" else 0)
    assert "Entity Write Plugin" in caplog.text
    assert "SECRET" not in caplog.text


async def test_unregistered_operation_runs_without_warnings(entity_store):
    repo, user_id, _ = entity_store
    calls = []

    async def before(request):
        calls.append(request)
        return WriteDecision(outcome="allow")

    service = EntityService(
        repo, write_plugin=EntityWritePluginService(
            EntityPlugin(before_save={"create": before}),
        ),
    )
    created = (await service.create_entity(user_id, candidate())).entity
    updated = await service.update_entity(user_id, created.id, EntityUpdate(notes="changed"))
    assert updated.plugin_warnings == []
    assert calls == [calls[0]]
    assert calls[0].operation == "create"


async def test_update_rejection_leaves_entity_unchanged(entity_store):
    repo, user_id, _ = entity_store

    async def check(request):
        if request.proposed and "blocked" in request.proposed.tags:
            return WriteDecision(outcome="reject", message="Remove the blocked tag.")
        return WriteDecision(outcome="allow")

    service = EntityService(
        repo, write_plugin=EntityWritePluginService(
            EntityPlugin(before_save={"create": check, "update": check}),
        ),
    )
    created = (await service.create_entity(user_id, candidate())).entity
    before = await service.get_entity(user_id, created.id)
    with pytest.raises(WritePluginRejectedError, match="Remove the blocked tag"):
        await service.update_entity(user_id, created.id, EntityUpdate(tags=["blocked"]))
    assert (await service.get_entity(user_id, created.id)).model_dump() == before.model_dump()


async def test_delete_rejection_leaves_entity_unchanged(entity_store):
    repo, user_id, _ = entity_store

    async def check(request):
        if request.operation == "delete":
            return WriteDecision(outcome="reject", message="Keep this entity.")
        return WriteDecision(outcome="allow")

    service = EntityService(
        repo, write_plugin=EntityWritePluginService(
            EntityPlugin(before_save={"create": check, "delete": check}),
        ),
    )
    created = (await service.create_entity(user_id, candidate())).entity
    with pytest.raises(WritePluginRejectedError, match="Keep this entity"):
        await service.delete_entity(user_id, created.id)
    assert (await service.get_entity(user_id, created.id)).id == created.id


async def test_before_handler_sees_caller_user_id_and_isolates_other_users(entity_store):
    from app.models.user_models import UserCreate
    from app.repositories.sqlite.user_repository import SqliteUserRepository
    from app.services.user_service import UserService

    repo, user_id, _ = entity_store
    other = await UserService(SqliteUserRepository(repo.db_adapter)).get_or_create_user(
        UserCreate(external_id="other-entity", name="Other", email="other-entity@example.com"),
    )
    observer = EntityService(repo)
    foreign = (await observer.create_entity(other.id, candidate())).entity
    seen = []

    async def before(request):
        seen.append(request)
        return WriteDecision(outcome="allow")

    service = EntityService(
        repo, write_plugin=EntityWritePluginService(EntityPlugin(before_save={"create": before})),
    )
    await service.create_entity(user_id, candidate())
    assert len(seen) == 1
    assert seen[0].user_id == user_id
    assert (await observer.get_entity(other.id, foreign.id)).id == foreign.id


async def test_external_cancellation_after_save_propagates_but_write_remains(entity_store):
    repo, user_id, _ = entity_store
    entered = asyncio.Event()

    async def after(request):
        entered.set()
        await asyncio.Event().wait()

    service = EntityService(
        repo, write_plugin=EntityWritePluginService(
            EntityPlugin(after_save={"create": after}),
        ),
    )
    task = asyncio.create_task(service.create_entity(user_id, candidate()))
    try:
        async with asyncio.timeout(5):
            await entered.wait()
    finally:
        task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    _, total = await service.list_entities(user_id)
    assert total == 1


async def test_before_cancellation_propagates_in_warn_mode(entity_store):
    repo, user_id, _ = entity_store

    async def before(request):
        if request.proposed and "cancel" in request.proposed.tags:
            raise asyncio.CancelledError()
        return WriteDecision(outcome="reject", message="Check the source.", code="source")

    service = EntityService(
        repo, write_plugin=EntityWritePluginService(
            EntityPlugin(before_save={"create": before}), mode="warn",
        ),
    )
    await service.create_entity(user_id, candidate())
    with pytest.raises(asyncio.CancelledError):
        await service.create_entity(user_id, candidate(tags=["cancel"]))
    _, total = await service.list_entities(user_id)
    assert total == 1

