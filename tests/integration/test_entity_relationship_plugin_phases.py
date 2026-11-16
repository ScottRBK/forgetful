"""Entity Relationship Plugin phases through EntityService and isolated SQLite."""

import asyncio
import logging

import pytest

from app.exceptions import (
    NotFoundError,
    WritePluginRejectedError,
    WritePluginUnavailableError,
)
from app.models.entity_models import (
    EntityCreate,
    EntityRelationshipCreate,
    EntityRelationshipUpdate,
    EntityType,
)
from app.models.write_plugin_models import PluginWarning, WriteDecision
from app.protocols.write_plugin_protocol import EntityRelationshipPlugin
from app.services.entity_relationship_plugin_service import (
    EntityRelationshipPluginService,
)
from app.services.entity_service import EntityService


def relationship_service(repo, mode="enforce", timeout_seconds=5.0, **phases):
    plugin = EntityRelationshipPlugin(**phases)
    return EntityService(repo, relationship_plugin=EntityRelationshipPluginService(
        plugin, mode=mode, timeout_seconds=timeout_seconds,
    ))


async def endpoints(repo, user_id):
    service = EntityService(repo)
    person = (await service.create_entity(user_id, EntityCreate(
        name="Synthetic Person", entity_type=EntityType.INDIVIDUAL,
    ))).entity
    org = (await service.create_entity(user_id, EntityCreate(
        name="Synthetic Org", entity_type=EntityType.ORGANIZATION,
    ))).entity
    return person, org


def candidate(person, org, **changes):
    return EntityRelationshipCreate(**({
        "source_entity_id": person.id, "target_entity_id": org.id,
        "relationship_type": "works_for", "strength": 0.5,
    } | changes))


async def test_no_plugin_returns_empty_warnings(entity_store):
    repo, user_id, _ = entity_store
    person, org = await endpoints(repo, user_id)
    service = EntityService(repo)

    created = await service.create_entity_relationship(user_id, candidate(person, org))
    updated = await service.update_entity_relationship(
        user_id, created.relationship.id, EntityRelationshipUpdate(strength=0.7),
    )
    deleted = await service.delete_entity_relationship(user_id, created.relationship.id)

    assert created.plugin_warnings == updated.plugin_warnings == deleted.plugin_warnings == []
    assert updated.relationship.strength == 0.7
    assert deleted.deleted is True


async def test_unregistered_operation_does_not_call_handlers(entity_store):
    repo, user_id, _ = entity_store
    person, org = await endpoints(repo, user_id)
    calls = []

    async def handler(request):
        calls.append(request.operation)
        return WriteDecision(outcome="reject", message="Updates are frozen.")

    service = relationship_service(repo, before_save={"update": handler})
    created = await service.create_entity_relationship(user_id, candidate(person, org))
    assert (await service.delete_entity_relationship(user_id, created.relationship.id)).deleted
    assert calls == []


@pytest.mark.parametrize("mode", ["warn", "enforce"])
async def test_before_warn_returns_warning_and_persists(entity_store, mode):
    repo, user_id, _ = entity_store
    person, org = await endpoints(repo, user_id)

    async def before(request):
        return WriteDecision(outcome="warn", message="Check the relationship.", code="rel")

    service = relationship_service(repo, mode=mode, before_save={"create": before})
    result = await service.create_entity_relationship(user_id, candidate(person, org))

    assert result.plugin_warnings == [
        PluginWarning(message="Check the relationship.", code="rel"),
    ]
    assert await repo.get_entity_relationship_by_id(user_id, result.relationship.id)


async def test_warn_mode_downgrades_reject_and_persists(entity_store):
    repo, user_id, _ = entity_store
    person, org = await endpoints(repo, user_id)

    async def before(request):
        return WriteDecision(outcome="reject", message="Relationship type not allowed.")

    service = relationship_service(repo, mode="warn", before_save={"create": before})
    result = await service.create_entity_relationship(user_id, candidate(person, org))

    assert result.plugin_warnings[0].outcome == "warn"
    assert result.plugin_warnings[0].message == "Relationship type not allowed."


@pytest.mark.parametrize("mode", ["warn", "enforce"])
@pytest.mark.parametrize("failure", ["error", "timeout", "malformed"])
async def test_before_unavailable_is_generic_and_mode_controls_persistence(
    entity_store, mode, failure, caplog,
):
    repo, user_id, _ = entity_store
    person, org = await endpoints(repo, user_id)
    logging.getLogger("app.services.entity_relationship_plugin_service").disabled = False

    async def before(request):
        if failure == "error":
            raise RuntimeError("SECRET relationship metadata")
        if failure == "timeout":
            await asyncio.sleep(10)
        return {"outcome": "invalid", "message": "SECRET relationship metadata"}

    service = relationship_service(
        repo, mode=mode, timeout_seconds=0.01, before_save={"create": before},
    )
    if mode == "enforce":
        with pytest.raises(
            WritePluginUnavailableError, match=r"^Entity Relationship Plugin unavailable\.$",
        ):
            await service.create_entity_relationship(user_id, candidate(person, org))
    else:
        result = await service.create_entity_relationship(user_id, candidate(person, org))
        assert result.plugin_warnings == [PluginWarning(
            message="Entity Relationship Plugin unavailable.", code="WRITE_PLUGIN_UNAVAILABLE",
        )]
    stored = await repo.get_all_entity_relationships(user_id)
    assert len(stored) == (1 if mode == "warn" else 0)
    assert "phase=before_save" in caplog.text
    assert "SECRET" not in caplog.text


@pytest.mark.parametrize("operation", ["create", "update", "delete"])
@pytest.mark.parametrize("failure", ["error", "timeout", "reject", "cancelled_child"])
async def test_after_failure_warns_without_failing_completed_write(
    entity_store, operation, failure, caplog,
):
    repo, user_id, _ = entity_store
    person, org = await endpoints(repo, user_id)
    logging.getLogger("app.services.entity_relationship_plugin_service").disabled = False
    existing = (await EntityService(repo).create_entity_relationship(
        user_id, candidate(person, org),
    )).relationship

    async def after(request):
        if failure == "error":
            raise RuntimeError("SECRET relationship metadata")
        if failure == "timeout":
            await asyncio.sleep(10)
        if failure == "reject":
            return {"outcome": "reject", "message": "SECRET relationship metadata"}
        child = asyncio.create_task(asyncio.sleep(10))
        child.cancel("SECRET relationship metadata")
        await child

    service = relationship_service(
        repo, timeout_seconds=0.01 if failure == "timeout" else 5,
        after_save={operation: after},
    )
    if operation == "create":
        result = await service.create_entity_relationship(
            user_id, candidate(person, org, relationship_type="advises"),
        )
        assert await repo.get_entity_relationship_by_id(user_id, result.relationship.id)
    elif operation == "update":
        result = await service.update_entity_relationship(
            user_id, existing.id, EntityRelationshipUpdate(strength=0.9),
        )
        assert (await repo.get_entity_relationship_by_id(user_id, existing.id)).strength == 0.9
    else:
        result = await service.delete_entity_relationship(user_id, existing.id)
        assert result.deleted is True
        assert await repo.get_entity_relationship_by_id(user_id, existing.id) is None

    verb = "deleted" if operation == "delete" else "saved"
    assert result.plugin_warnings == [PluginWarning(
        message=f"Entity relationship {verb}, but after-save plugin unavailable.",
        code="ENTITY_RELATIONSHIP_PLUGIN_AFTER_SAVE_UNAVAILABLE",
    )]
    assert "phase=after_save" in caplog.text
    assert "SECRET" not in caplog.text


async def test_detached_snapshots_survive_handler_mutation(entity_store):
    repo, user_id, _ = entity_store
    person, org = await endpoints(repo, user_id)
    seen = []

    async def before(request):
        seen.append(request.model_copy(deep=True))
        request.proposed.relationship_type = "mutated"
        request.source.name = "mutated"
        return WriteDecision(outcome="allow")

    async def after(request):
        request.saved.relationship_type = "mutated"
        return None

    service = relationship_service(
        repo, before_save={"create": before}, after_save={"create": after},
    )
    result = await service.create_entity_relationship(user_id, candidate(person, org))

    assert seen[0].proposed.relationship_type == "works_for"
    assert result.relationship.relationship_type == "works_for"
    stored = await repo.get_entity_relationship_by_id(user_id, result.relationship.id)
    assert stored.relationship_type == "works_for"
    assert (await repo.get_entity_by_id(user_id, person.id)).name == "Synthetic Person"


async def test_update_refreshes_previous_after_before_wait(entity_store):
    repo, user_id, _ = entity_store
    person, org = await endpoints(repo, user_id)
    observer = EntityService(repo)
    existing = (await observer.create_entity_relationship(
        user_id, candidate(person, org),
    )).relationship
    paused, release = asyncio.Event(), asyncio.Event()
    after_seen = []

    async def before(request):
        paused.set()
        await release.wait()
        return WriteDecision(outcome="allow")

    async def after(request):
        after_seen.append(request)
        return None

    service = relationship_service(
        repo, before_save={"update": before}, after_save={"update": after},
    )
    async with asyncio.timeout(5), asyncio.TaskGroup() as tasks:
        pending = tasks.create_task(service.update_entity_relationship(
            user_id, existing.id, EntityRelationshipUpdate(strength=0.9),
        ))
        await paused.wait()
        try:
            await observer.update_entity_relationship(
                user_id, existing.id, EntityRelationshipUpdate(confidence=0.4),
            )
        finally:
            release.set()

    assert pending.result().relationship.strength == 0.9
    assert pending.result().relationship.confidence == 0.4
    assert after_seen[0].previous.confidence == 0.4


@pytest.mark.parametrize("operation", ["update", "delete"])
async def test_relationship_removed_during_before_wait(entity_store, operation):
    repo, user_id, _ = entity_store
    person, org = await endpoints(repo, user_id)
    observer = EntityService(repo)
    existing = (await observer.create_entity_relationship(
        user_id, candidate(person, org),
    )).relationship
    after_calls = []

    async def before(request):
        await observer.delete_entity_relationship(user_id, existing.id)
        return WriteDecision(outcome="warn", message="Check the relationship.")

    async def after(request):
        after_calls.append(request)
        return None

    service = relationship_service(
        repo, before_save={operation: before}, after_save={operation: after},
    )
    if operation == "update":
        with pytest.raises(NotFoundError):
            await service.update_entity_relationship(
                user_id, existing.id, EntityRelationshipUpdate(strength=0.9),
            )
    else:
        result = await service.delete_entity_relationship(user_id, existing.id)
        assert result.deleted is False
        assert result.plugin_warnings[0].message == "Check the relationship."
    assert after_calls == []


async def test_endpoint_removed_during_create_wait_keeps_persistence_checks(entity_store):
    repo, user_id, _ = entity_store
    person, org = await endpoints(repo, user_id)
    observer = EntityService(repo)

    async def before(request):
        await observer.delete_entity(user_id, org.id)
        return WriteDecision(outcome="allow")

    service = relationship_service(repo, before_save={"create": before})
    with pytest.raises(NotFoundError, match="Target entity"):
        await service.create_entity_relationship(user_id, candidate(person, org))
    assert await repo.get_all_entity_relationships(user_id) == []


async def test_external_cancellation_after_save_propagates_but_write_remains(entity_store):
    repo, user_id, _ = entity_store
    person, org = await endpoints(repo, user_id)
    entered = asyncio.Event()

    async def after(request):
        entered.set()
        await asyncio.Event().wait()

    service = relationship_service(repo, after_save={"create": after})
    task = asyncio.create_task(
        service.create_entity_relationship(user_id, candidate(person, org)),
    )
    try:
        async with asyncio.timeout(5):
            await entered.wait()
    finally:
        task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert len(await repo.get_all_entity_relationships(user_id)) == 1


async def test_before_cancellation_propagates_in_warn_mode(entity_store):
    repo, user_id, _ = entity_store
    person, org = await endpoints(repo, user_id)

    async def before(request):
        raise asyncio.CancelledError()

    service = relationship_service(repo, mode="warn", before_save={"create": before})
    with pytest.raises(asyncio.CancelledError):
        await service.create_entity_relationship(user_id, candidate(person, org))
    assert await repo.get_all_entity_relationships(user_id) == []


async def test_reject_in_enforce_mode_blocks_create(entity_store):
    repo, user_id, _ = entity_store
    person, org = await endpoints(repo, user_id)

    async def before(request):
        if request.target.entity_type != EntityType.ORGANIZATION:
            return WriteDecision(outcome="reject", message="works_for must target an Organization.")
        return WriteDecision(outcome="allow")

    service = relationship_service(repo, before_save={"create": before})
    await service.create_entity_relationship(user_id, candidate(person, org))
    with pytest.raises(WritePluginRejectedError, match="must target an Organization"):
        await service.create_entity_relationship(
            user_id, candidate(org, person, relationship_type="works_for"),
        )
    assert len(await repo.get_all_entity_relationships(user_id)) == 1


@pytest.mark.parametrize(("phases", "message"), [
    ({"before_save": {"link": None}}, "unsupported entity-relationship operation"),
    ({"after_save": {"create": lambda request: None}}, "handlers must be async functions"),
    ({"before_save": [("create", None)]}, "operation-to-handler mapping"),
])
def test_invalid_registration_is_rejected(phases, message):
    with pytest.raises(ValueError, match=message):
        EntityRelationshipPlugin(**phases)
