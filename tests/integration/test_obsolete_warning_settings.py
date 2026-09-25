import pytest
from pydantic import ValidationError

from app.config.settings import Settings


def test_obsolete_warning_enabled_default_is_true():
    assert Settings().OBSOLETE_WARNING_ENABLED is True


def test_obsolete_warning_enabled_false_from_env(monkeypatch):
    monkeypatch.setenv("OBSOLETE_WARNING_ENABLED", "false")
    assert Settings().OBSOLETE_WARNING_ENABLED is False


def test_obsolete_warning_threshold_default():
    assert Settings().OBSOLETE_WARNING_THRESHOLD == 0.89


def test_obsolete_warning_threshold_validation_rejects_out_of_range():
    with pytest.raises(ValidationError):
        Settings(OBSOLETE_WARNING_THRESHOLD=1.5)
    with pytest.raises(ValidationError):
        Settings(OBSOLETE_WARNING_THRESHOLD=0.0)


def test_obsolete_warning_threshold_accepts_one():
    assert Settings(OBSOLETE_WARNING_THRESHOLD=1.0).OBSOLETE_WARNING_THRESHOLD == 1.0
