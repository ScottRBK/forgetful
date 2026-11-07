"""Integration tests for the UAT harness configuration (test_harness/config.py).

Precedence is init kwargs (CLI flags) > TEST_HARNESS_* env > defaults. The walkthrough
order is fixed by data dependencies (writes feed later reads), so a skills subset must
always run in canonical order regardless of how the filter was spelled.
"""
import pytest

from test_harness.config import SKILL_ORDER, HarnessConfig


def test_defaults_match_locked_decisions():
    # Act
    config = HarnessConfig()

    # Assert
    assert config.agent_type == "opencode"
    assert config.model == "opencode-go/deepseek-v4.1-flash"
    assert config.effort is None
    assert config.surface == "cli"
    assert config.skills == list(SKILL_ORDER)
    assert config.timeout_for("forgetful-recall") == 900
    assert config.timeout_for("forgetful-encode-repo") == 1800


def test_walkthrough_order_starts_with_setup_and_ends_with_encode_repo():
    # Assert: cli-setup verifies the connection story before anything writes; encode-repo
    # is the heaviest write pass and depends on nothing after it. mcp-setup is reserved
    # for the MCP surface pass and must not be walked in v1.
    assert SKILL_ORDER[0] == "forgetful-cli-setup"
    assert SKILL_ORDER[-1] == "forgetful-encode-repo"
    assert "forgetful-mcp-setup" not in SKILL_ORDER
    assert len(SKILL_ORDER) == 9


def test_env_overrides_defaults(monkeypatch):
    # Arrange
    monkeypatch.setenv("TEST_HARNESS_MODEL", "anthropic/claude-sonnet-4-5")
    monkeypatch.setenv("TEST_HARNESS_SKILL_TIMEOUT", "300")

    # Act
    config = HarnessConfig()

    # Assert
    assert config.model == "anthropic/claude-sonnet-4-5"
    assert config.timeout_for("forgetful-recall") == 300


def test_init_kwargs_beat_env(monkeypatch):
    # Arrange
    monkeypatch.setenv("TEST_HARNESS_MODEL", "from-env")

    # Act
    config = HarnessConfig(model="from-flag")

    # Assert
    assert config.model == "from-flag"


def test_surface_other_than_cli_is_rejected():
    # Act / Assert: mcp is a reserved axis, not a silent no-op
    with pytest.raises(ValueError, match="cli"):
        HarnessConfig(surface="mcp")


def test_skills_subset_normalizes_to_walkthrough_order():
    # Arrange: filter spelled in reverse of canonical order
    subset = ["forgetful-recall", "forgetful-remember"]

    # Act
    config = HarnessConfig(skills=subset)

    # Assert
    assert config.skills == ["forgetful-remember", "forgetful-recall"]


def test_unknown_skill_is_rejected_by_name():
    # Act / Assert
    with pytest.raises(ValueError, match="forgetful-teleport"):
        HarnessConfig(skills=["forgetful-recall", "forgetful-teleport"])
