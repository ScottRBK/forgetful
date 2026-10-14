"""Integration tests for unobsolete_memory restore path."""
from uuid import uuid4

import pytest

from app.exceptions import InvalidStateTransitionError, NotFoundError
from app.models.activity_models import ActionType, EntityType
from app.models.memory_models import MemoryCreate, MemoryQueryRequest


@pytest.mark.asyncio
async def test_unobsolete_restores_query_visibility_and_clears_fields(test_memory_service):
    user_id = uuid4()
    mem_data = MemoryCreate(
        title="Restore me unique-title-ff86",
        content="Memory to obsolete then restore",
        context="unobsolete test",
        keywords=["restore", "ff86"],
        tags=["stub"],
        importance=5,
    )
    mem, _ = await test_memory_service.create_memory(user_id=user_id, memory_data=mem_data)
    await test_memory_service.mark_memory_obsolete(
        user_id=user_id,
        memory_id=mem.id,
        reason="test obsolete",
        superseded_by=None,
    )

    before = await test_memory_service.query_memory(
        user_id=user_id,
        memory_query=MemoryQueryRequest(
            query="unique-title-ff86",
            query_context="unobsolete visibility check",
            k=5,
        ),
    )
    assert all(m.id != mem.id for m in before.primary_memories)

    ok = await test_memory_service.unobsolete_memory(user_id=user_id, memory_id=mem.id)
    assert ok is True

    refreshed = await test_memory_service.get_memory(user_id=user_id, memory_id=mem.id)
    assert refreshed is not None
    assert refreshed.is_obsolete is False
    assert refreshed.obsolete_reason is None
    assert refreshed.superseded_by is None
    assert refreshed.obsoleted_at is None

    after = await test_memory_service.query_memory(
        user_id=user_id,
        memory_query=MemoryQueryRequest(
            query="unique-title-ff86",
            query_context="unobsolete visibility check",
            k=5,
        ),
    )
    assert any(m.id == mem.id for m in after.primary_memories)


@pytest.mark.asyncio
async def test_unobsolete_emits_updated_activity_event(test_memory_service_with_event_bus):
    service, event_bus = test_memory_service_with_event_bus
    user_id = uuid4()
    mem_data = MemoryCreate(
        title="Audit restore event",
        content="Obsolete then restore for activity trail",
        context="unobsolete audit test",
        keywords=["audit", "restore"],
        tags=["stub"],
        importance=5,
    )
    mem, _ = await service.create_memory(user_id=user_id, memory_data=mem_data)
    await service.mark_memory_obsolete(
        user_id=user_id,
        memory_id=mem.id,
        reason="audit obsolete",
        superseded_by=None,
    )
    event_bus.collected_events.clear()

    ok = await service.unobsolete_memory(user_id=user_id, memory_id=mem.id)
    assert ok is True

    assert len(event_bus.collected_events) == 1
    event = event_bus.collected_events[0]
    assert event.entity_type == EntityType.MEMORY
    assert event.entity_id == mem.id
    assert event.action == ActionType.UPDATED
    assert event.snapshot["is_obsolete"] is False


@pytest.mark.asyncio
async def test_unobsolete_unknown_id_raises_not_found(test_memory_service):
    user_id = uuid4()
    with pytest.raises(NotFoundError):
        await test_memory_service.unobsolete_memory(user_id=user_id, memory_id=999_999)


@pytest.mark.asyncio
async def test_unobsolete_active_memory_raises_invalid_state_transition(test_memory_service):
    user_id = uuid4()
    mem_data = MemoryCreate(
        title="Still active",
        content="Never obsolete",
        context="unobsolete negative test",
        keywords=["active"],
        tags=["stub"],
        importance=5,
    )
    mem, _ = await test_memory_service.create_memory(user_id=user_id, memory_data=mem_data)

    with pytest.raises(InvalidStateTransitionError, match="is not obsolete"):
        await test_memory_service.unobsolete_memory(user_id=user_id, memory_id=mem.id)
