"""Integration tests: EntityService.update_entity validates the merged state

An update is a PATCH, so the entity_type / custom_type pair that gets stored is
the combination of the payload and the stored entity. These tests pin the
invariant "custom_type is set if and only if entity_type is Other" for updates,
the same way EntityCreate already does for creates.
"""
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.models.activity_models import ActionType
from app.models.entity_models import (
    EntityCreate,
    EntitySummary,
    EntityType,
    EntityUpdate,
)


async def _create_other(service, user_id):
    return await service.create_entity(
        user_id,
        EntityCreate(
            name="Message Queue",
            entity_type=EntityType.OTHER,
            custom_type="Middleware",
        ),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("cleared", ["", None])
async def test_update_rejects_clearing_custom_type_of_other_entity(
    test_entity_service, cleared,
):
    user_id = uuid4()
    entity = await _create_other(test_entity_service, user_id)

    with pytest.raises(ValueError, match="custom_type is required"):
        await test_entity_service.update_entity(
            user_id, entity.id, EntityUpdate(custom_type=cleared),
        )

    # Nothing was written: the entity is still readable and unchanged
    stored = await test_entity_service.get_entity(user_id, entity.id)
    assert stored.entity_type == EntityType.OTHER
    assert stored.custom_type == "Middleware"


@pytest.mark.asyncio
async def test_rejected_update_emits_no_event(test_entity_service_with_event_bus):
    service, event_bus = test_entity_service_with_event_bus
    user_id = uuid4()
    entity = await _create_other(service, user_id)
    event_bus.collected_events.clear()

    with pytest.raises(ValueError, match="custom_type is required"):
        await service.update_entity(user_id, entity.id, EntityUpdate(custom_type=""))

    assert event_bus.collected_events == []


@pytest.mark.asyncio
async def test_update_can_still_change_custom_type_of_other_entity(test_entity_service):
    user_id = uuid4()
    entity = await _create_other(test_entity_service, user_id)

    updated = await test_entity_service.update_entity(
        user_id, entity.id, EntityUpdate(custom_type="Broker"),
    )

    assert updated.entity_type == EntityType.OTHER
    assert updated.custom_type == "Broker"


@pytest.mark.asyncio
async def test_update_unrelated_field_keeps_custom_type_of_other_entity(test_entity_service):
    user_id = uuid4()
    entity = await _create_other(test_entity_service, user_id)

    updated = await test_entity_service.update_entity(
        user_id, entity.id, EntityUpdate(notes="Runs on the shared cluster"),
    )

    assert updated.custom_type == "Middleware"
    summaries = await test_entity_service.search_entities(user_id, "Message")
    assert summaries[0].custom_type == "Middleware"


@pytest.mark.asyncio
async def test_moving_away_from_other_clears_custom_type_everywhere(test_entity_service):
    user_id = uuid4()
    entity = await _create_other(test_entity_service, user_id)

    await test_entity_service.update_entity(
        user_id, entity.id, EntityUpdate(entity_type=EntityType.ORGANIZATION),
    )

    stored = await test_entity_service.get_entity(user_id, entity.id)
    listed, _ = await test_entity_service.list_entities(user_id)
    searched = await test_entity_service.search_entities(user_id, "Message")
    # What the repository was asked to persist, not a re-validated view of it
    persisted = await test_entity_service.entity_repo.get_entity_by_id(user_id, entity.id)

    assert stored.entity_type == EntityType.ORGANIZATION
    assert stored.custom_type is None
    assert persisted.custom_type is None
    assert listed[0].custom_type is None
    assert searched[0].custom_type is None


@pytest.mark.asyncio
async def test_update_does_not_store_custom_type_for_non_other_entity(test_entity_service):
    user_id = uuid4()
    entity = await test_entity_service.create_entity(
        user_id, EntityCreate(name="Plain Team", entity_type=EntityType.INDIVIDUAL),
    )

    await test_entity_service.update_entity(
        user_id,
        entity.id,
        EntityUpdate(entity_type=EntityType.TEAM, custom_type="zzz"),
    )

    persisted = await test_entity_service.entity_repo.get_entity_by_id(user_id, entity.id)
    assert persisted.entity_type == EntityType.TEAM
    assert persisted.custom_type is None

    # A custom_type sent without a type change is dropped as well
    await test_entity_service.update_entity(
        user_id, entity.id, EntityUpdate(custom_type="yyy"),
    )
    persisted = await test_entity_service.entity_repo.get_entity_by_id(user_id, entity.id)
    assert persisted.custom_type is None


@pytest.mark.asyncio
async def test_moving_away_from_other_records_custom_type_in_update_event(
    test_entity_service_with_event_bus,
):
    service, event_bus = test_entity_service_with_event_bus
    user_id = uuid4()
    entity = await _create_other(service, user_id)
    event_bus.collected_events.clear()

    await service.update_entity(
        user_id, entity.id, EntityUpdate(entity_type=EntityType.TEAM),
    )

    updated_events = [
        e for e in event_bus.collected_events if e.action == ActionType.UPDATED
    ]
    assert len(updated_events) == 1
    assert updated_events[0].changes["custom_type"] == {"old": "Middleware", "new": None}
    assert updated_events[0].changes["entity_type"]["new"] == EntityType.TEAM


def test_entity_summary_hides_stale_custom_type_of_non_other_row():
    """Rows written before updates cleared custom_type must not leak it in lists"""
    now = datetime.now(UTC)

    stale = EntitySummary(
        id=1,
        name="Legacy",
        entity_type=EntityType.ORGANIZATION,
        custom_type="Middleware",
        tags=[],
        aka=[],
        created_at=now,
        updated_at=now,
    )
    other = EntitySummary(
        id=2,
        name="Other",
        entity_type=EntityType.OTHER,
        custom_type="Middleware",
        tags=[],
        aka=[],
        created_at=now,
        updated_at=now,
    )

    assert stale.custom_type is None
    assert other.custom_type == "Middleware"
