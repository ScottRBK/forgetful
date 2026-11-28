"""Task Plugin loading and bootstrap wiring."""

import pytest

from app.config.settings import settings
from app.protocols.write_plugin_protocol import TaskPlugin


def test_loader_returns_none_when_unset(monkeypatch):
    from app.config.write_plugin import load_task_plugin

    monkeypatch.setattr(settings, "TASK_WRITE_PLUGIN", "")
    assert load_task_plugin(settings) is None


def test_loader_rejects_unimportable_module(monkeypatch):
    from app.config.write_plugin import load_task_plugin

    monkeypatch.setattr(settings, "TASK_WRITE_PLUGIN", "no_such_module_xyz:plugin")
    with pytest.raises(ValueError, match="TASK_WRITE_PLUGIN import failed"):
        load_task_plugin(settings)


def test_loader_rejects_missing_attribute(task_plugin_runtime, monkeypatch):
    from app.config.write_plugin import load_task_plugin

    monkeypatch.setattr(
        settings, "TASK_WRITE_PLUGIN", f"{task_plugin_runtime}:no_such_object",
    )
    with pytest.raises(ValueError, match="attribute lookup failed"):
        load_task_plugin(settings)


def test_loader_rejects_non_plugin_object(task_plugin_runtime, monkeypatch):
    from app.config.write_plugin import load_task_plugin

    monkeypatch.setattr(settings, "TASK_WRITE_PLUGIN", f"{task_plugin_runtime}:decide")
    with pytest.raises(ValueError, match="must reference a TaskPlugin registration"):
        load_task_plugin(settings)


def test_loader_rejects_malformed_reference(monkeypatch):
    from app.config.write_plugin import load_task_plugin

    monkeypatch.setattr(settings, "TASK_WRITE_PLUGIN", "not-a-reference")
    with pytest.raises(ValueError, match="must be an importable module:object reference"):
        load_task_plugin(settings)


def test_loader_accepts_a_valid_registration(task_plugin_runtime, monkeypatch):
    from app.config.write_plugin import load_task_plugin

    monkeypatch.setattr(settings, "TASK_WRITE_PLUGIN", f"{task_plugin_runtime}:plugin")
    loaded = load_task_plugin(settings)
    assert isinstance(loaded, TaskPlugin)
    assert set(loaded.before_save) == {"create", "update", "delete"}


async def test_bootstrap_wires_the_task_plugin(task_plugin_runtime, monkeypatch):
    """The registration must reach TaskService through build_runtime."""
    from app.bootstrap import build_runtime, dispose_runtime

    runtime = await build_runtime()
    try:
        service = runtime.services.task
        assert service is not None
        assert service._write_plugin is not None
        assert service._write_plugin.has_before("create") is True
    finally:
        await dispose_runtime(runtime)


async def test_bootstrap_rejects_a_bad_registration(monkeypatch):
    from app.bootstrap import build_runtime

    monkeypatch.setattr(settings, "TASK_WRITE_PLUGIN", "no_such_module_xyz:plugin")
    with pytest.raises(ValueError, match="TASK_WRITE_PLUGIN"):
        await build_runtime()
