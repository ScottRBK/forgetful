"""End-to-end SQLite tests for the `run_decay_scan` MCP tool.

Verifies the full stack: HTTP → FastMCP Client → MCP Protocol → Meta-tools
(discover + execute) → Service → SQLite repository → schema.

Requires the SQLite MCP server fixture (see tests/e2e_sqlite/conftest.py).
"""
import pytest


@pytest.mark.asyncio
async def test_run_decay_scan_is_discoverable_e2e(mcp_client):
    """`discover_forgetful_tools` must list `run_decay_scan` under the memory category."""
    result = await mcp_client.call_tool(
        "discover_forgetful_tools",
        {"category": "memory"},
    )
    assert result.data is not None
    memory_tools = result.data["tools_by_category"]["memory"]
    names = {t["name"] for t in memory_tools}
    assert "run_decay_scan" in names, "run_decay_scan must be discoverable via meta-tools"


@pytest.mark.asyncio
async def test_run_decay_scan_dry_run_e2e(mcp_client):
    """`execute_forgetful_tool('run_decay_scan', {dry_run: true})` must return a preview."""
    # First create a memory so the scan has something to look at
    create_result = await mcp_client.call_tool(
        "execute_forgetful_tool",
        {
            "tool_name": "create_memory",
            "arguments": {
                "title": "Decay scan E2E stub",
                "content": "Memory used to verify the run_decay_scan MCP tool",
                "context": "E2E test for run_decay_scan",
                "keywords": ["decay", "e2e"],
                "tags": ["test"],
                "importance": 5,
            },
        },
    )
    assert create_result.data is not None
    memory_id = (
        create_result.data["id"]
        if isinstance(create_result.data, dict)
        else create_result.data.id
    )

    # Dry-run scan scoped to the freshly created memory
    result = await mcp_client.call_tool(
        "execute_forgetful_tool",
        {
            "tool_name": "run_decay_scan",
            "arguments": {
                "memory_ids": [memory_id],
                "dry_run": True,
            },
        },
    )
    assert result.data is not None
    data = result.data if isinstance(result.data, dict) else result.data.model_dump()
    assert data["dry_run"] is True
    assert data["scanned"] >= 1
    assert data["applied"] == 0
    # A freshly created memory is too recent to decay -> at least one skip action
    kinds = {a["kind"] for a in data["actions"]}
    assert "skip" in kinds or len(data["actions"]) == 0


@pytest.mark.asyncio
async def test_run_decay_scan_live_e2e(mcp_client):
    """`execute_forgetful_tool('run_decay_scan', {dry_run: false})` executes without error."""
    # Create a fresh memory; live scan on a fresh memory is a no-op (skip)
    create_result = await mcp_client.call_tool(
        "execute_forgetful_tool",
        {
            "tool_name": "create_memory",
            "arguments": {
                "title": "Decay scan E2E live stub",
                "content": "Memory used to verify live run_decay_scan",
                "context": "E2E test for live run_decay_scan",
                "keywords": ["decay", "e2e"],
                "tags": ["test"],
                "importance": 5,
            },
        },
    )
    assert create_result.data is not None
    memory_id = (
        create_result.data["id"]
        if isinstance(create_result.data, dict)
        else create_result.data.id
    )

    result = await mcp_client.call_tool(
        "execute_forgetful_tool",
        {
            "tool_name": "run_decay_scan",
            "arguments": {
                "memory_ids": [memory_id],
                "dry_run": False,
            },
        },
    )
    assert result.data is not None
    data = result.data if isinstance(result.data, dict) else result.data.model_dump()
    assert data["dry_run"] is False
    assert data["scanned"] >= 1
