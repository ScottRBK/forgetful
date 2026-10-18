"""Production bootstrap loads one trusted async handler before constructing resources."""

import importlib

import pytest

from app.bootstrap import build_runtime, dispose_runtime
from app.config.settings import settings
from app.models.memory_models import MemoryCreate
from app.models.user_models import UserCreate


@pytest.fixture
def plugin_runtime(sqlite_runtime_settings, monkeypatch, tmp_path):
    from test_memory_write_plugin import RecordingEmbeddings

    monkeypatch.setattr("app.bootstrap.get_embedding_adapter", RecordingEmbeddings)
    monkeypatch.setattr("app.bootstrap.check_first_run_models", lambda: None)
    monkeypatch.syspath_prepend(str(tmp_path))
    module_name = "runtime_write_checks"
    (tmp_path / f"{module_name}.py").write_text("""
from app.models.write_plugin_models import WriteDecision
loads = 0
calls = []
async def decide(request):
    calls.append(request)
    if "blocked" in request.proposed.tags or request.proposed.content == "blocked":
        return WriteDecision(outcome="reject", message="Remove the blocked tag.")
    if "warn" in request.proposed.tags or request.proposed.content == "warn":
        return WriteDecision(outcome="warn", message="Check the source.", code="source")
    if "error" in request.proposed.tags:
        raise RuntimeError("SECRET")
    return WriteDecision(outcome="allow")
def __getattr__(name):
    global loads
    if name == "check_write":
        loads += 1
        return decide
    raise AttributeError(name)
def sync_handler(request):
    return WriteDecision(outcome="allow")
""")
    monkeypatch.setattr(settings, "MEMORY_WRITE_PLUGIN", f"{module_name}:check_write")
    monkeypatch.setattr(settings, "MEMORY_WRITE_PLUGIN_MODE", "enforce")
    monkeypatch.setattr(settings, "MEMORY_WRITE_PLUGIN_TIMEOUT_SECONDS", 5.0)
    yield module_name
    import sys
    sys.modules.pop(module_name, None)


async def runtime_user(runtime):
    return await runtime.services.user.get_or_create_user(UserCreate(
        external_id=settings.DEFAULT_USER_ID, name=settings.DEFAULT_USER_NAME,
        email=settings.DEFAULT_USER_EMAIL,
    ))


def data(tags=None):
    return MemoryCreate(title="Runtime test", content="A fact", context="Testing",
                        keywords=[], tags=tags or [], importance=7)


async def test_runtime_plugin_controls_writes_and_loads_once(plugin_runtime):
    from app.exceptions import WritePluginRejectedError

    runtime = await build_runtime()
    try:
        user = await runtime_user(runtime)
        await runtime.services.memory.create_memory(user.id, data())
        with pytest.raises(WritePluginRejectedError, match="Remove the blocked tag"):
            await runtime.services.memory.create_memory(user.id, data(["blocked"]))
        _, total = await runtime.services.memory.list_memories(user.id)
        assert total == 1
        module = importlib.import_module(plugin_runtime)
        assert module.loads == 1
        assert len(module.calls) == 2
    finally:
        await dispose_runtime(runtime)


@pytest.mark.parametrize("reference", ["missing_plugin:check", "runtime_write_checks:sync_handler",
                                       "/plugins/checks.py:check", "runtime_write_checks:missing"])
async def test_invalid_reference_fails_startup_even_in_warn_mode(
    plugin_runtime, monkeypatch, reference,
):
    monkeypatch.setattr(settings, "MEMORY_WRITE_PLUGIN", reference)
    monkeypatch.setattr(settings, "MEMORY_WRITE_PLUGIN_MODE", "warn")
    with pytest.raises(ValueError, match="MEMORY_WRITE_PLUGIN"):
        runtime = await build_runtime()
        await dispose_runtime(runtime)


async def test_empty_reference_disables_plugin(plugin_runtime, monkeypatch):
    monkeypatch.setattr(settings, "MEMORY_WRITE_PLUGIN", "")
    runtime = await build_runtime()
    try:
        user = await runtime_user(runtime)
        result = await runtime.services.memory.create_memory(user.id, data(["blocked"]))
        assert result.memory.tags == ["blocked"]
        assert result.plugin_warnings == []
    finally:
        await dispose_runtime(runtime)


async def test_runtime_unavailable_logs_safe_diagnostics(plugin_runtime, capsys):
    from app.exceptions import WritePluginUnavailableError

    runtime = await build_runtime()
    try:
        user = await runtime_user(runtime)
        with pytest.raises(WritePluginUnavailableError):
            await runtime.services.memory.create_memory(user.id, data(["error"]))
        diagnostics = capsys.readouterr().err
        assert "Memory Write Plugin unavailable" in diagnostics
        assert "RuntimeError" in diagnostics
        assert "SECRET" not in diagnostics
    finally:
        await dispose_runtime(runtime)


@pytest.mark.parametrize("overrides", [
    {"MEMORY_WRITE_PLUGIN_MODE": "invalid"},
    {"MEMORY_WRITE_PLUGIN_TIMEOUT_SECONDS": 0},
    {"MEMORY_WRITE_PLUGIN_TIMEOUT_SECONDS": float("inf")},
])
async def test_invalid_configuration_prevents_runtime_start(plugin_runtime, monkeypatch, overrides):
    from pydantic import ValidationError

    from app.config.settings import Settings

    with pytest.raises(ValidationError):
        config = Settings(_env_file=None, **overrides)
        monkeypatch.setattr("app.bootstrap.settings", config)
        runtime = await build_runtime()
        await dispose_runtime(runtime)
