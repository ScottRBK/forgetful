"""File Plugin loading, bootstrap wiring and transport shapes."""

import pytest
from pydantic import ValidationError

from app.config.settings import Settings, settings
from app.protocols.write_plugin_protocol import FilePlugin


def test_loader_returns_none_when_unset(monkeypatch):
    from app.config.write_plugin import load_file_plugin

    monkeypatch.setattr(settings, "FILE_WRITE_PLUGIN", "")
    assert load_file_plugin(settings) is None


def test_loader_rejects_unimportable_module(monkeypatch):
    from app.config.write_plugin import load_file_plugin

    monkeypatch.setattr(settings, "FILE_WRITE_PLUGIN", "no_such_module_xyz:plugin")
    with pytest.raises(ValueError, match="FILE_WRITE_PLUGIN import failed"):
        load_file_plugin(settings)


def test_loader_rejects_missing_attribute(file_plugin_runtime, monkeypatch):
    from app.config.write_plugin import load_file_plugin

    monkeypatch.setattr(
        settings, "FILE_WRITE_PLUGIN", f"{file_plugin_runtime}:no_such_object",
    )
    with pytest.raises(ValueError, match="attribute lookup failed"):
        load_file_plugin(settings)


def test_loader_rejects_non_plugin_object(file_plugin_runtime, monkeypatch):
    from app.config.write_plugin import load_file_plugin

    monkeypatch.setattr(settings, "FILE_WRITE_PLUGIN", f"{file_plugin_runtime}:decide")
    with pytest.raises(ValueError, match="must reference a FilePlugin registration"):
        load_file_plugin(settings)


def test_loader_rejects_malformed_reference(monkeypatch):
    from app.config.write_plugin import load_file_plugin

    monkeypatch.setattr(settings, "FILE_WRITE_PLUGIN", "not-a-reference")
    with pytest.raises(ValueError, match="must be an importable module:object reference"):
        load_file_plugin(settings)


def test_loader_accepts_a_valid_registration(file_plugin_runtime, monkeypatch):
    from app.config.write_plugin import load_file_plugin

    monkeypatch.setattr(settings, "FILE_WRITE_PLUGIN", f"{file_plugin_runtime}:plugin")
    loaded = load_file_plugin(settings)
    assert isinstance(loaded, FilePlugin)
    assert set(loaded.before_save) == {"create", "update", "delete"}


async def test_bootstrap_wires_the_file_plugin(file_plugin_runtime, monkeypatch):
    """The registration must reach FileService through build_runtime, not just load."""
    from app.bootstrap import build_runtime, dispose_runtime

    monkeypatch.setattr(settings, "FILES_ENABLED", True)
    runtime = await build_runtime()
    try:
        service = runtime.services.file
        assert service is not None
        assert service._write_plugin is not None
        assert service._write_plugin.has_before("create") is True
    finally:
        await dispose_runtime(runtime)


async def test_bootstrap_rejects_a_bad_registration(monkeypatch):
    from app.bootstrap import build_runtime

    monkeypatch.setattr(settings, "FILE_WRITE_PLUGIN", "no_such_module_xyz:plugin")
    with pytest.raises(ValueError, match="FILE_WRITE_PLUGIN"):
        await build_runtime()


def test_settings_mode_rejects_unknown_value():
    with pytest.raises(ValidationError):
        Settings(FILE_WRITE_PLUGIN_MODE="silent")
