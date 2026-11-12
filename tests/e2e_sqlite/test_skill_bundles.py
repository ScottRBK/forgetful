"""Native bundle package workflows; shared contract on both databases."""
import pytest

from app.config.settings import settings
from tests.skill_bundle_cases import SkillBundleCases
from tests.skill_bundle_feedback_cases import SkillBundleFeedbackCases

pytestmark = pytest.mark.asyncio


class TestSkillBundles(SkillBundleFeedbackCases, SkillBundleCases):
    pass


@pytest.fixture(autouse=True)
def bundle_feature_settings(monkeypatch):
    monkeypatch.setattr(settings, "SKILLS_ENABLED", True)
    monkeypatch.setattr(settings, "FILES_ENABLED", True)


@pytest.fixture
def bundle_app(sqlite_app):
    return sqlite_app
