"""Integration tests for harness argument and config parsing.

An explicit timeout must win over built-in per-skill defaults and must never reach the
in-container `timeout` as 0 (GNU `timeout 0` means no limit).
"""
import pytest
from pydantic import ValidationError

from test_harness.__main__ import config_from_argv
from test_harness.config import HarnessConfig
from test_harness.container import exec_command


@pytest.fixture(autouse=True)
def _clean_harness_env(monkeypatch):
    for name in ("SKILL_TIMEOUT", "SKILL_TIMEOUTS", "SKILLS"):
        monkeypatch.delenv(f"TEST_HARNESS_{name}", raising=False)


# --- explicit timeout beats the built-in per-skill default -------------------------


@pytest.mark.parametrize("seconds", [60, 600, 3000])
def test_cli_timeout_applies_to_every_skill_including_encode_repo(seconds):
    # Act
    config = config_from_argv(["--timeout", str(seconds)])

    # Assert
    assert config.timeout_for("forgetful-recall") == seconds
    assert config.timeout_for("forgetful-encode-repo") == seconds


def test_env_timeout_applies_to_encode_repo(monkeypatch):
    # Arrange
    monkeypatch.setenv("TEST_HARNESS_SKILL_TIMEOUT", "3000")

    # Act
    config = HarnessConfig()

    # Assert
    assert config.timeout_for("forgetful-encode-repo") == 3000


def test_in_container_wrapper_receives_the_cli_timeout_for_encode_repo():
    # Act
    config = config_from_argv(["--timeout", "60"])
    cmd = exec_command(config.timeout_for("forgetful-encode-repo"), "forgetful-encode-repo")

    # Assert
    assert cmd[:3] == ["timeout", "--kill-after=30s", "60"]


def test_encode_repo_keeps_its_longer_default_when_no_timeout_is_given():
    # Act
    config = config_from_argv([])

    # Assert
    assert config.timeout_for("forgetful-recall") == 900
    assert config.timeout_for("forgetful-encode-repo") == 1800


def test_explicit_per_skill_timeout_still_beats_the_global_timeout():
    # Act
    config = HarnessConfig(skill_timeout=600, skill_timeouts={"forgetful-encode-repo": 1200})

    # Assert
    assert config.timeout_for("forgetful-encode-repo") == 1200
    assert config.timeout_for("forgetful-recall") == 600


# --- the OS-level guard is never disabled -----------------------------------------


@pytest.mark.parametrize("raw", ["0", "0.5", "0.99", "-5", "nan", "inf"])
def test_cli_rejects_timeouts_that_cannot_enforce_a_limit(raw):
    # Act / Assert
    with pytest.raises(ValidationError, match="skill_timeout"):
        config_from_argv(["--timeout", raw])


def test_env_timeout_below_one_second_is_rejected(monkeypatch):
    # Arrange
    monkeypatch.setenv("TEST_HARNESS_SKILL_TIMEOUT", "0")

    # Act / Assert
    with pytest.raises(ValidationError, match="skill_timeout"):
        HarnessConfig()


def test_per_skill_timeout_below_one_second_is_rejected():
    # Act / Assert
    with pytest.raises(ValidationError, match="skill_timeouts"):
        HarnessConfig(skill_timeouts={"forgetful-encode-repo": 0})


def test_one_second_timeout_is_accepted():
    # Act
    config = config_from_argv(["--timeout", "1"])

    # Assert
    assert config.timeout_for("forgetful-recall") == 1


@pytest.mark.parametrize(
    ("timeout", "expected"),
    [(0, "1"), (0.5, "1"), (1, "1"), (1.2, "2"), (59.9, "60"), (900, "900")],
)
def test_exec_command_never_hands_gnu_timeout_a_zero_or_shorter_limit(timeout, expected):
    # Act
    cmd = exec_command(timeout, "forgetful-recall")

    # Assert: rounded up, so the in-container limit is never below what was asked for
    assert cmd[:3] == ["timeout", "--kill-after=30s", expected]
