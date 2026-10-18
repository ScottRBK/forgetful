"""E2E tests (in-memory SQLite) for SKILL.md import/export YAML handling.

Exercises the REST routes and the MCP tool against the real SkillService and
SQLite repository: lossless export -> import, 400 responses for malformed
frontmatter and persistence of YAML-native values.
"""
import time

import pytest
from fastmcp.exceptions import ToolError


async def _import(http_client, skill_md):
    return await http_client.post("/api/v1/skills/import", json={"skill_md": skill_md})


async def test_rest_export_import_roundtrip_is_lossless(http_client):
    payload = {
        "name": "yaml-roundtrip",
        "description": "See https://example.com/docs/guide --- details: use this skill whenever asked",
        "content": "    indented first line\n\n---\n\ntail\n",
        "license": "MIT",
        "compatibility": "Needs https://pypi.org/simple access",
        "allowed_tools": ["Bash(git commit:*)", "Read"],
        "metadata": {"k": "v: w", "n": 3},
        "tags": ["t:1"],
        "importance": 7,
    }
    created = await http_client.post("/api/v1/skills", json=payload)
    assert created.status_code == 201, created.text
    skill_id = created.json()["id"]

    exported = await http_client.get(f"/api/v1/skills/{skill_id}/export")
    assert exported.status_code == 200, exported.text
    skill_md = exported.json()["skill_md"]
    assert (await http_client.delete(f"/api/v1/skills/{skill_id}")).status_code in (200, 204)

    imported = await _import(http_client, skill_md)

    assert imported.status_code == 201, imported.text
    data = imported.json()
    for field in (
        "name", "description", "content", "license", "compatibility",
        "allowed_tools", "metadata", "tags",
    ):
        assert data[field] == payload[field], field


@pytest.mark.parametrize(
    "description",
    ["[WIP] deploy things", "`deploy` things", "@deploy things", "!important deploy things"],
)
async def test_rest_import_malformed_yaml_returns_400(http_client, description):
    response = await _import(
        http_client, f"---\nname: bad-yaml\ndescription: {description}\n---\nbody",
    )

    assert response.status_code == 400, response.text
    assert "Invalid YAML frontmatter" in response.json()["error"]


async def test_rest_import_unquoted_date_metadata_is_stored_as_text(http_client):
    skill_md = (
        "---\nname: sk-date\ndescription: d\nmetadata:\n  updated: 2024-01-15\n"
        "  stamp: 2024-01-15 10:00:00\n---\nbody\n"
    )

    response = await _import(http_client, skill_md)

    assert response.status_code == 201, response.text
    assert response.json()["metadata"] == {
        "updated": "2024-01-15",
        "stamp": "2024-01-15 10:00:00",
    }


async def test_rest_import_non_json_metadata_returns_400(http_client):
    skill_md = "---\nname: odd-meta\ndescription: d\nmetadata:\n  k: !!set {a, b}\n---\nbody\n"

    response = await _import(http_client, skill_md)

    assert response.status_code == 400, response.text
    assert "metadata" in response.json()["error"]


async def test_rest_import_string_allowed_tools(http_client):
    skill_md = "---\nname: at-skill\ndescription: ok\nallowed-tools: Bash(git:*) Read\n---\nbody\n"

    response = await _import(http_client, skill_md)

    assert response.status_code == 201, response.text
    assert response.json()["allowed_tools"] == ["Bash(git:*)", "Read"]


async def test_rest_import_alias_bomb_is_rejected_quickly(http_client):
    lines = [
        "name: alias-bomb",
        "description: harmless looking skill",
        "a0: &a0 [" + ",".join(["x"] * 10) + "]",
    ]
    for i in range(1, 8):
        lines.append(f"a{i}: &a{i} [" + ",".join([f"*a{i - 1}"] * 10) + "]")
    lines.append("metadata: {k: *a7}")
    skill_md = "---\n" + "\n".join(lines) + "\n---\n\n# body\n"

    started = time.perf_counter()
    response = await _import(http_client, skill_md)

    assert response.status_code == 400, response.text[:200]
    assert "aliases" in response.json()["error"]
    assert time.perf_counter() - started < 1.5


async def test_mcp_import_malformed_yaml_reports_invalid_frontmatter(mcp_client):
    with pytest.raises(ToolError, match="Invalid YAML frontmatter"):
        await mcp_client.call_tool("execute_forgetful_tool", {
            "tool_name": "import_skill",
            "arguments": {
                "skill_md_content": "---\nname: bad-yaml\ndescription: [WIP] deploy\n---\nbody",
            },
        })


async def test_mcp_import_trailing_comment_with_colon(mcp_client):
    result = await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "import_skill",
        "arguments": {
            "skill_md_content": (
                "---\nname: commented\ndescription: Does things\n"
                "license: MIT # see: LICENSE file\n---\nbody\n"
            ),
        },
    })

    assert result.data["name"] == "commented"
    assert result.data["license"] == "MIT"
