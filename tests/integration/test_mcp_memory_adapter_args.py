"""Integration tests for the sort option validation in MemoryService.list_memories.

The service is shared by the MCP adapter, the REST routes and the CLI, so it is the
single place where sort_by / sort_order are normalised and validated.
"""
from uuid import uuid4

import pytest

from app.models.memory_models import (
    VALID_SORT_BY,
    VALID_SORT_ORDER,
    MemoryCreate,
)
from app.routes.api import memories as memories_routes

# ---------------------------------------------------------------------------
# sort option validation in MemoryService.list_memories
# ---------------------------------------------------------------------------


async def _seed(service, user_id, importances=(3, 9, 6)):
    """Create memories oldest to newest; the stub repository stamps increasing created_at values"""
    ids = []
    for i, importance in enumerate(importances):
        memory, _ = await service.create_memory(
            user_id=user_id,
            memory_data=MemoryCreate(
                title=f"sort probe {i}",
                content=f"content {i}",
                context="sort validation",
                keywords=["sort"],
                tags=["sort"],
                importance=importance,
            ),
        )
        ids.append(memory.id)
    return ids


@pytest.mark.asyncio
@pytest.mark.parametrize("sort_order", ["desc", "DESC", "Desc", " desc ", "\tdesc\n"])
async def test_list_memories_normalises_descending_sort_order(test_memory_service, sort_order):
    user_id = uuid4()
    ids = await _seed(test_memory_service, user_id)

    memories, total = await test_memory_service.list_memories(user_id=user_id, sort_order=sort_order)

    assert [m.id for m in memories] == ids[::-1]
    assert total == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("sort_order", ["asc", "ASC", " Asc "])
async def test_list_memories_normalises_ascending_sort_order(test_memory_service, sort_order):
    user_id = uuid4()
    ids = await _seed(test_memory_service, user_id)

    memories, _ = await test_memory_service.list_memories(user_id=user_id, sort_order=sort_order)

    assert [m.id for m in memories] == ids


@pytest.mark.asyncio
async def test_list_memories_normalises_sort_by(test_memory_service):
    user_id = uuid4()
    first, second, third = await _seed(test_memory_service, user_id)

    memories, _ = await test_memory_service.list_memories(
        user_id=user_id, sort_by="Importance", sort_order="DESC",
    )

    assert [m.id for m in memories] == [second, third, first]


@pytest.mark.asyncio
async def test_list_memories_passes_only_normalised_sort_options_to_the_repository(test_memory_service):
    seen = {}

    async def fake_list_memories(**kwargs):
        seen.update(kwargs)
        return [], 0

    test_memory_service.memory_repo.list_memories = fake_list_memories

    await test_memory_service.list_memories(
        user_id=uuid4(), sort_by=" Updated_At ", sort_order=" ASC ",
    )

    assert seen["sort_by"] == "updated_at"
    assert seen["sort_order"] == "asc"


@pytest.mark.asyncio
@pytest.mark.parametrize("sort_order", ["descending", "newest", "", None, 5])
async def test_list_memories_rejects_invalid_sort_order(test_memory_service, sort_order):
    with pytest.raises(ValueError, match="sort_order must be one of: asc, desc"):
        await test_memory_service.list_memories(user_id=uuid4(), sort_order=sort_order)


@pytest.mark.asyncio
@pytest.mark.parametrize("sort_by", ["bogus", "createdat", "", None, 5])
async def test_list_memories_rejects_invalid_sort_by(test_memory_service, sort_by):
    with pytest.raises(ValueError, match="sort_by must be one of: created_at, updated_at, importance"):
        await test_memory_service.list_memories(user_id=uuid4(), sort_by=sort_by)


def test_shared_sort_constants_match_the_rest_route():
    assert set(VALID_SORT_BY) == memories_routes.VALID_SORT_BY
    assert set(VALID_SORT_ORDER) == memories_routes.VALID_SORT_ORDER
