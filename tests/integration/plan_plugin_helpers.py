"""Synthetic trusted registration and real runtime wiring for Plan transport tests."""

import socket
import sys
import threading
import time
from contextlib import asynccontextmanager, contextmanager
from uuid import uuid4

import pytest
import uvicorn
from fastmcp import FastMCP

from app.bootstrap import build_runtime, dispose_runtime
from app.config.settings import settings
from app.routes.api import plans, projects, tasks
from app.routes.mcp import meta_tools

REGISTRATION_SOURCE = """
from app.models.write_plugin_models import PluginWarning, WriteDecision
from app.protocols.plan_plugin_protocol import PlanPlugin
loads = 0
before_calls = []
after_calls = []
async def before(request):
    before_calls.append(request.model_copy(deep=True))
    candidate = request.previous if request.operation == "delete" else request.proposed
    marker = candidate.title
    if "blocked" in marker:
        return WriteDecision(outcome="reject", message="Synthetic plan rejected.", code="PLAN_POLICY")
    if "error" in marker and "post_error" not in marker:
        raise RuntimeError("SYNTHETIC_PRIVATE_ERROR")
    if "warn" in marker:
        return WriteDecision(outcome="warn", message="Review synthetic plan.", code="PLAN_POLICY")
    return WriteDecision(outcome="allow")
async def after(request):
    after_calls.append(request.model_copy(deep=True))
    snapshot = request.previous if request.operation == "delete" else request.saved
    if "post_error" in snapshot.title:
        raise RuntimeError("SYNTHETIC_PRIVATE_ERROR")
    if "post_warn" in snapshot.title:
        return PluginWarning(message="Review saved synthetic plan.", code="PLAN_AFTER")
def __getattr__(name):
    global loads
    if name != "registration":
        raise AttributeError(name)
    loads += 1
    return PlanPlugin(
        before_save={op: before for op in ("create", "update", "delete")},
        after_save={op: after for op in ("create", "update", "delete")},
    )
"""


@pytest.fixture
def plan_runtime(sqlite_runtime_settings, monkeypatch, tmp_path):
    from test_memory_write_plugin import RecordingEmbeddings

    monkeypatch.setattr("app.bootstrap.get_embedding_adapter", RecordingEmbeddings)
    monkeypatch.setattr("app.bootstrap.check_first_run_models", lambda: None)
    monkeypatch.setattr(settings, "PLANNING_ENABLED", True)
    monkeypatch.setattr(settings, "MEMORY_WRITE_PLUGIN", "")
    monkeypatch.setattr(settings, "PLAN_WRITE_PLUGIN_MODE", "enforce")
    monkeypatch.setattr(settings, "PLAN_WRITE_PLUGIN_TIMEOUT_SECONDS", 5.0)
    monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "plan-transport.db"))
    name = f"synthetic_plan_policy_{uuid4().hex}"
    (tmp_path / f"{name}.py").write_text(REGISTRATION_SOURCE)
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setattr(settings, "PLAN_WRITE_PLUGIN", f"{name}:registration")
    try:
        yield name
    finally:
        sys.modules.pop(name, None)


def plan_app():
    @asynccontextmanager
    async def lifespan(app):
        runtime = await build_runtime()
        app.plan_service = runtime.services.plan
        app.task_service = runtime.services.task
        app.project_service = runtime.services.project
        app.user_service = runtime.services.user
        app.registry = runtime.registry
        app._instance_permitted_tools = runtime.permitted_tools
        app._instance_scopes = runtime.instance_scopes
        try:
            yield
        finally:
            await dispose_runtime(runtime)

    app = FastMCP("Synthetic Plan policy tests", lifespan=lifespan)
    meta_tools.register(app)
    plans.register(app)
    projects.register(app)
    tasks.register(app)
    return app


async def execute_tool(client, tool_name, arguments):
    result = await client.call_tool(
        "execute_forgetful_tool", {"tool_name": tool_name, "arguments": arguments},
    )
    return result.data


@contextmanager
def loopback_plan_server(app):
    """Use the upstream real-HTTP fixture's independently bounded server loop."""
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    sock.listen()
    port = sock.getsockname()[1]
    config = uvicorn.Config(
        app.http_app(), log_level="error", lifespan="on", timeout_graceful_shutdown=2,
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 15
        while not server.started:
            if time.monotonic() >= deadline or not thread.is_alive():
                raise RuntimeError("Synthetic HTTP server stopped before readiness")
            time.sleep(0.01)
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=15)
        sock.close()
        if thread.is_alive():
            raise RuntimeError("Synthetic HTTP server failed to stop within 15 seconds")
