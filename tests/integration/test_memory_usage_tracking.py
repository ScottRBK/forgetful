"""Integration tests for memory usage tracking (forgetful-hulkito fork).

Covers read-side telemetry: `record_memory_access` via repository and
EventBus subscriber paths, with verification that `updated_at` is not mutated.
"""
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.config.settings import settings
from app.models.activity_models import ActionType
from app.models.memory_models import MemoryCreate, MemoryQueryRequest


@pytest.mark.asyncio
async def test_record_memory_access_does_not_mutate_updated_at(test_memory_service):
    """Access tracking must update access_count + last_accessed_at but NOT updated_at."""
    user_id = uuid4()
    mem_data = MemoryCreate(
        title="Usage stub",
        content="Memory used to test access tracking",
        context="Verifying updated_at is preserved",
        keywords=["usage", "test"],
        tags=["stub"],
        importance=5,
    )
    mem, _ = await test_memory_service.create_memory(user_id=user_id, memory_data=mem_data)
    updated_at_before = mem.updated_at

    count = await test_memory_service.memory_repo.record_memory_access(
        user_id=user_id,
        memory_ids=[mem.id],
    )
    assert count == 1

    refreshed = await test_memory_service.memory_repo.get_memory_by_id(user_id=user_id, memory_id=mem.id)
    assert refreshed is not None
    assert refreshed.access_count == 1
    assert refreshed.last_accessed_at is not None
    assert refreshed.updated_at == updated_at_before, "updated_at must not move on access"


@pytest.mark.asyncio
async def test_get_memory_records_access(test_memory_service_with_access_tracking):
    """get_memory should bump access_count via EventBus subscriber when tracking enabled."""
    service, event_bus = test_memory_service_with_access_tracking
    user_id = uuid4()
    mem_data = MemoryCreate(
        title="Get stub",
        content="Memory used to test get_memory access tracking",
        context="Verifying get_memory bumps access_count",
        keywords=["usage", "get"],
        tags=["stub"],
        importance=5,
    )
    mem, _ = await service.create_memory(user_id=user_id, memory_data=mem_data)
    updated_at_before = mem.updated_at

    with patch.object(settings, "ACTIVITY_TRACK_READS", True):
        await service.get_memory(user_id=user_id, memory_id=mem.id)

    await event_bus.wait_for_pending()

    refreshed = await service.memory_repo.get_memory_by_id(user_id=user_id, memory_id=mem.id)
    assert refreshed is not None
    assert refreshed.access_count == 1
    assert refreshed.last_accessed_at is not None
    assert refreshed.updated_at == updated_at_before


@pytest.mark.asyncio
async def test_query_memory_records_access_for_primaries_and_linked(
    test_memory_service_with_access_tracking,
):
    """query_memory should record access for returned primaries and linked memories."""
    service, event_bus = test_memory_service_with_access_tracking
    user_id = uuid4()

    primary_data = MemoryCreate(
        title="Primary Memory",
        content="Main memory content",
        context="Primary context",
        keywords=["primary"],
        tags=["main"],
        importance=9,
    )
    primary, _ = await service.create_memory(user_id, primary_data)
    primary_updated_at_before = primary.updated_at

    linked_data = MemoryCreate(
        title="Linked Memory",
        content="Related content",
        context="Related context",
        keywords=["linked"],
        tags=["related"],
        importance=8,
    )
    linked, _ = await service.create_memory(user_id, linked_data)
    linked_updated_at_before = linked.updated_at

    await service.link_memories(
        user_id=user_id,
        memory_id=primary.id,
        related_ids=[linked.id],
    )

    event_bus.collected_events.clear()

    query_request = MemoryQueryRequest(
        query="primary",
        query_context="searching for primary memory",
        k=5,
        include_links=True,
        max_links_per_primary=5,
    )

    with patch.object(settings, "ACTIVITY_TRACK_READS", True):
        result = await service.query_memory(user_id, query_request)

    await event_bus.wait_for_pending()

    assert len(result.primary_memories) >= 1
    assert any(m.id == primary.id for m in result.primary_memories)

    queried_events = [e for e in event_bus.collected_events if e.action == ActionType.QUERIED]
    assert len(queried_events) == 1
    snapshot = queried_events[0].snapshot or {}
    tracked_ids = set(snapshot.get("result_ids") or []) | set(snapshot.get("linked_ids") or [])
    assert primary.id in tracked_ids
    assert linked.id in tracked_ids

    primary_refreshed = await service.memory_repo.get_memory_by_id(user_id=user_id, memory_id=primary.id)
    assert primary_refreshed is not None
    assert primary_refreshed.access_count >= 1
    assert primary_refreshed.last_accessed_at is not None
    assert primary_refreshed.updated_at == primary_updated_at_before

    linked_refreshed = await service.memory_repo.get_memory_by_id(user_id=user_id, memory_id=linked.id)
    assert linked_refreshed is not None
    assert linked_refreshed.access_count >= 1
    assert linked_refreshed.last_accessed_at is not None
    assert linked_refreshed.updated_at == linked_updated_at_before


@pytest.mark.asyncio
async def test_get_memory_no_access_when_tracking_disabled(
    test_memory_service_with_access_tracking,
):
    """get_memory must not bump access_count when ACTIVITY_TRACK_READS is false."""
    service, event_bus = test_memory_service_with_access_tracking
    user_id = uuid4()
    mem_data = MemoryCreate(
        title="No track stub",
        content="Memory used to test disabled tracking",
        context="Verifying no access write when tracking off",
        keywords=["usage", "off"],
        tags=["stub"],
        importance=5,
    )
    mem, _ = await service.create_memory(user_id=user_id, memory_data=mem_data)

    with patch.object(settings, "ACTIVITY_TRACK_READS", False):
        await service.get_memory(user_id=user_id, memory_id=mem.id)

    await event_bus.wait_for_pending()

    refreshed = await service.memory_repo.get_memory_by_id(user_id=user_id, memory_id=mem.id)
    assert refreshed is not None
    assert refreshed.access_count == 0
    assert refreshed.last_accessed_at is None
