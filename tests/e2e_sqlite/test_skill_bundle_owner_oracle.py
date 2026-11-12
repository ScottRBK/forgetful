"""Baseline-compatible owner-report assertions, with a working roundtrip control."""
import base64
import sys

import pytest
from fastmcp.exceptions import ToolError

from app.config.settings import settings
from tests.skill_bundle_cases import call_tool, skill_bundle

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def features(monkeypatch):
    monkeypatch.setattr(settings, "SKILLS_ENABLED", True)
    monkeypatch.setattr(settings, "FILES_ENABLED", True)


@pytest.fixture
def bundle_app(sqlite_app):
    return sqlite_app


async def test_owner_nested_schema(mcp_client):
    info = await mcp_client.call_tool("how_to_use_forgetful_tool", {"tool_name": "import_skill_bundle"})
    assert "BundleFile" in info.data["json_schema"].get("$defs", {}), "feedback_nested_schema"


async def test_owner_permission(mcp_client, bundle_app, monkeypatch):
    from app.routes.mcp.scope_resolver import parse_scopes, resolve_permitted_tools
    value = skill_bundle("permission-oracle")
    value["resources"] = [value["resources"][2]]
    value["resources"][0]["tags"] = ["CONFIDENTIAL"]
    created = await call_tool(mcp_client, "import_skill_bundle", bundle=value)
    await call_tool(mcp_client, "update_file", file_id=created["members"][0]["resource_id"], description="binary" + chr(0))
    scopes = parse_scopes("read:skills")
    monkeypatch.setattr(bundle_app, "_instance_scopes", scopes, raising=False)
    monkeypatch.setattr(bundle_app, "_instance_permitted_tools", resolve_permitted_tools(scopes, bundle_app.registry), raising=False)
    caught = ""
    try:
        await call_tool(mcp_client, "export_skill_bundle", skill_id=created["skill"]["id"])
    except ToolError as error:
        caught = str(error)
    assert "get_file" in caught and "CONFIDENTIAL" not in caught, "feedback_permission_before_conversion"


async def test_owner_budget(mcp_client, bundle_app, monkeypatch):
    value = skill_bundle("budget-oracle")
    value["resources"] = [value["resources"][2]]
    value["resources"][0]["data"] = base64.b64encode(b"x" * 1024).decode()
    created = await call_tool(mcp_client, "import_skill_bundle", bundle=value)
    module = sys.modules[bundle_app.skill_service.skill_repo.__module__]
    convert = module.file_model
    calls = []
    monkeypatch.setattr(module, "file_model", lambda row: (calls.append(True), convert(row))[1])
    monkeypatch.setattr(settings, "SKILL_BUNDLE_MAX_BYTES", 512)
    with pytest.raises(ToolError, match="SKILL_BUNDLE_MAX_BYTES"):
        await call_tool(mcp_client, "export_skill_bundle", skill_id=created["skill"]["id"], members=[dict(created["members"][0], path=f"assets/copy-{i}.bin") for i in range(100)])
    assert calls == [], "feedback_budget_before_conversion"


async def test_owner_canonical(mcp_client, monkeypatch):
    monkeypatch.setattr(settings, "SKILL_BUNDLE_MAX_BYTES", 32)
    rejected = False
    try:
        await call_tool(mcp_client, "import_skill_bundle", bundle={"schema_version": 1, "skill_md": "---\nname: x\ndescription: x\n---\nx", "resources": []})
    except ToolError:
        rejected = True
    assert rejected, "feedback_canonical_before_commit"
    assert (await call_tool(mcp_client, "list_skills"))["skills"] == []


async def test_owner_control(mcp_client):
    created = await call_tool(mcp_client, "import_skill_bundle", bundle=skill_bundle("owner-control"))
    exported = await call_tool(mcp_client, "export_skill_bundle", skill_id=created["skill"]["id"])
    assert len(exported["resources"]) == 3
