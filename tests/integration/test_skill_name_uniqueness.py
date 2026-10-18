"""Skill service name uniqueness with stubbed storage (no database required)."""

from uuid import uuid4

import pytest

from app.exceptions import ConflictError, NotFoundError
from app.models.skill_models import SkillCreate, SkillUpdate
from app.services.skill_service import SkillService
from tests.integration.conftest import InMemorySkillRepository


def make_skill(name: str) -> SkillCreate:
    return SkillCreate(name=name, description="desc", content="body", tags=[])


class RacingSkillRepository(InMemorySkillRepository):
    """Passes the name pre-check, then loses the race at write time like a unique index."""

    async def skill_name_exists(self, user_id, name):
        return False

    async def create_skill(self, user_id, skill_data):
        raise ConflictError("duplicate skill name")

    async def update_skill(self, user_id, skill_id, skill_data):
        raise ConflictError("duplicate skill name")


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def service():
    return SkillService(InMemorySkillRepository(), event_bus=None)


class TestUpdateSkillRename:
    async def test_rename_to_name_used_by_another_skill_is_rejected(self, service, user_id):
        await service.create_skill(user_id, make_skill("skill-a"))
        second = await service.create_skill(user_id, make_skill("skill-b"))

        with pytest.raises(ValueError, match="'skill-a' already exists"):
            await service.update_skill(user_id, second.id, SkillUpdate(name="skill-a"))

        assert (await service.get_skill(user_id, second.id)).name == "skill-b"

    async def test_rename_to_own_name_or_free_name_is_allowed(self, service, user_id):
        created = await service.create_skill(user_id, make_skill("skill-a"))

        same = await service.update_skill(user_id, created.id, SkillUpdate(name="skill-a"))
        assert same.name == "skill-a"
        renamed = await service.update_skill(user_id, created.id, SkillUpdate(name="skill-b"))
        assert renamed.name == "skill-b"

    async def test_update_without_name_does_not_check_names(self, service, user_id):
        created = await service.create_skill(user_id, make_skill("skill-a"))

        updated = await service.update_skill(user_id, created.id, SkillUpdate(importance=9))

        assert updated.importance == 9

    async def test_missing_skill_is_still_not_found(self, service, user_id):
        await service.create_skill(user_id, make_skill("skill-a"))

        with pytest.raises(NotFoundError):
            await service.update_skill(user_id, 999, SkillUpdate(name="skill-a"))


class TestWriteTimeConflicts:
    """A unique index violation at write time must look like the pre-check failure."""

    async def test_create_conflict_is_reported_as_already_exists(self, user_id):
        service = SkillService(RacingSkillRepository(), event_bus=None)

        with pytest.raises(ValueError, match="'racing' already exists"):
            await service.create_skill(user_id, make_skill("racing"))

    async def test_rename_conflict_is_reported_as_already_exists(self, user_id):
        repo = RacingSkillRepository()
        service = SkillService(repo, event_bus=None)
        created = await InMemorySkillRepository.create_skill(repo, user_id, make_skill("old"))

        with pytest.raises(ValueError, match="'racing' already exists"):
            await service.update_skill(user_id, created.id, SkillUpdate(name="racing"))
