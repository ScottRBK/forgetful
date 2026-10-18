"""Skill name uniqueness contracts exercised unchanged against SQLite and PostgreSQL."""

import asyncio
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy.exc import IntegrityError

from alembic import command
from app.bootstrap import create_repositories
from app.config.settings import settings
from app.exceptions import ConflictError
from app.models.skill_models import Skill, SkillCreate, SkillUpdate
from app.models.user_models import UserCreate
from app.services.skill_service import SkillService

PREVIOUS_REVISION = "20261008_plan_external_ref"


class StubEmbeddings:
    """Deterministic embeddings so the tests never load a model."""

    async def generate_embedding(self, text: str) -> list[float]:
        return [0.1] * settings.EMBEDDING_DIMENSIONS


def make_skill(name: str, **fields) -> SkillCreate:
    return SkillCreate(
        name=name, description=f"{name} description", content=f"# {name}", tags=[], **fields,
    )


@pytest.fixture
async def skill_store(skill_db, monkeypatch):
    monkeypatch.setattr(settings, "SKILLS_ENABLED", True)
    repos = create_repositories(skill_db, StubEmbeddings(), None)
    user = await repos["user"].create_user(UserCreate(
        external_id="skill-names-user", name="Skill names", email="skill-names@example.test",
    ))
    other_user = await repos["user"].create_user(UserCreate(
        external_id="skill-names-other", name="Other", email="skill-names-other@example.test",
    ))
    return repos, user, other_user


def pause_after_name_check(repo, gate: asyncio.Barrier) -> None:
    """Make the next name check wait for the other writer, so both pass it before either writes."""
    check = repo.skill_name_exists
    waited = False

    async def skill_name_exists(user_id, name):
        nonlocal waited
        exists = await check(user_id, name)
        if not waited:
            waited = True
            await gate.wait()
        return exists

    repo.skill_name_exists = skill_name_exists


class TestSkillNameUniquenessStorage:
    async def test_rename_to_existing_name_is_rejected(self, skill_store):
        repos, user, other_user = skill_store
        service = SkillService(repos["skill"])
        first = await service.create_skill(user.id, make_skill("skill-a"))
        second = await service.create_skill(user.id, make_skill("skill-b"))
        foreign = await service.create_skill(other_user.id, make_skill("skill-c"))

        with pytest.raises(ValueError, match="already exists"):
            await service.update_skill(user.id, second.id, SkillUpdate(name="skill-a"))

        assert (await service.get_skill(user.id, second.id)).name == "skill-b"
        assert (await service.get_skill(user.id, first.id)).name == "skill-a"
        # Renaming to the skill's own name and to a free name keeps working.
        same = await service.update_skill(
            user.id, first.id, SkillUpdate(name="skill-a", importance=9),
        )
        assert (same.name, same.importance) == ("skill-a", 9)
        renamed = await service.update_skill(user.id, second.id, SkillUpdate(name="skill-d"))
        assert renamed.name == "skill-d"
        # The name freed by the rename can be used again; names are per user.
        reused = await service.update_skill(user.id, first.id, SkillUpdate(name="skill-b"))
        assert reused.name == "skill-b"
        shared = await service.update_skill(other_user.id, foreign.id, SkillUpdate(name="skill-d"))
        assert shared.name == "skill-d"

    async def test_concurrent_creates_on_separate_connections(self, skill_db, skill_store):
        repos, user, _ = skill_store
        # Independent engines guarantee independent physical database connections (also on SQLite).
        other_db = type(skill_db)()
        other_repo = type(repos["skill"])(other_db, StubEmbeddings(), None)
        services = [SkillService(repos["skill"]), SkillService(other_repo)]
        gate = asyncio.Barrier(2)
        pause_after_name_check(repos["skill"], gate)
        pause_after_name_check(other_repo, gate)

        try:
            results = await asyncio.gather(
                *(s.create_skill(user.id, make_skill("race-skill")) for s in services),
                return_exceptions=True,
            )
        finally:
            await other_db.dispose()

        winners = [result for result in results if isinstance(result, Skill)]
        losers = [result for result in results if isinstance(result, ValueError)]
        assert len(winners) == len(losers) == 1, results
        assert "already exists" in str(losers[0])
        stored = [s for s in await services[0].list_skills(user.id) if s.name == "race-skill"]
        assert [s.id for s in stored] == [winners[0].id]
        # A failed transaction must not poison the next request.
        created = await services[0].create_skill(user.id, make_skill("race-skill-next"))
        assert created.name == "race-skill-next"

    async def test_concurrent_renames_on_separate_connections(self, skill_db, skill_store):
        repos, user, _ = skill_store
        service = SkillService(repos["skill"])
        first = await service.create_skill(user.id, make_skill("rename-one"))
        second = await service.create_skill(user.id, make_skill("rename-two"))
        other_db = type(skill_db)()
        other_repo = type(repos["skill"])(other_db, StubEmbeddings(), None)
        attempts = [(service, first.id), (SkillService(other_repo), second.id)]
        gate = asyncio.Barrier(2)
        pause_after_name_check(repos["skill"], gate)
        pause_after_name_check(other_repo, gate)

        try:
            results = await asyncio.gather(
                *(
                    target.update_skill(user.id, skill_id, SkillUpdate(name="rename-target"))
                    for target, skill_id in attempts
                ),
                return_exceptions=True,
            )
        finally:
            await other_db.dispose()

        winners = [result for result in results if isinstance(result, Skill)]
        losers = [result for result in results if isinstance(result, ValueError)]
        assert len(winners) == len(losers) == 1, results
        names = sorted(s.name for s in await service.list_skills(user.id))
        assert names.count("rename-target") == 1
        assert len(names) == 2

    async def test_unrelated_integrity_error_is_not_a_name_conflict(self, skill_store):
        repos, user, _ = skill_store
        with pytest.raises(IntegrityError):
            await repos["skill"].create_skill(user.id, make_skill("orphan", project_id=-1))

    async def test_repository_signals_duplicate_names_as_conflicts(self, skill_store):
        repos, user, _ = skill_store
        repo = repos["skill"]
        await repo.create_skill(user.id, make_skill("repo-a"))
        second = await repo.create_skill(user.id, make_skill("repo-b"))

        with pytest.raises(ConflictError):
            await repo.create_skill(user.id, make_skill("repo-a"))
        with pytest.raises(ConflictError):
            await repo.update_skill(user.id, second.id, SkillUpdate(name="repo-a"))

        assert (await repo.get_skill_by_id(user.id, second.id)).name == "repo-b"

    async def test_migration_renames_existing_duplicates_before_adding_the_index(
        self, skill_db, skill_store,
    ):
        repos, user, other_user = skill_store
        repo = repos["skill"]
        config = Config(str(Path(__file__).parents[1] / "alembic.ini"))

        def migrate(connection, direction, revision):
            config.attributes["connection"] = connection
            getattr(command, direction)(config, revision)

        async with skill_db._engine.begin() as connection:
            await connection.run_sync(migrate, "downgrade", PREVIOUS_REVISION)

        long_name = "x" * settings.SKILL_NAME_MAX_LENGTH
        try:
            # The old schema has no unique index, so the repository can store duplicates.
            legacy = [
                await repo.create_skill(user.id, make_skill(name))
                for name in ("legacy", "legacy", "legacy-2", "legacy", long_name, long_name)
            ]
            foreign = await repo.create_skill(other_user.id, make_skill("legacy"))
        finally:
            async with skill_db._engine.begin() as connection:
                await connection.run_sync(migrate, "upgrade", "head")

        names = {s.id: s.name for s in await repo.list_skills(user.id)}
        assert names[legacy[0].id] == "legacy"
        assert names[legacy[2].id] == "legacy-2"
        assert names[legacy[1].id] == "legacy-3"
        assert names[legacy[3].id] == "legacy-4"
        assert names[legacy[4].id] == long_name
        assert names[legacy[5].id] == "x" * (settings.SKILL_NAME_MAX_LENGTH - 2) + "-2"
        assert len(set(names.values())) == len(legacy)
        # Nothing but the colliding names changes, and other users are untouched.
        kept = await repo.get_skill_by_id(user.id, legacy[3].id)
        assert (kept.description, kept.content) == ("legacy description", "# legacy")
        assert (await repo.get_skill_by_id(other_user.id, foreign.id)).name == "legacy"
        # The index is back, so new duplicates are refused again.
        with pytest.raises(ConflictError):
            await repo.create_skill(user.id, make_skill("legacy"))
