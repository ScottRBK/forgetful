from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.config.settings import settings
from app.models.memory_models import MemoryCreate


@pytest.mark.asyncio
async def test_find_obsolete_matches_enabled_returns_stub_matches(test_memory_service):
    user_id = uuid4()
    old_data = MemoryCreate(
        title="Gate obsolete source",
        content="Shared gate test content for obsolete warning.",
        context="gate",
        keywords=["gate", "obsolete"],
        tags=["gate"],
        importance=8,
    )
    old_mem, _ = await test_memory_service.create_memory(user_id, old_data)
    replacement, _ = await test_memory_service.create_memory(
        user_id,
        MemoryCreate(
            title="Gate replacement",
            content="Replacement content.",
            context="gate",
            keywords=["gate"],
            tags=["gate"],
            importance=8,
        ),
    )
    await test_memory_service.memory_repo.mark_obsolete(
        user_id=user_id,
        memory_id=old_mem.id,
        reason="superseded",
        superseded_by=replacement.id,
    )

    new_mem, _ = await test_memory_service.create_memory(
        user_id,
        MemoryCreate(
            title="Gate new memory",
            content="Shared gate test content for obsolete warning.",
            context="gate",
            keywords=["gate", "obsolete"],
            tags=["gate"],
            importance=8,
        ),
    )

    matches = await test_memory_service.find_obsolete_matches(user_id, new_mem.id)
    assert matches
    assert matches[0].id == old_mem.id


@pytest.mark.asyncio
async def test_find_obsolete_matches_enabled_uses_threshold(test_memory_service, mock_memory_repository):
    user_id = uuid4()
    mem, _ = await test_memory_service.create_memory(
        user_id,
        MemoryCreate(
            title="Threshold spy",
            content="content",
            context="gate",
            keywords=["spy"],
            tags=["gate"],
            importance=5,
        ),
    )

    spy = AsyncMock(return_value=[])
    mock_memory_repository.find_obsolete_matches = spy

    await test_memory_service.find_obsolete_matches(user_id, mem.id)

    spy.assert_awaited_once()
    assert spy.await_args.kwargs["min_similarity"] == settings.OBSOLETE_WARNING_THRESHOLD


@pytest.mark.asyncio
async def test_find_obsolete_matches_disabled_skips_repo(test_memory_service, mock_memory_repository):
    user_id = uuid4()
    mem, _ = await test_memory_service.create_memory(
        user_id,
        MemoryCreate(
            title="Disabled gate",
            content="content",
            context="gate",
            keywords=["disabled"],
            tags=["gate"],
            importance=5,
        ),
    )

    spy = AsyncMock(return_value=[])
    mock_memory_repository.find_obsolete_matches = spy

    prev = settings.OBSOLETE_WARNING_ENABLED
    settings.OBSOLETE_WARNING_ENABLED = False
    try:
        matches = await test_memory_service.find_obsolete_matches(user_id, mem.id)
        assert matches == []
        spy.assert_not_called()
    finally:
        settings.OBSOLETE_WARNING_ENABLED = prev


@pytest.mark.asyncio
async def test_find_obsolete_matches_repo_error_returns_empty(test_memory_service, mock_memory_repository):
    user_id = uuid4()
    mem, _ = await test_memory_service.create_memory(
        user_id,
        MemoryCreate(
            title="Error gate",
            content="content",
            context="gate",
            keywords=["error"],
            tags=["gate"],
            importance=5,
        ),
    )

    mock_memory_repository.find_obsolete_matches = AsyncMock(side_effect=RuntimeError("boom"))

    matches = await test_memory_service.find_obsolete_matches(user_id, mem.id)
    assert matches == []
