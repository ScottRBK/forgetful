"""Skill Plugin loading and bootstrap wiring."""

import pytest

from app.config.settings import settings
from app.protocols.write_plugin_protocol import SkillPlugin


def test_loader_returns_none_when_unset(monkeypatch):
    from app.config.write_plugin import load_skill_plugin

    monkeypatch.setattr(settings, "SKILL_WRITE_PLUGIN", "")
    assert load_skill_plugin(settings) is None


def test_loader_rejects_unimportable_module(monkeypatch):
    from app.config.write_plugin import load_skill_plugin

    monkeypatch.setattr(settings, "SKILL_WRITE_PLUGIN", "no_such_module_xyz:plugin")
    with pytest.raises(ValueError, match="SKILL_WRITE_PLUGIN import failed"):
        load_skill_plugin(settings)


def test_loader_rejects_missing_attribute(skill_plugin_runtime, monkeypatch):
    from app.config.write_plugin import load_skill_plugin

    monkeypatch.setattr(
        settings, "SKILL_WRITE_PLUGIN", f"{skill_plugin_runtime}:no_such_object",
    )
    with pytest.raises(ValueError, match="attribute lookup failed"):
        load_skill_plugin(settings)


def test_loader_rejects_non_plugin_object(skill_plugin_runtime, monkeypatch):
    from app.config.write_plugin import load_skill_plugin

    monkeypatch.setattr(settings, "SKILL_WRITE_PLUGIN", f"{skill_plugin_runtime}:decide")
    with pytest.raises(ValueError, match="must reference a SkillPlugin registration"):
        load_skill_plugin(settings)


def test_loader_rejects_malformed_reference(monkeypatch):
    from app.config.write_plugin import load_skill_plugin

    monkeypatch.setattr(settings, "SKILL_WRITE_PLUGIN", "not-a-reference")
    with pytest.raises(ValueError, match="must be an importable module:object reference"):
        load_skill_plugin(settings)


def test_loader_accepts_a_valid_registration(skill_plugin_runtime, monkeypatch):
    from app.config.write_plugin import load_skill_plugin

    monkeypatch.setattr(
        settings, "SKILL_WRITE_PLUGIN", f"{skill_plugin_runtime}:plugin",
    )
    loaded = load_skill_plugin(settings)
    assert isinstance(loaded, SkillPlugin)
    assert set(loaded.before_save) == {"create", "update", "delete"}


async def test_bootstrap_wires_the_skill_plugin(skill_plugin_runtime, monkeypatch):
    """The registration must reach SkillService through build_runtime."""
    from app.bootstrap import build_runtime, dispose_runtime

    runtime = await build_runtime()
    try:
        service = runtime.services.skill
        assert service is not None
        assert service._write_plugin is not None
        assert service._write_plugin.has_before("create") is True
    finally:
        await dispose_runtime(runtime)


async def test_bootstrap_rejects_a_bad_registration(monkeypatch):
    from app.bootstrap import build_runtime

    monkeypatch.setattr(settings, "SKILLS_ENABLED", True)
    monkeypatch.setattr(settings, "SKILL_WRITE_PLUGIN", "no_such_module_xyz:plugin")
    with pytest.raises(ValueError, match="SKILL_WRITE_PLUGIN"):
        await build_runtime()
