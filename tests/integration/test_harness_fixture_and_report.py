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
import stat
import subprocess
import sys
from dataclasses import dataclass, field

import pytest

from test_harness.__main__ import main
from test_harness.config import HarnessConfig
from test_harness.report import load_report
from test_harness.server import HarnessInfraError
from test_harness.walkthrough import (
    SessionOutcome,
    Walkthrough,
    load_events,
    prepare_workspace,
    scan_for_breaches,
)

THROWAWAY_URL = "http://127.0.0.1:59999"
SKILL = "forgetful-recall"
FIXTURE_SKILL = "forgetful-encode-repo"

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


# --------------------------------------------------------------------------------------
# Hermetic fixture repo: the developer's git setup must not change how it is built
# --------------------------------------------------------------------------------------

posix_only = pytest.mark.skipif(sys.platform == "win32", reason="needs a POSIX shell")


def clean_git_env():
    """Environment for inspecting repos from the tests, free of any inherited GIT_*."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    return env


def git(*args, cwd):
    return subprocess.run(
        ["git", *args], cwd=cwd, env=clean_git_env(), check=True,
        capture_output=True, text=True, encoding="utf-8",
    ).stdout.strip()


def build_fixture(tmp_path):
    workspace = prepare_workspace(
        tmp_path / "skills" / FIXTURE_SKILL, FIXTURE_SKILL, HarnessConfig().skills_dir,
    )
    return workspace / "fixture-repo"


def assert_committed_fixture(fixture):
    assert (fixture / ".git").is_dir()
    assert git("log", "--format=%s", cwd=fixture) == "Initial fixture"
    assert git("ls-files", cwd=fixture).splitlines() == [
        "README.md", "pyproject.toml", "src/calc.py",
    ]
    assert git("remote", "get-url", "origin", cwd=fixture).endswith("uat-fixture-calc.git")


def use_global_git_config(monkeypatch, tmp_path, text):
    """Make `text` the developer's global git config for everything the test spawns."""
    config = tmp_path / "global-gitconfig"
    config.write_text(text)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))


def test_fixture_commit_ignores_a_signer_that_cannot_sign(tmp_path, monkeypatch):
    # Arrange: commit.gpgsign=true with a signer that always fails (locked key, no agent)
    use_global_git_config(
        monkeypatch, tmp_path,
        "[commit]\n\tgpgsign = true\n[gpg]\n\tformat = ssh\n"
        '[gpg "ssh"]\n\tprogram = /nonexistent/signer\n'
        "[user]\n\tsigningkey = /nonexistent/key.pub\n",
    )

    # Act
    fixture = build_fixture(tmp_path)

    # Assert
    assert_committed_fixture(fixture)


@posix_only
def test_fixture_commit_ignores_global_hooks_and_excludes(tmp_path, monkeypatch):
    # Arrange: a global rejecting pre-commit hook, and a global ignore-everything file
    hooks = tmp_path / "global-hooks"
    hooks.mkdir()
    hook = hooks / "pre-commit"
    hook.write_text("#!/bin/sh\necho 'policy: rejected' >&2\nexit 1\n")
    hook.chmod(hook.stat().st_mode | stat.S_IEXEC)
    ignore_all = tmp_path / "ignore-all"
    ignore_all.write_text("*\n")
    use_global_git_config(
        monkeypatch, tmp_path,
        f"[core]\n\thooksPath = {hooks}\n\texcludesFile = {ignore_all}\n",
    )

    # Act
    fixture = build_fixture(tmp_path)

    # Assert
    assert_committed_fixture(fixture)


def test_fixture_repo_survives_the_env_git_gives_a_linked_worktree_hook(
    tmp_path, monkeypatch,
):
    # Arrange: a real repo with a linked worktree; inside a hook git exports an
    # absolute GIT_DIR and GIT_INDEX_FILE (plus GIT_AUTHOR_*) that win over cwd
    main_repo = tmp_path / "main"
    main_repo.mkdir()
    git("init", "-q", cwd=main_repo)
    git("config", "user.email", "dev@example.com", cwd=main_repo)
    git("config", "user.name", "Developer", cwd=main_repo)
    (main_repo / "app.py").write_text("print('real code')\n")
    git("add", "-A", cwd=main_repo)
    git("commit", "-q", "-m", "real commit", cwd=main_repo)
    worktree = tmp_path / "wt"
    git("worktree", "add", "-q", str(worktree), "-b", "feature", cwd=main_repo)
    head_before = git("rev-parse", "HEAD", cwd=worktree)
    config_before = (main_repo / ".git" / "config").read_text()
    gitdir = git("rev-parse", "--absolute-git-dir", cwd=worktree)
    monkeypatch.setenv("GIT_DIR", gitdir)
    monkeypatch.setenv("GIT_INDEX_FILE", os.path.join(gitdir, "index"))
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Someone Else")

    # Act
    fixture = build_fixture(tmp_path)

    # Assert: the fixture is self-contained and the caller's repository is untouched
    assert_committed_fixture(fixture)
    assert git("log", "--format=%an", cwd=fixture) == "UAT Fixture"
    assert git("rev-parse", "HEAD", cwd=worktree) == head_before
    assert git("ls-files", cwd=worktree) == "app.py"
    assert (main_repo / ".git" / "config").read_text() == config_before


@posix_only
def test_git_failure_is_an_infra_error_carrying_gits_stderr(tmp_path, monkeypatch):
    # Arrange: a git that always fails
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "git"
    fake.write_text("#!/bin/sh\necho 'fatal: boom from fake git' >&2\nexit 3\n")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", str(bin_dir))

    # Act / Assert: harness defect (exit 2), with git's own message, not a bare traceback
    with pytest.raises(HarnessInfraError, match="boom from fake git"):
        build_fixture(tmp_path)


def test_missing_git_is_an_infra_error(tmp_path, monkeypatch):
    # Arrange
    monkeypatch.setenv("PATH", str(tmp_path / "no-such-dir"))

    # Act / Assert
    with pytest.raises(HarnessInfraError, match="cannot run git"):
        build_fixture(tmp_path)


def test_broken_git_fails_the_run_up_front_with_exit_code_2(tmp_path, monkeypatch, capsys):
    # Arrange: no git, and docker must never be reached
    monkeypatch.setenv("PATH", str(tmp_path / "no-such-dir"))

    def docker_must_not_be_touched(*args, **kwargs):
        raise AssertionError("preflight should have failed before the image check")

    monkeypatch.setattr("test_harness.__main__.ensure_image", docker_must_not_be_touched)
    output = tmp_path / "runs"
    output.mkdir()

    # Act
    exit_code = main(["--output", str(output), "--skills", FIXTURE_SKILL])

    # Assert: infra failure, and no half-created run directory
    assert exit_code == 2
    assert "cannot run git" in capsys.readouterr().err
    assert list(output.iterdir()) == []
