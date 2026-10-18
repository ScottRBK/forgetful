"""Skill name uniqueness and unrestricted allowed_tools against PostgreSQL."""

import pytest
from sqlalchemy import text

from app.models.skill_models import SkillCreate, SkillUpdate
from app.services.skill_service import SkillService
from tests.skill_name_uniqueness_cases import (
    TestSkillNameUniquenessStorage as TestSkillNameUniquenessStorage,
)
from tests.skill_name_uniqueness_cases import skill_store as skill_store

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio(loop_scope="session")]


@pytest.fixture
def skill_db(db_adapter):
    return db_adapter


async def stored_allowed_tools_is_null(db_adapter, skill_id: int) -> bool:
    async with db_adapter.system_session() as session:
        result = await session.execute(
            text("SELECT allowed_tools IS NULL FROM skills WHERE id = :id"), {"id": skill_id},
        )
        return result.scalar_one()


class TestSkillAllowedToolsStorage:
    async def test_unset_allowed_tools_is_stored_as_null(self, skill_store, skill_db):
        repos, user, _ = skill_store
        service = SkillService(repos["skill"])

        created = await service.create_skill(user.id, SkillCreate(
            name="no-tools", description="skill without tool restrictions", content="body",
        ))

        assert created.allowed_tools is None
        assert (await service.get_skill(user.id, created.id)).allowed_tools is None
        assert await stored_allowed_tools_is_null(skill_db, created.id)
        assert "allowed-tools" not in await service.export_skill(user.id, created.id)

    async def test_explicit_allowed_tools_round_trip(self, skill_store, skill_db):
        repos, user, _ = skill_store
        service = SkillService(repos["skill"])

        restricted = await service.create_skill(user.id, SkillCreate(
            name="some-tools", description="d", content="body", allowed_tools=["Read", "Bash"],
        ))
        empty = await service.create_skill(user.id, SkillCreate(
            name="empty-tools", description="d", content="body", allowed_tools=[],
        ))

        assert restricted.allowed_tools == ["Read", "Bash"]
        assert empty.allowed_tools == []
        assert not await stored_allowed_tools_is_null(skill_db, empty.id)
        updated = await service.update_skill(user.id, restricted.id, SkillUpdate(importance=9))
        assert updated.allowed_tools == ["Read", "Bash"]
