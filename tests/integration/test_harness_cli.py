"""Integration tests for the harness CLI argument mapping (test_harness/__main__.py).

Only flags the user actually passed reach HarnessConfig, so unset flags fall through to
TEST_HARNESS_* env and then defaults (precedence proven in test_harness_config.py).
"""
from test_harness.__main__ import config_from_argv


def test_no_flags_uses_config_defaults():
    # Act
    config = config_from_argv([])

    # Assert
    assert config.agent_type == "opencode"
    assert config.model == "opencode-go/deepseek-v4.1-flash"
    assert len(config.skills) == 9


def test_flags_map_to_config_fields():
    # Act
    config = config_from_argv([
        "--agent", "claude_code",
        "--model", "sonnet",
        "--effort", "medium",
        "--skills", "forgetful-recall,forgetful-remember",
        "--timeout", "120",
    ])

    # Assert
    assert config.agent_type == "claude_code"
    assert config.model == "sonnet"
    assert config.effort == "medium"
    assert config.skills == ["forgetful-remember", "forgetful-recall"]
    assert config.timeout_for("forgetful-recall") == 120


def test_rebuild_image_flag():
    # Act
    config = config_from_argv(["--rebuild-image"])
    default = config_from_argv([])

    # Assert
    assert config.rebuild_image is True
    assert default.rebuild_image is False


def test_unset_flags_fall_through_to_env(monkeypatch):
    # Arrange
    monkeypatch.setenv("TEST_HARNESS_MODEL", "from-env")

    # Act
    config = config_from_argv(["--agent", "codex"])

    # Assert
    assert config.agent_type == "codex"
    assert config.model == "from-env"
