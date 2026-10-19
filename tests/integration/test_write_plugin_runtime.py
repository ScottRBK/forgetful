"""Production bootstrap loads one explicit registration before constructing resources."""

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
from app.models.write_plugin_models import PluginWarning, WriteDecision
from app.protocols.write_plugin_protocol import MemoryPlugin
loads = 0
calls = []
after_calls = []
async def decide(request):
    calls.append(request)
    if "blocked" in request.proposed.tags or request.proposed.content == "blocked":
        return WriteDecision(outcome="reject", message="Remove the blocked tag.")
    if "warn" in request.proposed.tags or request.proposed.content == "warn":
        return WriteDecision(outcome="warn", message="Check the source.", code="source")
    if "error" in request.proposed.tags:
        raise RuntimeError("SECRET")
    return WriteDecision(outcome="allow")
async def lifecycle(request):
    calls.append(request)
    tags = request.previous.tags
    if request.operation + "_blocked" in tags:
        return WriteDecision(outcome="reject", message="Keep this state.")
    if request.operation + "_error" in tags:
        raise RuntimeError("SECRET")
    if request.operation + "_warn" in tags:
        return WriteDecision(outcome="warn", message="Check the lifecycle change.")
    return WriteDecision(outcome="allow")
async def after(request):
    after_calls.append(request)
    if "post_error" in request.saved.tags:
        raise RuntimeError("SECRET")
    if "post_warn" in request.saved.tags:
        return PluginWarning(message="Review saved memory.", code="review")
def __getattr__(name):
    global loads
    if name == "check_write":
        loads += 1
        return MemoryPlugin(
            before_save={"create": decide, "update": decide,
                         "obsolete": lifecycle, "restore": lifecycle},
            after_save={operation: after for operation in
                        ("create", "update", "obsolete", "restore")},
        )
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
                                       "runtime_write_checks:decide",
                                       "/plugins/checks.py:check", "runtime_write_checks:missing"])
async def test_invalid_reference_fails_startup_even_in_warn_mode(
    plugin_runtime, monkeypatch, reference,
):
    monkeypatch.setattr(settings, "MEMORY_WRITE_PLUGIN", reference)
    monkeypatch.setattr(settings, "MEMORY_WRITE_PLUGIN_MODE", "warn")
    with pytest.raises(ValueError, match="MEMORY_WRITE_PLUGIN"):
        runtime = await build_runtime()
        await dispose_runtime(runtime)


@pytest.mark.parametrize("registration", [
    'before_save={"delete": decide}',
    'after_save={"link": decide}',
    'before_save={"create": sync_handler}',
    'after_save={"update": missing_argument}',
    'before_save={"create": extra_argument}',
    "after_save=[]",
])
async def test_invalid_registration_fails_startup(
    plugin_runtime, tmp_path, monkeypatch, registration,
):
    import sys
    from uuid import uuid4

    module_name = f"invalid_registration_{uuid4().hex}"
    source = (
        "from app.protocols.write_plugin_protocol import MemoryPlugin\n"
        f"from {plugin_runtime} import decide, sync_handler\n"
        "async def missing_argument(): pass\n"
        "async def extra_argument(request, required): pass\n"
        f"plugin = MemoryPlugin({registration})\n"
    )
    (tmp_path / f"{module_name}.py").write_text(source)
    monkeypatch.setattr(settings, "MEMORY_WRITE_PLUGIN", f"{module_name}:plugin")
    monkeypatch.setattr(settings, "MEMORY_WRITE_PLUGIN_MODE", "warn")

    try:
        with pytest.raises(ValueError, match="MEMORY_WRITE_PLUGIN.*ValueError"):
            await build_runtime()
    finally:
        sys.modules.pop(module_name, None)


def test_registration_validates_the_mapping_it_keeps():
    from app.protocols.write_plugin_protocol import MemoryPlugin

    async def after(request):
        return None

    class StaleItems(dict):
        def items(self):
            return {"create": after}.items()

    handlers = StaleItems(create=lambda request: None)

    with pytest.raises(ValueError, match="after_save handlers must be async functions"):
        MemoryPlugin(after_save=handlers)


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


async def test_registration_dispatches_only_selected_operations(plugin_runtime, monkeypatch):
    from app.models.memory_models import MemoryUpdate
    from app.protocols.write_plugin_protocol import MemoryPlugin

    module = importlib.import_module(plugin_runtime)
    module.selected = MemoryPlugin(before_save={"create": module.decide})
    monkeypatch.setattr(settings, "MEMORY_WRITE_PLUGIN", f"{plugin_runtime}:selected")

    runtime = await build_runtime()
    try:
        user = await runtime_user(runtime)
        created = await runtime.services.memory.create_memory(user.id, data())
        updated = await runtime.services.memory.update_memory(
            user.id, created.memory.id, MemoryUpdate(tags=["blocked"]),
        )
        assert updated.memory.tags == ["blocked"]
        assert updated.plugin_warnings == []
        assert [request.operation for request in module.calls] == ["create"]
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
def test_settings_reject_invalid_write_plugin_values(overrides):
    from pydantic import ValidationError

    from app.config.settings import Settings

    with pytest.raises(ValidationError):
        Settings(_env_file=None, **overrides)


@pytest.mark.parametrize("reexport,use_partial", [(False, False), (True, False), (True, True)])
async def test_runtime_preserves_plugin_module_diagnostics(
    plugin_runtime, tmp_path, monkeypatch, capsys, reexport, use_partial,
):
    import sys
    from uuid import uuid4

    configured_module = f"plugin_logs_{uuid4().hex}"
    handler_module = f"{configured_module}_impl" if reexport else configured_module
    (tmp_path / f"{handler_module}.py").write_text(f"""
import logging
from functools import partial
from app.models.write_plugin_models import WriteDecision
from app.protocols.write_plugin_protocol import MemoryPlugin
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
handler = partial(check_write) if {use_partial} else check_write
plugin = MemoryPlugin(before_save={{"create": handler}})
""")
    if reexport:
        (tmp_path / f"{configured_module}.py").write_text(
            "import logging\nlogger = logging.getLogger(__name__)\n"
            f"from {handler_module} import plugin\n",
        )
    monkeypatch.setattr(settings, "MEMORY_WRITE_PLUGIN", f"{configured_module}:plugin")
    runtime = await build_runtime()
    try:
        user = await runtime_user(runtime)
        result = await runtime.services.memory.create_memory(user.id, data())
        diagnostics = capsys.readouterr().err
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
