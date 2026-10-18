"""E2E (SQLite) hardening of the three MCP meta-tools.

- database failures reach the client as short messages, never SQL, bound parameters or ids
- every category advertised by discover_forgetful_tools lists tools
"""

import re

import pytest
from fastmcp.exceptions import ToolError

from app.routes.mcp.meta_tools import _build_category_list
from app.routes.mcp.tool_errors import CONSTRAINT_FAILURE, GENERIC_FAILURE

UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE)
SECRET_DESCRIPTION = "SECRET-DESC-9f2c"
SECRET_CONTENT = "SECRET-CONTENT-BODY-7a1d"
LEAK_MARKERS = (
    "[SQL:",
    "[parameters:",
    "sqlalche.me",
    "INSERT INTO",
    "sqlite3.",
    "IntegrityError",
    "UNIQUE constraint failed",
    "FOREIGN KEY constraint failed",
    "too large to convert",
    SECRET_DESCRIPTION,
    SECRET_CONTENT,
)


def assert_no_leak(message: str) -> None:
    leaked = [marker for marker in LEAK_MARKERS if marker in message]
    assert not leaked, f"driver text leaked to the client ({leaked}): {message[:400]!r}"
    assert not UUID_RE.search(message), f"internal id leaked to the client: {message[:400]!r}"


async def execute(client, tool_name: str, arguments: dict):
    return await client.call_tool(
        "execute_forgetful_tool", {"tool_name": tool_name, "arguments": arguments},
    )


async def tool_error(client, tool_name: str, arguments: dict) -> str:
    with pytest.raises(ToolError) as caught:
        await execute(client, tool_name, arguments)
    return str(caught.value)


class TestExecuteErrorsAreSanitised:
    """execute_forgetful_tool keeps domain messages and hides database details."""

    async def test_foreign_key_failure_returns_constraint_message(self, mcp_client):
        message = await tool_error(
            mcp_client,
            "create_document",
            {
                "title": "t",
                "description": SECRET_DESCRIPTION,
                "content": SECRET_CONTENT,
                "document_type": "text",
                "project_id": 9999,
            },
        )

        assert_no_leak(message)
        assert message.startswith("Failed to execute 'create_document'")
        assert CONSTRAINT_FAILURE in message

    async def test_code_artifact_with_unknown_project_is_sanitised(self, mcp_client):
        message = await tool_error(
            mcp_client,
            "create_code_artifact",
            {
                "title": "t",
                "description": "d",
                "code": "print(1)",
                "language": "python",
                "project_id": 9999,
            },
        )

        assert_no_leak(message)
        assert CONSTRAINT_FAILURE in message

    async def test_duplicate_entity_relationship_is_sanitised(self, mcp_client):
        ids = []
        for name in ("dup-a", "dup-b"):
            created = await execute(
                mcp_client, "create_entity",
                {"name": name, "entity_type": "Individual", "tags": []},
            )
            ids.append(created.data["id"])
        relationship = {
            "source_entity_id": ids[0],
            "target_entity_id": ids[1],
            "relationship_type": "works_with",
        }
        await execute(mcp_client, "create_entity_relationship", relationship)

        message = await tool_error(mcp_client, "create_entity_relationship", relationship)

        assert_no_leak(message)
        assert CONSTRAINT_FAILURE in message

    async def test_driver_error_for_huge_id_is_generic(self, mcp_client):
        message = await tool_error(mcp_client, "get_memory", {"memory_id": 10**30})

        assert_no_leak(message)
        assert GENERIC_FAILURE in message

    async def test_invalid_skill_yaml_is_short(self, mcp_client):
        message = await tool_error(
            mcp_client,
            "import_skill",
            {"skill_md_content": "---\nname: [unclosed\n---\nbody", "importance": 8},
        )

        assert "invalid YAML" in message
        assert "while parsing" not in message

    async def test_domain_not_found_message_is_kept(self, mcp_client):
        message = await tool_error(mcp_client, "get_memory", {"memory_id": 987654})

        assert "987654" in message
        assert "not found" in message.lower()

    async def test_argument_error_message_is_kept(self, mcp_client):
        message = await tool_error(mcp_client, "get_memory", {"memory_id": "abc"})

        assert "memory_id" in message


class TestDiscoverCategories:
    """Every category the tool docstrings advertise holds tools."""

    async def test_linking_category_lists_link_tools(self, mcp_client):
        result = await mcp_client.call_tool("discover_forgetful_tools", {"category": "linking"})
        data = result.data

        names = {tool["name"] for tools in data["tools_by_category"].values() for tool in tools}
        assert data["total_count"] > 0
        assert {"link_memories", "unlink_memories"} <= names
        assert data["filtered_by"] == "linking"

    async def test_every_advertised_category_is_non_empty(self, mcp_client):
        advertised = [name.strip() for name in _build_category_list().split(",")]
        assert "linking" in advertised, "precondition: the category is documented"

        for category in advertised:
            result = await mcp_client.call_tool(
                "discover_forgetful_tools", {"category": category},
            )
            assert result.data["total_count"] > 0, f"advertised category {category!r} is empty"
