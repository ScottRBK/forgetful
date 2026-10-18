"""Integration tests for the walkthrough orchestration (test_harness/walkthrough.py).

The session runner is dependency-injected: the real one execs the agent inside the
harness container and events land in the mounted skill dir; these tests inject a stub
that writes scripted event records, driving the full per-skill loop — workspace prep,
prompt hand-off, status derivation from the event file, breach scan, report collection,
meta — with no docker and no model calls.
"""
import json
import os
import subprocess
from dataclasses import dataclass, field

import pytest

from test_harness.config import HarnessConfig
from test_harness.report import report_contract_example
from test_harness.walkthrough import (
    SessionOutcome,
    Walkthrough,
    load_events,
    prepare_workspace,
    scan_for_breaches,
)

THROWAWAY_URL = "http://127.0.0.1:59999"

OK_RESULT = {
    "type": "result", "content": "ok", "cost": 0.01, "duration": 2.5,
    "session_id": "s-1", "output_tokens": 42,
}


@dataclass
class StubRunner:
    """Protocol-shaped stand-in for the containerized session runner: writes the
    scripted events where the real runner would (the mounted skill dir)."""

    events: list[dict] = field(default_factory=lambda: [OK_RESULT])
    report: dict | None = None
    outcome: SessionOutcome = field(default_factory=lambda: SessionOutcome(kind="ran"))
    seen: dict = field(default_factory=dict)

    async def run_session(self, *, skill, skill_dir, workspace, prompt, timeout):
        self.seen = {
            "skill": skill, "skill_dir": skill_dir, "workspace": workspace,
            "prompt": prompt, "timeout": timeout,
        }
        with (skill_dir / "events.jsonl").open("w") as event_log:
            for event in self.events:
                event_log.write(json.dumps(event) + "\n")
        if self.report is not None:
            (workspace / "report.json").write_text(json.dumps(self.report))
        return self.outcome


def make_walkthrough(tmp_path, runner, **config_kwargs):
    config = HarnessConfig(skills=["forgetful-recall"], **config_kwargs)
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    return Walkthrough(config=config, runner=runner, server_url=THROWAWAY_URL, run_dir=run_dir)


def valid_report(skill="forgetful-recall"):
    return {"skill": skill, "verdict": "pass", "steps": [], "issues": []}


async def test_run_skill_writes_artifacts_and_collects_report(tmp_path):
    # Arrange
    events = [
        {"type": "system", "content": "", "session_id": "s-1"},
        {"type": "text", "content": "Working through the skill"},
        {"type": "tool_use", "content": "bash"},
        OK_RESULT,
    ]
    runner = StubRunner(events=events, report=valid_report())
    walkthrough = make_walkthrough(tmp_path, runner)

    # Act
    result = await walkthrough.run_skill("forgetful-recall")

    # Assert: session driven with the skill's prompt and timeout
    assert runner.seen["skill"] == "forgetful-recall"
    assert runner.seen["timeout"] == 900
    assert report_contract_example() in runner.seen["prompt"]

    # Assert: outcome derived from the event file the runner wrote
    assert result.status == "completed"
    assert result.report_load.status == "ok"
    assert result.cost == pytest.approx(0.01)
    assert result.output_tokens == 42
    assert result.session_id == "s-1"

    skill_dir = walkthrough.run_dir / "skills" / "forgetful-recall"
    assert runner.seen["skill_dir"] == skill_dir
    assert (skill_dir / "prompt.txt").read_text() == runner.seen["prompt"]
    meta = json.loads((skill_dir / "meta.json").read_text())
    assert meta["skill"] == "forgetful-recall"
    assert meta["status"] == "completed"
    assert meta["report_status"] == "ok"
    assert meta["model"] == "opencode-go/deepseek-v4-flash"


async def test_missing_report_is_finding_not_crash(tmp_path):
    # Arrange: agent completes but never writes report.json
    runner = StubRunner(events=[OK_RESULT], report=None)
    walkthrough = make_walkthrough(tmp_path, runner)

    # Act
    result = await walkthrough.run_skill("forgetful-recall")

    # Assert
    assert result.status == "completed"
    assert result.report_load.status == "missing"


async def test_timeout_outcome_marks_run_timeout(tmp_path):
    # Arrange: the in-container `timeout` wrapper killed the session (exit 124/137);
    # whatever events were flushed before the kill are still on disk
    runner = StubRunner(
        events=[{"type": "text", "content": "partial work"}],
        outcome=SessionOutcome(kind="timeout", detail="exceeded 900s"),
    )
    walkthrough = make_walkthrough(tmp_path, runner)

    # Act
    result = await walkthrough.run_skill("forgetful-recall")

    # Assert
    assert result.status == "timeout"
    meta = json.loads(
        (walkthrough.run_dir / "skills" / "forgetful-recall" / "meta.json").read_text(),
    )
    assert meta["status"] == "timeout"


async def test_stream_without_result_event_is_error(tmp_path):
    # Arrange: opencode can truncate a turn with no result and no error (mem 1690) -
    # completion requires an explicit result event with content "ok"
    runner = StubRunner(events=[{"type": "text", "content": "partial"}])
    walkthrough = make_walkthrough(tmp_path, runner)

    # Act
    result = await walkthrough.run_skill("forgetful-recall")

    # Assert
    assert result.status == "error"
    assert "result" in result.error


async def test_error_event_is_captured(tmp_path):
    # Arrange
    runner = StubRunner(events=[{"type": "error", "content": "CLI exploded: stderr tail"}])
    walkthrough = make_walkthrough(tmp_path, runner)

    # Act
    result = await walkthrough.run_skill("forgetful-recall")

    # Assert
    assert result.status == "error"
    assert "CLI exploded" in result.error


async def test_breach_scan_flags_real_mcp_tools_in_meta(tmp_path):
    # Arrange: an MCP tool name referencing forgetful means the agent reached a
    # configured forgetful server directly instead of the fenced CLI route
    events = [
        {"type": "tool_use", "content": "forgetful_execute_forgetful_tool"},
        OK_RESULT,
    ]
    runner = StubRunner(events=events, report=valid_report())
    walkthrough = make_walkthrough(tmp_path, runner)

    # Act
    result = await walkthrough.run_skill("forgetful-recall")

    # Assert
    assert result.breaches == ["forgetful_execute_forgetful_tool"]
    meta = json.loads(
        (walkthrough.run_dir / "skills" / "forgetful-recall" / "meta.json").read_text(),
    )
    assert meta["breaches"] == ["forgetful_execute_forgetful_tool"]


def test_breach_scan_ignores_cli_commands_and_local_tools():
    # Arrange: codex-style tool_use carries the command string; the fenced CLI route
    # and plain local tools are expected, not breaches
    events = [
        {"type": "tool_use", "content": "bash"},
        {"type": "tool_use", "content": "forgetful call query_memory --json"},
        {"type": "text", "content": "mentioning forgetful in prose"},
        {"type": "tool_use", "content": "mcp__forgetful__execute_forgetful_tool"},
    ]

    # Act
    breaches = scan_for_breaches(events)

    # Assert
    assert breaches == ["mcp__forgetful__execute_forgetful_tool"]


def test_torn_final_event_line_is_tolerated(tmp_path):
    # Arrange: the timeout kill can land mid-write, leaving a torn trailing line -
    # everything flushed before it must still count
    path = tmp_path / "events.jsonl"
    path.write_text(
        json.dumps({"type": "text", "content": "whole"}) + "\n" + '{"type": "res',
    )

    # Act
    events = load_events(path)

    # Assert
    assert events == [{"type": "text", "content": "whole"}]


def test_missing_event_file_loads_empty(tmp_path):
    # Arrange: a session that died before the runner opened the event log
    path = tmp_path / "events.jsonl"

    # Act / Assert
    assert load_events(path) == []


def test_workspace_prepared_with_skill_md(tmp_path):
    # Arrange
    config = HarnessConfig()

    # Act
    workspace = prepare_workspace(tmp_path / "forgetful-recall", "forgetful-recall",
                                  config.skills_dir)

    # Assert: the canonical SKILL.md is copied in as the document under review
    copied = (workspace / "SKILL.md").read_text()
    assert "name: forgetful-recall" in copied


def test_encode_repo_workspace_gets_fixture_repo(tmp_path):
    # Arrange
    config = HarnessConfig()

    # Act
    workspace = prepare_workspace(tmp_path / "forgetful-encode-repo", "forgetful-encode-repo",
                                  config.skills_dir)

    # Assert: a tiny committed git repo with a fake origin for project resolution.
    # Inspect it without inherited GIT_* (a pre-commit hook in a linked worktree exports
    # GIT_DIR, which would point these commands at the caller's repo instead)
    fixture = workspace / "fixture-repo"
    assert (fixture / ".git").is_dir()
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    remote = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=fixture, env=env, capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert remote.endswith("uat-fixture-calc.git")
    log = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=fixture, env=env, capture_output=True, text=True, check=True,
    ).stdout
    assert log.strip()


async def test_run_walks_skills_in_order_and_writes_summary(tmp_path):
    # Arrange
    runner = StubRunner(events=[OK_RESULT], report=valid_report())
    config = HarnessConfig(skills=["forgetful-recall", "forgetful-remember"])
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    walkthrough = Walkthrough(
        config=config, runner=runner, server_url=THROWAWAY_URL, run_dir=run_dir,
    )

    # Act
    results = await walkthrough.run()

    # Assert: canonical order (remember before recall), summary on disk
    assert [r.skill for r in results] == ["forgetful-remember", "forgetful-recall"]
    summary = json.loads((run_dir / "run.json").read_text())
    assert [entry["skill"] for entry in summary["skills"]] == [
        "forgetful-remember", "forgetful-recall",
    ]
    assert all(entry["status"] == "completed" for entry in summary["skills"])


def test_prompt_embeds_contract_and_ground_rules():
    # Arrange
    from test_harness.prompts import build_prompt

    # Act
    prompt = build_prompt("forgetful-recall")

    # Assert
    assert "./SKILL.md" in prompt
    assert report_contract_example() in prompt
    assert "subagent" in prompt.lower()
    assert "--json" in prompt
    assert "--local" in prompt  # forbids sidestepping the connected server


def test_encode_repo_prompt_points_at_fixture_repo():
    # Arrange
    from test_harness.prompts import build_prompt

    # Act
    prompt = build_prompt("forgetful-encode-repo")

    # Assert
    assert "./fixture-repo" in prompt


def test_prompts_never_reveal_evaluation():
    # Arrange: the agent must believe this is a real doc-review task (mem 1667) - no
    # scoring or harness language on any skill's prompt
    from test_harness.config import SKILL_ORDER
    from test_harness.prompts import build_prompt

    forbidden = ["evaluat", "graded", "grading", "scoring", "score", "harness", "benchmark"]

    for skill in SKILL_ORDER:
        # Act
        prompt = build_prompt(skill).lower()

        # Assert
        for word in forbidden:
            assert word not in prompt, f"{skill} prompt leaks {word!r}"
