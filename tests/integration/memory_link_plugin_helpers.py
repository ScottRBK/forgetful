"""Trusted synthetic registration; actual bootstrap, SQLite and HTTP/MCP transports."""

import sys
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from fastmcp import FastMCP

from app.bootstrap import build_runtime, dispose_runtime
from app.config.settings import settings
from app.routes.api import memories
from app.routes.mcp import meta_tools

REGISTRATION_SOURCE = """
import asyncio
from app.models.write_plugin_models import PluginWarning, WriteDecision
from app.protocols.write_plugin_protocol import MemoryLinkPlugin
before_calls = []
after_calls = []
async def before(request):
    before_calls.append(request.model_copy(deep=True))
    tags = request.target.tags
    if 'reject' in tags:
        return WriteDecision(outcome='reject', message='Synthetic target rejected.')
    if 'error' in tags:
        raise RuntimeError('SYNTHETIC_PRIVATE_ERROR')
    if 'timeout' in tags:
        await asyncio.Event().wait()
    if 'child_cancel' in tags:
        child = asyncio.create_task(asyncio.sleep(100))
        child.cancel()
        await child
    if 'mutate' in tags:
        request.source.title = 'rewritten'
        request.target.tags.clear()
    if 'warn' in tags:
        return WriteDecision(outcome='warn', message='Review synthetic link.', code='LINK_POLICY')
    return WriteDecision(outcome='allow')
async def after(request):
    after_calls.append(request.model_copy(deep=True))
    if any('post_error' in pair.target.tags for pair in request.pairs):
        raise RuntimeError('SYNTHETIC_PRIVATE_ERROR')
    if any('post_warn' in pair.target.tags for pair in request.pairs):
        return PluginWarning(message='Review changed links.', code='LINK_AFTER')
registration = MemoryLinkPlugin(
    before_save={'link': before, 'unlink': before},
    after_save={'link': after, 'unlink': after},
)
"""


@pytest.fixture
def link_runtime(sqlite_runtime_settings, monkeypatch, tmp_path):
    from test_memory_write_plugin import RecordingEmbeddings

    monkeypatch.setattr("app.bootstrap.get_embedding_adapter", RecordingEmbeddings)
    monkeypatch.setattr("app.bootstrap.check_first_run_models", lambda: None)
    for name in ("MEMORY_WRITE_PLUGIN", "ENTITY_WRITE_PLUGIN", "PLAN_WRITE_PLUGIN"):
        monkeypatch.setattr(settings, name, "")
    monkeypatch.setattr(settings, "MEMORY_NUM_AUTO_LINK", 0)
    monkeypatch.setattr(settings, "MEMORY_LINK_PLUGIN_MODE", "enforce")
    monkeypatch.setattr(settings, "MEMORY_LINK_PLUGIN_TIMEOUT_SECONDS", 5.0)
    monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "links.db"))
    name = f"synthetic_link_policy_{uuid4().hex}"
    (tmp_path / f"{name}.py").write_text(REGISTRATION_SOURCE)
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setattr(settings, "MEMORY_LINK_PLUGIN", f"{name}:registration")
    try:
        yield name
    finally:
        sys.modules.pop(name, None)


def link_app():
    @asynccontextmanager
    async def lifespan(app):
        runtime = await build_runtime()
        app.memory_service = runtime.services.memory
        app.user_service = runtime.services.user
        app.registry = runtime.registry
        app._instance_permitted_tools = runtime.permitted_tools
        app._instance_scopes = runtime.instance_scopes
        try:
            yield
        finally:
            await dispose_runtime(runtime)

    app = FastMCP("Synthetic Memory Link policies", lifespan=lifespan)
    meta_tools.register(app)
    memories.register(app)
    return app


async def execute(client, name, arguments):
    return (await client.call_tool("execute_forgetful_tool", {
        "tool_name": name, "arguments": arguments,
    })).data


def memory_arguments(title, tags=None):
    return {"title": title, "content": "Synthetic fact", "context": "Link test",
            "keywords": [], "tags": tags or [], "importance": 7}
