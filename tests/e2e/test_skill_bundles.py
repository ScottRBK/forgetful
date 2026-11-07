"""Native bundle package workflows; shared contract on both databases."""
import pytest

from app.config.settings import settings
from tests.skill_bundle_cases import SkillBundleCases

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio(loop_scope="session")]


class TestSkillBundles(SkillBundleCases):
    pass


@pytest.fixture(autouse=True)
def bundle_feature_settings(monkeypatch):
    monkeypatch.setattr(settings, "SKILLS_ENABLED", True)
    monkeypatch.setattr(settings, "FILES_ENABLED", True)


@pytest.fixture
def bundle_app(postgres_app):
    return postgres_app

SETTINGS_OVERRIDE = {"SKILLS_ENABLED": True}
