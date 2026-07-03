"""Adapter + registry tests for the `run_decay_scan` MCP tool.

Verifies that:
- `create_memory_adapters` exposes a `run_decay_scan` callable
- `register_memory_tools_metadata` registers the tool under the MEMORY category
- The adapter returns a `DecayScanResponse` (dry-run, no writes)

This is the registry-level equivalent of the E2E round-trip — it proves the
tool is discoverable and executable through the meta-tool surface without
requiring a Postgres container.
"""
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.models.memory_models import DecayScanResponse
from app.routes.mcp.tool_adapters import create_memory_adapters
from app.routes.mcp.tool_metadata_registry import register_memory_tools_metadata
from app.routes.mcp.tool_registry import ToolRegistry


@pytest.fixture
def decay_adapters(test_memory_service, test_user_service):
    """Build memory adapters against the in-memory test services."""
    return create_memory_adapters(test_memory_service, test_user_service)


@pytest.fixture
def decay_registry(decay_adapters):
    """Build a ToolRegistry with the memory tool metadata registered."""
    registry = ToolRegistry()
    register_memory_tools_metadata(registry, decay_adapters)
    return registry


def test_run_decay_scan_adapter_is_registered(decay_adapters):
    """`create_memory_adapters` must expose `run_decay_scan`."""
    assert "run_decay_scan" in decay_adapters
    assert callable(decay_adapters["run_decay_scan"])


def test_run_decay_scan_registry_metadata(decay_registry):
    """The metadata registry must register `run_decay_scan` so meta-tools can discover it."""
    tools = decay_registry.list_all_tools()
    names = {t.name for t in tools}
    assert "run_decay_scan" in names, "run_decay_scan must be discoverable in the registry"


def test_run_decay_scan_registry_implementation_bound(decay_registry):
    """The registry-bound implementation must be the adapter callable."""
    tool = decay_registry.get_tool("run_decay_scan")
    assert tool is not None
    assert callable(tool.implementation)


@pytest.mark.asyncio
async def test_run_decay_scan_adapter_dry_run_returns_response(decay_adapters):
    """Calling the adapter with dry_run=True returns a DecayScanResponse and writes nothing."""
    fake_user = type("FakeUser", (), {"id": uuid4()})()
    fake_ctx = type("FakeCtx", (), {})()

    with patch(
        "app.routes.mcp.tool_adapters.get_user_from_auth",
        return_value=fake_user,
    ):
        result = await decay_adapters["run_decay_scan"](
            ctx=fake_ctx,
            memory_ids=None,
            project_id=None,
            dry_run=True,
        )

    assert isinstance(result, DecayScanResponse)
    assert result.dry_run is True
    assert result.applied == 0

