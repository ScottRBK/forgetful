"""Service-level regression tests for `ReEmbeddingService` scope validation.

Uses an AsyncMock repository and a mocked embedding adapter, no database required.
The real-SQL counterparts live in `tests/e2e_sqlite/test_updated_at_embedding_writes_sqlite.py`.
"""
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services.re_embedding_service import ReEmbeddingService


def _make_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.project_exists_for_user.return_value = True
    return repo


def _make_adapter() -> AsyncMock:
    adapter = AsyncMock()
    adapter.generate_embedding.return_value = [0.1] * 384
    return adapter


async def test_project_scope_must_exist_and_be_owned_even_without_memory_ids():
    user_id = uuid4()
    repo = _make_repo()
    repo.project_exists_for_user.return_value = False
    service = ReEmbeddingService(repo, _make_adapter())

    with pytest.raises(ValueError, match=r"project_id=42 not found or not owned"):
        await service.validate_targeted_scope(user_id, None, 42)

    repo.project_exists_for_user.assert_awaited_once_with(user_id=user_id, project_id=42)


async def test_owned_project_scope_is_accepted_without_memory_ids():
    repo = _make_repo()
    service = ReEmbeddingService(repo, _make_adapter())

    await service.validate_targeted_scope(uuid4(), None, 42)


async def test_global_scope_does_not_look_up_a_project():
    repo = _make_repo()
    service = ReEmbeddingService(repo, _make_adapter())

    await service.validate_targeted_scope(uuid4(), None, None)

    repo.project_exists_for_user.assert_not_awaited()
