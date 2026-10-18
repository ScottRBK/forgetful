"""Integration tests for mark_memory_obsolete state validation (stubbed repository)."""
from uuid import uuid4

import pytest

from app.exceptions import InvalidStateTransitionError
from app.models.activity_models import ActionType
from app.models.memory_models import MemoryCreate


def _memory_data(title: str) -> MemoryCreate:
    return MemoryCreate(
        title=title,
        content=f"Content for {title}",
        context="obsolete state validation",
        keywords=["obsolete"],
        tags=["stub"],
        importance=5,
    )


@pytest.mark.asyncio
async def test_self_supersede_is_rejected_and_leaves_memory_active(test_memory_service_with_event_bus):
    service, event_bus = test_memory_service_with_event_bus
    user_id = uuid4()
    memory = (await service.create_memory(user_id=user_id, memory_data=_memory_data("Self reference"))).memory
    event_bus.collected_events.clear()

    with pytest.raises(InvalidStateTransitionError, match="cannot be superseded by itself"):
        await service.mark_memory_obsolete(
            user_id=user_id,
            memory_id=memory.id,
            reason="r",
            superseded_by=memory.id,
        )

    stored = await service.get_memory(user_id=user_id, memory_id=memory.id)
    assert stored.is_obsolete is False
    assert stored.superseded_by is None
    assert event_bus.collected_events == []


@pytest.mark.asyncio
async def test_obsoleting_an_obsolete_memory_is_rejected_and_keeps_audit_trail(test_memory_service_with_event_bus):
    service, event_bus = test_memory_service_with_event_bus
    user_id = uuid4()
    memory = (await service.create_memory(user_id=user_id, memory_data=_memory_data("Obsolete twice"))).memory
    replacement = (await service.create_memory(user_id=user_id, memory_data=_memory_data("Replacement"))).memory
    await service.mark_memory_obsolete(user_id=user_id, memory_id=memory.id, reason="first", superseded_by=None)
    first = await service.get_memory(user_id=user_id, memory_id=memory.id)
    event_bus.collected_events.clear()

    with pytest.raises(InvalidStateTransitionError, match="already obsolete"):
        await service.mark_memory_obsolete(
            user_id=user_id,
            memory_id=memory.id,
            reason="second",
            superseded_by=replacement.id,
        )

    after = await service.get_memory(user_id=user_id, memory_id=memory.id)
    assert after.obsolete_reason == "first"
    assert after.obsoleted_at == first.obsoleted_at
    assert after.superseded_by is None
    assert event_bus.collected_events == []


@pytest.mark.asyncio
async def test_restored_memory_can_be_obsoleted_again(test_memory_service_with_event_bus):
    service, event_bus = test_memory_service_with_event_bus
    user_id = uuid4()
    memory = (await service.create_memory(user_id=user_id, memory_data=_memory_data("Round trip"))).memory
    await service.mark_memory_obsolete(user_id=user_id, memory_id=memory.id, reason="first")
    await service.unobsolete_memory(user_id=user_id, memory_id=memory.id)
    event_bus.collected_events.clear()

    assert await service.mark_memory_obsolete(user_id=user_id, memory_id=memory.id, reason="second") is True

    stored = await service.get_memory(user_id=user_id, memory_id=memory.id)
    assert stored.obsolete_reason == "second"
    assert [e.action for e in event_bus.collected_events] == [ActionType.DELETED]
