"""Snapshots of the public MCP and HTTP surface.

A changed snapshot is a contract change: review the diff, then refresh deliberately with
``uv run pytest -m snapshot --snapshot-update``.
"""

import pytest
from syrupy.extensions.json import JSONSnapshotExtension

pytestmark = pytest.mark.snapshot


@pytest.fixture
def json_snapshot(snapshot):
    return snapshot.use_extension(JSONSnapshotExtension)


async def test_meta_tool_signatures(mcp_client, json_snapshot):
    tools = await mcp_client.list_tools()
    surface = {
        tool.name: {"description": tool.description, "input_schema": tool.inputSchema}
        for tool in sorted(tools, key=lambda t: t.name)
    }
    assert surface == json_snapshot


async def test_discovered_tool_catalogue(mcp_client, json_snapshot):
    result = await mcp_client.call_tool("discover_forgetful_tools", {})
    assert result.data == json_snapshot


async def test_http_route_table(sqlite_app, mcp_client, json_snapshot):
    routes = sorted(
        f"{method} {route.path}"
        for route in sqlite_app.http_app().routes
        for method in sorted(getattr(route, "methods", None) or [])
        if method not in {"HEAD", "OPTIONS"}
    )
    assert routes == json_snapshot
