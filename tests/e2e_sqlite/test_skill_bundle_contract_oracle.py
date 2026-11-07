"""Baseline-compatible feature-contract evidence; no new product imports."""
import pytest

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("tool", ["import_skill_bundle", "export_skill_bundle"])
async def test_bundle_registry_contract(mcp_client, tool):
    found = await mcp_client.call_tool("discover_forgetful_tools", {})
    names = {entry["name"] for entries in found.data["tools_by_category"].values() for entry in entries}
    assert tool in names, "missing_bundle_tool_" + tool


async def test_original_markdown_control(mcp_client):
    created = await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "import_skill", "arguments": {"skill_md_content":
            "---\nname: bundle-control\ndescription: Baseline Markdown control\n---\n\nUnchanged body."},
    })
    assert created.data["name"] == "bundle-control"
    exported = await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "export_skill", "arguments": {"skill_id": created.data["id"]},
    })
    assert exported.content and "Unchanged body." in exported.content[0].text
