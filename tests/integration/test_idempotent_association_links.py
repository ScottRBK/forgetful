"""Integration tests: entity link events must reflect real link creation only.

The repository reports whether a link row was actually inserted. The service keeps its
idempotent contract (always True for an existing or new link) but must emit the
CREATED activity event only when a link was really created.
"""
from uuid import uuid4

import pytest

from app.models.activity_models import ActionType, EntityType
from app.models.entity_models import EntityCreate
from app.models.entity_models import EntityType as EntityKind


async def _make_entity(service, user_id):
    return await service.create_entity(
        user_id,
        EntityCreate(name="Acme", entity_type=EntityKind.ORGANIZATION, tags=[]),
    )


def _created(event_bus, entity_type):
    return [
        e
        for e in event_bus.collected_events
        if e.entity_type == entity_type and e.action == ActionType.CREATED
    ]


@pytest.mark.asyncio
async def test_relinking_entity_to_memory_emits_single_created_event(
    test_entity_service_with_event_bus,
):
    service, event_bus = test_entity_service_with_event_bus
    user_id = uuid4()
    entity = await _make_entity(service, user_id)

    results = [
        await service.link_entity_to_memory(user_id, entity.id, 1) for _ in range(3)
    ]

    assert results == [True, True, True]
    assert len(_created(event_bus, EntityType.ENTITY_MEMORY_LINK)) == 1


@pytest.mark.asyncio
async def test_relinking_entity_to_project_emits_single_created_event(
    test_entity_service_with_event_bus,
):
    service, event_bus = test_entity_service_with_event_bus
    user_id = uuid4()
    entity = await _make_entity(service, user_id)

    results = [
        await service.link_entity_to_project(user_id, entity.id, 1) for _ in range(3)
    ]

    assert results == [True, True, True]
    assert len(_created(event_bus, EntityType.ENTITY_PROJECT_LINK)) == 1


@pytest.mark.asyncio
async def test_link_recreated_after_unlink_emits_new_created_event(
    test_entity_service_with_event_bus,
):
    service, event_bus = test_entity_service_with_event_bus
    user_id = uuid4()
    entity = await _make_entity(service, user_id)

    await service.link_entity_to_project(user_id, entity.id, 1)
    await service.link_entity_to_project(user_id, entity.id, 1)
    assert await service.unlink_entity_from_project(user_id, entity.id, 1) is True
    assert await service.link_entity_to_project(user_id, entity.id, 1) is True

    assert len(_created(event_bus, EntityType.ENTITY_PROJECT_LINK)) == 2
