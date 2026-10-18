"""E2E (SQLite) hardening of the three MCP meta-tools.

- database failures reach the client as short messages, never SQL, bound parameters or ids
- caller-controlled names cannot forge or inject into the console log
- every category advertised by discover_forgetful_tools lists tools
"""

import io
import logging
import re
import sys

import pytest
from fastmcp.exceptions import ToolError
from rich.logging import RichHandler

from app.config import logging_config
from app.routes.mcp import meta_tools
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


FORGED_RECORD = (
    "2026-10-18 12:00:00 - app.middleware.auth - INFO - "
    "Authentication enabled (JWTVerifier) - extracting user from token"
)
FORGED_PREFIX = "2026-10-18 12:00:00 - app.middleware.auth - INFO"
HOSTILE_MARKER = "FORGED-LINE-MARKER"
HOSTILE_NAME = f"x\x1b[2J\x1b[31m\n{HOSTILE_MARKER}\rsecond"


@pytest.fixture
def console_log(monkeypatch):
    """Run the real console logging pipeline and capture what it writes to stderr."""
    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stderr", buffer)
    root = logging.getLogger()
    saved_handlers, saved_level = root.handlers[:], root.level
    # Alembic's fileConfig (run by the app fixture) disables pre-existing loggers.
    for name in ("app.routes.mcp.meta_tools", "app.routes.mcp.tool_registry"):
        logging.getLogger(name).disabled = False
    logging_config.configure_logging(log_level="INFO", log_format="console")
    try:
        yield lambda: _drain(buffer)
    finally:
        logging_config.shutdown_logging()
        root.handlers.clear()
        for handler in saved_handlers:
            root.addHandler(handler)
        root.setLevel(saved_level)


@pytest.fixture
def every_logger_log(console_log):
    """``console_log`` with every logger enabled and FastMCP's own console output captured.

    FastMCP logs each failed tool call (message and traceback) through ``fastmcp.server.server``
    to its own Rich handlers, not the application's. Alembic's fileConfig (run by the app
    fixture) disables every logger that exists at that point, so the capture is only complete
    when all of them are switched back on. The Rich consoles look up ``sys.stderr`` at write
    time and pytest swaps it back at the start of each phase, so they are pointed at a buffer
    explicitly (wide, so that a long name is not folded across lines).
    """
    rich_buffer = io.StringIO()
    loggers = [
        logger for logger in logging.root.manager.loggerDict.values()
        if isinstance(logger, logging.Logger)
    ]
    saved_disabled = [(logger, logger.disabled) for logger in loggers]
    consoles = [
        handler.console
        for logger in loggers
        for handler in logger.handlers
        if isinstance(handler, RichHandler)
    ]
    saved_consoles = [(console, console._file, console._width) for console in consoles]
    for logger in loggers:
        logger.disabled = False
    for console in consoles:
        console.file = rich_buffer
        console.width = 400
    try:
        yield lambda: console_log() + rich_buffer.getvalue()
    finally:
        for console, file, width in saved_consoles:
            console.file = file
            console.width = width
        for logger, disabled in saved_disabled:
            logger.disabled = disabled


def _drain(buffer: io.StringIO) -> str:
    logging_config.shutdown_logging()
    return buffer.getvalue()


def forged_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.startswith(FORGED_PREFIX)]


def assert_no_raw_control_characters(output: str, client_message: str) -> None:
    """Neither the captured server output nor the client-facing error text may carry the
    hostile name's ESC, CR or LF, or start a line with its marker."""
    assert "\x1b[2J" not in output
    assert "\r" not in output
    assert not any(line.strip().startswith(HOSTILE_MARKER) for line in output.splitlines())
    assert "\x1b" not in client_message
    assert "\r" not in client_message
    assert "\n" not in client_message


async def ignore_tool_error(client, name: str, arguments: dict) -> None:
    try:
        await client.call_tool(name, arguments)
    except ToolError:
        pass


class TestLogInjection:
    """Caller-controlled names are logged escaped, one record per call."""

    @pytest.mark.parametrize(
        ("meta_tool", "arguments", "marker"),
        [
            ("how_to_use_forgetful_tool", {"tool_name": "x\n" + FORGED_RECORD}, "how_to_use"),
            (
                "execute_forgetful_tool",
                {"tool_name": "x\n" + FORGED_RECORD, "arguments": {}},
                "execute_forgetful_tool",
            ),
            ("discover_forgetful_tools", {"category": "x\n" + FORGED_RECORD}, "discover"),
        ],
        ids=["how_to_use", "execute", "discover"],
    )
    async def test_newline_cannot_forge_a_record(
        self, mcp_client, console_log, meta_tool, arguments, marker,
    ):
        await ignore_tool_error(mcp_client, meta_tool, arguments)

        output = console_log()

        assert marker in output, "precondition: the call was logged"
        assert forged_lines(output) == []

    async def test_escape_sequences_do_not_reach_the_log(self, mcp_client, console_log):
        await ignore_tool_error(
            mcp_client, "how_to_use_forgetful_tool", {"tool_name": "x\x1b[2J\x1b[31mPWNED"},
        )

        output = console_log()

        assert "how_to_use_forgetful_tool" in output, "precondition: the call was logged"
        assert "\x1b[2J" not in output

    @pytest.mark.parametrize(
        "poisoned_key",
        ["x\n" + FORGED_RECORD, "x\r" + FORGED_RECORD, "x\x1b[2J\x1b[31mPWNED", "x y", "", "1x"],
        ids=["newline", "carriage_return", "escape", "space", "empty", "leading_digit"],
    )
    async def test_argument_names_cannot_forge_a_record(
        self, mcp_client, console_log, poisoned_key,
    ):
        """CPython copies an unknown keyword into the TypeError text unescaped (message and
        traceback), so the name is rejected before dispatch and never logged or echoed raw."""
        with pytest.raises(ToolError) as caught:
            await execute(mcp_client, "list_projects", {poisoned_key: 1})

        output = console_log()

        assert "execute_forgetful_tool" in output, "precondition: the rejected call was logged"
        assert forged_lines(output) == []
        assert "\x1b[2J" not in output
        assert "\r" not in output
        assert "PWNED" not in output
        assert "PWNED" not in str(caught.value)
        assert FORGED_PREFIX not in str(caught.value)
        assert "argument name" in str(caught.value).lower()

    async def test_unknown_but_well_formed_argument_name_is_still_a_normal_error(
        self, mcp_client, console_log,
    ):
        message = await tool_error(mcp_client, "list_projects", {"no_such_argument": 1})

        output = console_log()

        assert "no_such_argument" in message
        assert "Tool 'list_projects' execution failed" in output, (
            "precondition: the registry failure is logged, so the poisoned-key tests cover it"
        )
        assert forged_lines(output) == []

    @pytest.mark.parametrize(
        ("meta_tool", "arguments", "error_text"),
        [
            ("how_to_use_forgetful_tool", {"tool_name": HOSTILE_NAME}, "not found in registry"),
            (
                "execute_forgetful_tool",
                {"tool_name": HOSTILE_NAME, "arguments": {}},
                "not found in registry",
            ),
            ("discover_forgetful_tools", {"category": HOSTILE_NAME}, "Invalid category"),
        ],
        ids=["how_to_use", "execute", "discover"],
    )
    async def test_server_error_log_and_client_error_carry_no_raw_control_characters(
        self, mcp_client, every_logger_log, meta_tool, arguments, error_text,
    ):
        """FastMCP logs every failed tool call with its traceback, and the traceback ends in the
        ToolError text, so the caller-supplied name must be escaped inside that text as well."""
        with pytest.raises(ToolError) as caught:
            await mcp_client.call_tool(meta_tool, arguments)

        output = every_logger_log()

        assert "Error calling tool" in output, "precondition: FastMCP logged the failed call"
        assert error_text in output, "precondition: the traceback shows the ToolError text"
        assert error_text in str(caught.value)
        assert_no_raw_control_characters(output, str(caught.value))

    @pytest.mark.parametrize(
        ("meta_tool", "arguments", "error_text"),
        [
            (
                "how_to_use_forgetful_tool",
                {"tool_name": HOSTILE_NAME},
                "Failed to get documentation for",
            ),
            (
                "execute_forgetful_tool",
                {"tool_name": HOSTILE_NAME, "arguments": {}},
                "Failed to execute",
            ),
        ],
        ids=["how_to_use", "execute"],
    )
    async def test_unexpected_failure_message_escapes_the_name_too(
        self, mcp_client, every_logger_log, monkeypatch, meta_tool, arguments, error_text,
    ):
        """The catch-all wrapper of a meta-tool also quotes the tool name it was called with."""

        def broken_scope_lookup(_ctx):
            raise RuntimeError("scope lookup failed")

        monkeypatch.setattr(meta_tools, "get_effective_scopes", broken_scope_lookup)

        with pytest.raises(ToolError) as caught:
            await mcp_client.call_tool(meta_tool, arguments)

        output = every_logger_log()

        assert "Error calling tool" in output, "precondition: FastMCP logged the failed call"
        assert error_text in output, "precondition: the traceback shows the ToolError text"
        assert error_text in str(caught.value)
        assert_no_raw_control_characters(output, str(caught.value))

    async def test_regular_calls_still_log_the_tool_name(self, mcp_client, console_log):
        await execute(mcp_client, "list_projects", {})

        output = console_log()

        assert "execute_forgetful_tool: 'list_projects'" in output
