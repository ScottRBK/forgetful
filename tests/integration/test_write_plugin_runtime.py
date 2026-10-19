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


async def test_runtime_unavailable_logs_safe_diagnostics(plugin_runtime, caplog):
    from app.exceptions import WritePluginUnavailableError

    runtime = await build_runtime()
    try:
        user = await runtime_user(runtime)
        with pytest.raises(WritePluginUnavailableError):
            await runtime.services.memory.create_memory(user.id, data(["error"]))
        diagnostics = caplog.text
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
def test_settings_reject_invalid_write_plugin_values(overrides):
    from pydantic import ValidationError

    from app.config.settings import Settings

    with pytest.raises(ValidationError):
        Settings(_env_file=None, **overrides)


@pytest.mark.parametrize("reexport", [False, True])
async def test_runtime_preserves_plugin_module_diagnostics(
    plugin_runtime, tmp_path, monkeypatch, caplog, reexport,
):
    import sys
    from uuid import uuid4

    configured_module = f"plugin_logs_{uuid4().hex}"
    handler_module = f"{configured_module}_impl" if reexport else configured_module
    (tmp_path / f"{handler_module}.py").write_text(f"""
import logging
from app.models.write_plugin_models import WriteDecision
logger = logging.getLogger(__name__)
child = logging.getLogger(__name__ + ".child")
muted = logging.getLogger(__name__ + ".muted")
muted.disabled = True
async def check_write(request):
    logger.warning("Safe handler diagnostic")
    child.warning("Safe child diagnostic")
    muted.warning("Muted diagnostic must stay disabled")
    logging.getLogger("{configured_module}").warning("Safe configured-module diagnostic")
    return WriteDecision(outcome="allow")
""")
    if reexport:
        (tmp_path / f"{configured_module}.py").write_text(
            "import logging\nlogger = logging.getLogger(__name__)\n"
            f"from {handler_module} import check_write\n",
        )
    monkeypatch.setattr(settings, "MEMORY_WRITE_PLUGIN", f"{configured_module}:check_write")
    runtime = await build_runtime()
    try:
        user = await runtime_user(runtime)
        result = await runtime.services.memory.create_memory(user.id, data())
        diagnostics = caplog.text
        assert result.memory.title == "Runtime test"
        assert "Safe handler diagnostic" in diagnostics
        assert "Safe child diagnostic" in diagnostics
        assert "Safe configured-module diagnostic" in diagnostics
        assert "Muted diagnostic must stay disabled" not in diagnostics
    finally:
        await dispose_runtime(runtime)
        sys.modules.pop(configured_module, None)
        sys.modules.pop(handler_module, None)


@pytest.mark.parametrize("source,phase,error_type", [
    ('raise RuntimeError("SECRET import detail")\n', "import", "RuntimeError"),
    ("import missing_plugin_dependency\n", "import", "ModuleNotFoundError"),
    ("value = 1\n", "attribute lookup", "AttributeError"),
    ('def __getattr__(name):\n    raise RuntimeError("SECRET lookup detail")\n',
     "attribute lookup", "RuntimeError"),
])
async def test_startup_identifies_failed_plugin_without_exception_details(
    plugin_runtime, tmp_path, monkeypatch, source, phase, error_type,
):
    import sys
    import traceback
    from uuid import uuid4

    module_name = f"broken_plugin_{uuid4().hex}"
    (tmp_path / f"{module_name}.py").write_text(source)
    monkeypatch.setattr(settings, "MEMORY_WRITE_PLUGIN", f"{module_name}:check_write")
    try:
        with pytest.raises(ValueError, match="MEMORY_WRITE_PLUGIN") as failure:
            await build_runtime()
        message = str(failure.value)
        assert module_name in message
        assert phase in message
        assert error_type in message
        assert "SECRET" not in "".join(traceback.format_exception(failure.value))
    finally:
        sys.modules.pop(module_name, None)
