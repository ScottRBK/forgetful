"""Integration tests for the full re-embed run: storage reset, constraints and skills.

Uses mocked repositories and embedding adapter, so no real database is required.
"""
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.models.memory_models import Memory
from app.models.skill_models import Skill
from app.services.re_embedding_service import ReEmbeddingService


def _memory(memory_id: int) -> Memory:
    return Memory(
        id=memory_id,
        title=f"Memory {memory_id}",
        content="Content",
        context="context",
        keywords=["k"],
        tags=["t"],
        importance=7,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _skill(skill_id: int) -> Skill:
    return Skill(
        id=skill_id,
        name=f"skill-{skill_id}",
        description=f"Description of skill {skill_id}",
        content="# Steps",
        tags=[],
        importance=7,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _memory_repo(memories: list[Memory]):
    repo = AsyncMock()
    repo.count_all_memories.return_value = len(memories)

    async def batch(limit: int, offset: int):
        return memories[offset:offset + limit]

    repo.get_memories_for_reembedding.side_effect = batch
    repo.validate_embedding_count.return_value = True
    repo.validate_embedding_dimensions.return_value = True
    repo.validate_search_works.return_value = True
    return repo


def _skill_repo(skills: list[Skill]):
    repo = AsyncMock()
    repo.count_all_skills.return_value = len(skills)

    async def batch(limit: int, offset: int):
        return skills[offset:offset + limit]

    repo.get_skills_for_reembedding.side_effect = batch
    repo.validate_embedding_count.return_value = True
    repo.validate_embedding_dimensions.return_value = True
    return repo


def _embedder():
    adapter = AsyncMock()
    adapter.generate_embedding.return_value = [0.1] * 8
    return adapter


async def test_empty_database_still_resets_vector_storage():
    """A dimension change on a database without memories must still resize the vector storage."""
    memory_repo = _memory_repo([])
    embedder = _embedder()

    result = await ReEmbeddingService(memory_repo, embedder).re_embed_all()

    memory_repo.reset_embedding_storage.assert_awaited_once()
    memory_repo.bulk_update_embeddings.assert_not_called()
    embedder.generate_embedding.assert_not_called()
    assert (result.total_memories, result.total_processed) == (0, 0)
    assert result.validation is not None
    assert result.validation.all_passed


async def test_constraints_are_restored_only_after_validation_passes():
    memory_repo = _memory_repo([_memory(1)])
    calls: list[str] = []

    async def validate():
        calls.append("validate")
        return True

    async def finalize():
        calls.append("finalize")

    memory_repo.validate_search_works.side_effect = validate
    memory_repo.finalize_embedding_storage.side_effect = finalize

    await ReEmbeddingService(memory_repo, _embedder()).re_embed_all()

    assert calls == ["validate", "finalize"]


async def test_failed_validation_keeps_constraints_relaxed():
    memory_repo = _memory_repo([_memory(1)])
    memory_repo.validate_embedding_count.return_value = False

    result = await ReEmbeddingService(memory_repo, _embedder()).re_embed_all()

    assert not result.validation.all_passed
    memory_repo.finalize_embedding_storage.assert_not_called()


async def test_failed_run_never_restores_constraints():
    memory_repo = _memory_repo([_memory(1), _memory(2)])
    embedder = _embedder()
    embedder.generate_embedding.side_effect = [[0.1] * 8, RuntimeError("provider down")]

    with pytest.raises(RuntimeError, match="provider down"):
        await ReEmbeddingService(memory_repo, embedder, batch_size=1).re_embed_all()

    memory_repo.finalize_embedding_storage.assert_not_called()


async def test_empty_database_with_skills_resets_and_refills_skill_storage():
    memory_repo = _memory_repo([])
    skill_repo = _skill_repo([_skill(1)])

    result = await ReEmbeddingService(
        memory_repo, _embedder(), skill_repository=skill_repo,
    ).re_embed_all()

    memory_repo.reset_embedding_storage.assert_awaited_once()
    skill_repo.reset_embedding_storage.assert_awaited_once()
    skill_repo.bulk_update_embeddings.assert_awaited_once()
    assert (result.total_skills, result.skills_processed) == (1, 1)


async def test_skills_are_reset_before_being_refilled_from_their_description():
    skills = [_skill(1), _skill(2), _skill(3)]
    skill_repo = _skill_repo(skills)
    embedder = _embedder()
    calls: list[str] = []

    async def track_reset():
        calls.append("reset")

    async def track_bulk(updates):
        calls.append(f"bulk:{[skill_id for skill_id, _ in updates]}")

    skill_repo.reset_embedding_storage.side_effect = track_reset
    skill_repo.bulk_update_embeddings.side_effect = track_bulk

    result = await ReEmbeddingService(
        _memory_repo([_memory(1)]), embedder, batch_size=2, skill_repository=skill_repo,
    ).re_embed_all()

    assert calls == ["reset", "bulk:[1, 2]", "bulk:[3]"]
    # Only the description is the semantic key of a skill.
    embedded = [call.args[0] for call in embedder.generate_embedding.await_args_list]
    assert embedded[1:] == [skill.description for skill in skills]
    assert (result.total_skills, result.skills_processed) == (3, 3)
    assert result.validation.all_passed


async def test_skill_validation_failures_fail_the_run_and_keep_constraints_relaxed():
    memory_repo = _memory_repo([_memory(1)])
    skill_repo = _skill_repo([_skill(1)])
    skill_repo.validate_embedding_dimensions.return_value = False

    result = await ReEmbeddingService(
        memory_repo, _embedder(), skill_repository=skill_repo,
    ).re_embed_all()

    assert not result.validation.dimensions_ok
    assert not result.validation.all_passed
    memory_repo.finalize_embedding_storage.assert_not_called()
    skill_repo.finalize_embedding_storage.assert_not_called()


async def test_skill_constraints_are_restored_after_the_memory_constraints():
    memory_repo = _memory_repo([_memory(1)])
    skill_repo = _skill_repo([_skill(1)])
    calls: list[str] = []

    async def finalize_memories():
        calls.append("finalize-memories")

    async def finalize_skills():
        calls.append("finalize-skills")

    memory_repo.finalize_embedding_storage.side_effect = finalize_memories
    skill_repo.finalize_embedding_storage.side_effect = finalize_skills

    await ReEmbeddingService(memory_repo, _embedder(), skill_repository=skill_repo).re_embed_all()

    assert calls == ["finalize-memories", "finalize-skills"]


async def test_skills_are_not_touched_without_a_skill_repository():
    memory_repo = _memory_repo([_memory(1)])

    result = await ReEmbeddingService(memory_repo, _embedder()).re_embed_all()

    assert (result.total_skills, result.skills_processed) == (0, 0)
    memory_repo.finalize_embedding_storage.assert_awaited_once()


async def test_caller_can_reset_storage_itself():
    """The CLI resets storage as its own visible step, so the run must not reset it twice."""
    memory_repo = _memory_repo([_memory(1)])
    skill_repo = _skill_repo([_skill(1)])
    service = ReEmbeddingService(memory_repo, _embedder(), skill_repository=skill_repo)

    await service.re_embed_all(reset_storage=False)

    memory_repo.reset_embedding_storage.assert_not_called()
    skill_repo.reset_embedding_storage.assert_not_called()

    await service.reset_vector_storage()

    memory_repo.reset_embedding_storage.assert_awaited_once()
    skill_repo.reset_embedding_storage.assert_awaited_once()
