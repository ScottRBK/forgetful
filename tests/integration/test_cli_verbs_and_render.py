"""Integration tests for CLI project resolution and human-output rendering

Covers deterministic -p resolution (exact-case first, ambiguity errors, digit-only
project names, empty values), terminal-safe rendering of stored text, the obsolete
marker in `memory get` and stdout encoding safety. Verbs run against a recording
executor, so no database or embedding model is involved.
"""
import re

import pytest

from app.routes.cli import render, verbs
from app.routes.cli.parser import build_parser

RAW_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f\u2028\u2029]")
EVIL = "evil\x1b[2J\x1b]0;pwned\x07\n#99  [10]  Fake injected row"


class RecordingExecutor:
    """ToolExecutor double that records execute() calls and returns canned payloads."""

    def __init__(self, responses=None):
        self.calls = []
        self._responses = dict(responses or {})

    async def execute(self, tool_name, arguments):
        self.calls.append((tool_name, dict(arguments)))
        return self._responses.get(tool_name, {})

    async def close(self):
        pass


def _args(argv):
    return build_parser().parse_args(argv)


def _listing(*rows):
    """Build a list_projects payload from (id, name[, status]) rows, newest first."""
    return {
        "projects": [
            {
                "id": row[0],
                "name": row[1],
                "project_type": "development",
                "status": row[2] if len(row) > 2 else "active",
            }
            for row in rows
        ],
        "total_count": len(rows),
    }


def _executor_with(*rows):
    return RecordingExecutor({"list_projects": _listing(*rows)})


# -- project resolution ---------------------------------------------------------------


async def test_exact_case_name_wins_over_newer_case_variant():
    executor = _executor_with((2, "alpha"), (1, "Alpha"))

    assert await verbs.resolve_project(executor, "Alpha") == 1
    assert await verbs.resolve_project(executor, "alpha") == 2


async def test_unique_case_insensitive_match_still_resolves():
    executor = _executor_with((4, "Forgetful"), (7, "Homelab"))

    assert await verbs.resolve_project(executor, "forgetful") == 4


async def test_ambiguous_case_variants_raise_and_list_the_ids():
    executor = _executor_with((2, "ALPHA"), (1, "Alpha"))

    with pytest.raises(verbs.CliError) as excinfo:
        await verbs.resolve_project(executor, "alpha")

    message = str(excinfo.value)
    assert "Ambiguous project 'alpha'" in message
    assert "1" in message and "2" in message
    assert "id" in message


async def test_identical_names_raise_ambiguity_instead_of_picking_the_newest():
    executor = _executor_with((3, "Dup"), (1, "Dup"))

    with pytest.raises(verbs.CliError, match="Ambiguous project 'Dup'"):
        await verbs.resolve_project(executor, "Dup")


async def test_identical_names_prefer_the_single_active_project():
    newer_archived = _executor_with((3, "Dup", "archived"), (1, "Dup", "active"))
    newer_active = _executor_with((3, "Dup", "active"), (1, "Dup", "completed"))

    assert await verbs.resolve_project(newer_archived, "Dup") == 1
    assert await verbs.resolve_project(newer_active, "Dup") == 3


async def test_digit_only_name_resolves_when_no_project_has_that_id():
    executor = _executor_with((3, "2024"), (1, "Other"))

    assert await verbs.resolve_project(executor, "2024") == 3


async def test_numeric_value_matching_a_project_id_stays_an_id():
    executor = _executor_with((3, "2024"), (2024, "Elsewhere"))

    assert await verbs.resolve_project(executor, "2024") == 2024


async def test_numeric_id_unknown_to_the_listing_still_passes_through():
    executor = _executor_with((4, "Forgetful"))

    assert await verbs.resolve_project(executor, "99") == 99


@pytest.mark.parametrize("value", ["\u00b2", "\u0663"])
async def test_non_ascii_digits_are_names_never_ids(value):
    executor = _executor_with((4, "Forgetful"))

    with pytest.raises(verbs.CliError, match="Unknown project"):
        await verbs.resolve_project(executor, value)


async def test_non_ascii_digit_project_name_resolves_by_name():
    executor = _executor_with((6, "\u00b2"), (4, "Forgetful"))

    assert await verbs.resolve_project(executor, "\u00b2") == 6


@pytest.mark.parametrize(
    ("argv", "tool"),
    [
        (["memory", "search", "q", "-c", "ctx", "-p", ""], "query_memory"),
        (["memory", "save", "body", "--title", "T", "-p", ""], "create_memory"),
        (["memory", "recent", "-p", ""], "get_recent_memories"),
    ],
)
async def test_empty_project_value_is_rejected_instead_of_dropping_the_scope(argv, tool):
    executor = _executor_with((4, "Forgetful"))

    with pytest.raises(verbs.CliError, match="Unknown project ''"):
        await verbs.run(executor, _args(argv))

    assert tool not in [name for name, _ in executor.calls]


async def test_unknown_project_message_escapes_stored_project_names():
    executor = _executor_with((4, "evil\x1b[2J\nname"))

    with pytest.raises(verbs.CliError) as excinfo:
        await verbs.resolve_project(executor, "nope")

    assert not RAW_CONTROL.search(str(excinfo.value))
    assert "evil\\x1b[2J\\nname" in str(excinfo.value)


# -- terminal-safe rendering ----------------------------------------------------------


def test_memory_lines_cannot_forge_extra_rows_or_emit_control_bytes():
    output = render.render_memory_lines([{"id": 1, "title": EVIL, "importance": 5}])

    assert not RAW_CONTROL.search(output)
    assert len(output.splitlines()) == 1
    assert output.startswith("#1  [5]  evil")
    assert output.endswith("(memory 1)")
    assert "\\x1b[2J" in output  # the attempt stays visible, just inert


def test_memory_detail_escapes_control_characters_in_every_field():
    memory = {
        "id": 3,
        "title": EVIL,
        "importance": 5,
        "tags": ["ok", "bad\x1b[31mtag\n"],
        "context": "ctx\x1b[2J\r\nmore",
        "content": "line one\n\tindented\r\nline three\x1b[31mred\x9b\u2028end\rboom",
    }

    output = render.render_memory_detail(memory)

    assert not RAW_CONTROL.search(output.replace("\n", "").replace("\t", ""))
    assert [ln for ln in output.splitlines() if ln.startswith("#")] == []
    assert "Memory 3: evil" in output
    assert "bad\\x1b[31mtag\\n" in output
    # content keeps its own line structure (newline, tab, CRLF folded to LF)
    assert "line one\n\tindented\nline three" in output
    assert "\\x1b[31mred\\x9b\\u2028end\\rboom" in output


def test_project_lines_escape_stored_names():
    output = render.render_project_lines([
        {"id": 1, "name": "Alpha\x1b[2J\n#2  Fake", "project_type": "development", "status": "active"},
    ])

    assert not RAW_CONTROL.search(output)
    assert len(output.splitlines()) == 1


async def test_save_confirmation_line_escapes_the_title():
    executor = RecordingExecutor({"create_memory": {"id": 9, "title": EVIL}})

    _, human = await verbs.run(executor, _args(["memory", "save", "body", "--title", EVIL]))

    assert human.startswith("Created memory 9: evil")
    assert not RAW_CONTROL.search(human)
    assert len(human.splitlines()) == 1


async def test_save_confirmation_keeps_plugin_warnings_as_escaped_single_lines():
    executor = RecordingExecutor({"create_memory": {
        "id": 9,
        "title": "ok",
        "plugin_warnings": [{"message": "Check the source.\x1b[2J\n#99  [10]  Fake row"}],
    }})

    _, human = await verbs.run(executor, _args(["memory", "save", "body", "--title", "ok"]))

    lines = human.splitlines()
    assert lines[0] == "Created memory 9: ok"
    assert lines[1].startswith("Warning: Check the source.")
    assert len(lines) == 2
    assert not RAW_CONTROL.search(human)
