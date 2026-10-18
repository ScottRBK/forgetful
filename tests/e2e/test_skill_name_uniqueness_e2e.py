"""Skill name uniqueness on create, rename and migration against PostgreSQL."""

import pytest

from tests.skill_name_uniqueness_cases import (
    TestSkillNameUniquenessStorage as TestSkillNameUniquenessStorage,
)
from tests.skill_name_uniqueness_cases import skill_store as skill_store

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio(loop_scope="session")]


@pytest.fixture
def skill_db(db_adapter):
    return db_adapter
