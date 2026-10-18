"""Integration tests for the harness's host-side file handling and fixture repo.

Everything the agent writes (report.json, events.jsonl, anything under the rw-mounted
skills tree) is untrusted input to the host orchestrator: malformed content must become
a recorded finding, never a harness crash, and no host-side read or write may follow a
symlink the agent planted. The throwaway fixture repo the encode-repo skill works on
must build the same on every developer machine, whatever git config or hook environment
surrounds the harness. No docker and no model calls: the session runner is a stub that
plays the agent by writing (or sabotaging) the files the real one would.
"""
import json
import os
import sys
from dataclasses import dataclass, field

import pytest

from test_harness.config import HarnessConfig
from test_harness.report import load_report
from test_harness.walkthrough import (
    SessionOutcome,
    Walkthrough,
    load_events,
    scan_for_breaches,
)

THROWAWAY_URL = "http://127.0.0.1:59999"
SKILL = "forgetful-recall"

OK_RESULT = {
    "type": "result", "content": "ok", "cost": 0.01, "duration": 2.5,
    "session_id": "s-1", "output_tokens": 42,
}

can_chmod_away_read = pytest.mark.skipif(
    sys.platform == "win32" or (hasattr(os, "geteuid") and os.geteuid() == 0),
    reason="needs POSIX file modes that the current user is subject to",
)


@dataclass
class ScriptedAgent:
    """Stub session runner playing the agent: writes the given raw file contents where
    the real container would (events in the skill dir, the report in the workspace)."""

    events_text: str = json.dumps(OK_RESULT) + "\n"
    report_text: str | None = None
    outcome: SessionOutcome = field(default_factory=lambda: SessionOutcome(kind="ran"))

    async def run_session(self, *, skill, skill_dir, workspace, prompt, timeout):
        (skill_dir / "events.jsonl").write_text(self.events_text)
        if self.report_text is not None:
            (workspace / "report.json").write_text(self.report_text)
        return self.outcome


def make_walkthrough(tmp_path, runner, skills=(SKILL,)):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    return Walkthrough(
        config=HarnessConfig(skills=list(skills)),
        runner=runner,
        server_url=THROWAWAY_URL,
        run_dir=run_dir,
    )


# --------------------------------------------------------------------------------------
# Tolerant parsing: malformed agent-written files are findings, not crashes
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("severity", [["major"], {"level": "major"}], ids=["list", "dict"])
def test_unhashable_severity_is_a_schema_error(tmp_path, severity):
    # Arrange: a severity the alias lookup cannot even hash
    path = tmp_path / "report.json"
    path.write_text(json.dumps({
        "skill": "s", "verdict": "issues", "issues": [{"severity": severity, "what": "w"}],
    }))

    # Act
    outcome = load_report(path)

    # Assert
    assert outcome.status == "schema_error"
    assert outcome.report is None


def test_severity_aliases_still_normalise(tmp_path):
    # Arrange
    path = tmp_path / "report.json"
    path.write_text(json.dumps({
        "skill": "s", "verdict": "issue",
        "issues": [{"severity": "Critical", "what": "w"}, {"severity": "TRIVIAL", "what": "x"}],
    }))

    # Act
    outcome = load_report(path)

    # Assert
    assert outcome.status == "ok"
    assert [issue.severity for issue in outcome.report.issues] == ["blocker", "nit"]


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param("[" * 100_000, id="deeply-nested"),
        pytest.param("9" * 5_000, id="huge-integer"),
        pytest.param('{"skill": "x", "verdict": ' + "9" * 5_000 + "}", id="huge-integer-in-object"),
        pytest.param('{"skill": "x", "verdict": "pass", "steps": [', id="truncated"),
    ],
)
def test_pathological_report_is_an_invalid_json_finding(tmp_path, payload):
    # Arrange
    path = tmp_path / "report.json"
    path.write_text(payload)

    # Act
    outcome = load_report(path)

    # Assert
    assert outcome.status == "invalid_json"
    assert outcome.report is None


@can_chmod_away_read
def test_unreadable_report_is_an_invalid_json_finding(tmp_path):
    # Arrange: e.g. a 0600 report written by the container's other uid
    path = tmp_path / "report.json"
    path.write_text('{"skill": "x", "verdict": "pass"}')
    path.chmod(0o000)

    # Act
    try:
        outcome = load_report(path)
    finally:
        path.chmod(0o600)

    # Assert
    assert outcome.status == "invalid_json"


def test_non_object_event_lines_are_dropped(tmp_path):
    # Arrange: valid JSON that is not an event object must not reach `.get`
    path = tmp_path / "events.jsonl"
    path.write_text('[1]\nnull\n5\n"text"\n{"type": "text", "content": "kept"}\n')

    # Act
    events = load_events(path)

    # Assert
    assert events == [{"type": "text", "content": "kept"}]


def test_pathological_event_line_is_dropped(tmp_path):
    # Arrange
    path = tmp_path / "events.jsonl"
    path.write_text("[" * 100_000 + "\n" + "9" * 5_000 + '\n{"type": "text"}\n')

    # Act
    events = load_events(path)

    # Assert
    assert events == [{"type": "text"}]


@can_chmod_away_read
def test_unreadable_events_file_reads_as_no_events(tmp_path):
    # Arrange
    path = tmp_path / "events.jsonl"
    path.write_text('{"type": "text"}\n')
    path.chmod(0o000)

    # Act
    try:
        events = load_events(path)
    finally:
        path.chmod(0o600)

    # Assert
    assert events == []


def test_non_string_tool_use_content_is_not_a_breach(tmp_path):
    # Arrange
    events = [
        {"type": "tool_use", "content": {"a": 1}},
        {"type": "tool_use", "content": ["forgetful"]},
        {"type": "tool_use", "content": None},
        {"type": "tool_use", "content": "mcp__forgetful__search"},
    ]

    # Act
    breaches = scan_for_breaches(events)

    # Assert: only the real MCP-style tool name is flagged
    assert breaches == ["mcp__forgetful__search"]


async def test_pathological_agent_files_do_not_abort_the_run(tmp_path):
    # Arrange: every file the agent controls is hostile at once
    events = "[1]\n" + "[" * 100_000 + "\n" + json.dumps(OK_RESULT) + "\n"
    agent = ScriptedAgent(events_text=events, report_text="[" * 100_000)
    walkthrough = make_walkthrough(tmp_path, agent)

    # Act
    results = await walkthrough.run()

    # Assert: recorded as findings, and the summary of the run is still written
    assert results[0].status == "completed"
    assert results[0].report_load.status == "invalid_json"
    summary = json.loads((walkthrough.run_dir / "run.json").read_text())
    assert summary["skills"][0]["report_status"] == "invalid_json"


async def test_non_string_error_event_content_is_recorded(tmp_path):
    # Arrange
    events = json.dumps({"type": "error", "content": {"code": 7}}) + "\n"
    walkthrough = make_walkthrough(tmp_path, ScriptedAgent(events_text=events))

    # Act
    result = await walkthrough.run_skill(SKILL)

    # Assert
    assert result.status == "error"
    assert "code" in result.error
