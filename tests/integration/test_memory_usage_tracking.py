"""Integration tests for memory usage tracking (forgetful-hulkito fork).

Covers read-side telemetry: `record_memory_access` via repository and
service paths, with verification that `updated_at` is not mutated.
"""
from uuid import uuid4

import pytest

from app.models.memory_models import MemoryCreate


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
async def test_get_memory_records_access(test_memory_service):
    """get_memory should bump access_count via the service path."""
    user_id = uuid4()
    mem_data = MemoryCreate(
        title="Get stub",
        content="Memory used to test get_memory access tracking",
        context="Verifying get_memory bumps access_count",
        keywords=["usage", "get"],
        tags=["stub"],
        importance=5,
    )
    mem, _ = await test_memory_service.create_memory(user_id=user_id, memory_data=mem_data)

    await test_memory_service.get_memory(user_id=user_id, memory_id=mem.id)
    refreshed = await test_memory_service.memory_repo.get_memory_by_id(user_id=user_id, memory_id=mem.id)
    assert refreshed is not None
    assert refreshed.access_count == 1
    assert refreshed.last_accessed_at is not None
