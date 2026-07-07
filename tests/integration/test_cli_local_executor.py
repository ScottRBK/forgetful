"""Integration tests for LocalExecutor (docs/dev/cli_plan.md phase 3)

LocalExecutor drives the same ToolRegistry the MCP meta-tools execute, through the
CliContext shim (default user, no auth) with the FORGETFUL_SCOPES ceiling applied.
Uses the real composition root against in-memory SQLite.
"""
import pytest
from fastmcp.exceptions import ToolError

from app.bootstrap import build_runtime
from app.config.settings import settings
from app.routes.cli.local_executor import LocalExecutor


@pytest.fixture
async def local_executor(sqlite_runtime_settings):
    executor = LocalExecutor(await build_runtime())
    yield executor
    await executor.close()


async def test_execute_create_then_get_memory_roundtrips(local_executor):
    created = await local_executor.execute(
        "create_memory",
        {
            "title": "CLI executor memory",
            "content": "Created through LocalExecutor against the in-process registry",
            "context": "Verifying the CLI executes the same registry as the meta-tools",
            "keywords": ["cli", "executor"],
            "tags": ["testing"],
            "importance": 5,
        },
    )

    assert created.id is not None

    fetched = await local_executor.execute("get_memory", {"memory_id": created.id})
    assert fetched.id == created.id
    assert fetched.title == "CLI executor memory"


async def test_execute_unknown_tool_raises_error_naming_available_tools(local_executor):
    with pytest.raises(ToolError) as excinfo:
        await local_executor.execute("definitely_not_a_tool", {})

    message = str(excinfo.value)
    assert "Tool 'definitely_not_a_tool' not found in registry" in message
    assert "Available tools (first 10):" in message


async def test_scope_ceiling_denies_write_tool_with_required_scope(sqlite_runtime_settings):
    settings.FORGETFUL_SCOPES = "read"
    executor = LocalExecutor(await build_runtime())

    try:
        with pytest.raises(ToolError) as excinfo:
            await executor.execute(
                "create_memory",
                {
                    "title": "Denied",
                    "content": "Should never be written",
                    "context": "Scope ceiling test",
                    "keywords": ["denied"],
                    "tags": [],
                    "importance": 1,
                },
            )

        message = str(excinfo.value)
        assert "not permitted under current scopes" in message
        assert "write:memories" in message
    finally:
        await executor.close()


async def test_list_tools_and_tool_info_expose_registry_metadata(local_executor):
    listing = await local_executor.list_tools()
    assert listing["total_count"] > 0
    assert "memory" in listing["tools_by_category"]

    filtered = await local_executor.list_tools(category="memory")
    assert set(filtered["tools_by_category"].keys()) == {"memory"}
    assert filtered["filtered_by"] == "memory"

    info = await local_executor.tool_info("query_memory")
    assert info["name"] == "query_memory"
    assert any(param["name"] == "query" for param in info["parameters"])
