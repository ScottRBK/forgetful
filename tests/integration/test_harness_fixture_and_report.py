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
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

import pytest

from test_harness.__main__ import main
from test_harness.config import HarnessConfig
from test_harness.container import AgentContainer
from test_harness.report import load_report
from test_harness.safe_io import (
    UnsafePathError,
    make_dirs,
    read_bytes,
    replace_tree,
    write_bytes,
    write_text,
)
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


# --------------------------------------------------------------------------------------
# The skills tree is mounted rw into the sandbox: the host must never follow its symlinks
# --------------------------------------------------------------------------------------

FIRST = "forgetful-remember"
SECOND = "forgetful-recall"


def plant_symlink(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("cannot create symlinks on this platform/user")


@dataclass
class PlantingAgent:
    """Stub runner playing an agent that sabotages the rw-mounted tree during its session
    for `during` (what `mkdir` / `ln -s` from inside the container can do)."""

    mount: Path
    during: str
    plant: Callable[[Path], None]

    async def run_session(self, *, skill, skill_dir, workspace, prompt, timeout):
        (skill_dir / "events.jsonl").write_text(json.dumps(OK_RESULT) + "\n")
        if skill == self.during:
            self.plant(self.mount)
        return SessionOutcome(kind="ran")


async def run_hostile_walkthrough(tmp_path, plant, skills=(FIRST, SECOND)):
    """Walk `skills`; the agent runs `plant(mount)` at the end of the first session."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    walkthrough = Walkthrough(
        config=HarnessConfig(skills=list(skills)),
        runner=PlantingAgent(run_dir / "skills", skills[0], plant),
        server_url=THROWAWAY_URL,
        run_dir=run_dir,
    )
    results = await walkthrough.run()
    return run_dir, {result.skill: result for result in results}


@pytest.fixture
def outside(tmp_path):
    """Stands in for the host files an escaping agent would aim at (~/.bashrc, ~/.ssh)."""
    directory = tmp_path / "outside-host"
    directory.mkdir()
    return directory


async def test_symlinked_skill_md_does_not_overwrite_a_host_file(tmp_path, outside):
    # Arrange: the agent plants workspace/SKILL.md -> a host file for the next skill
    victim = outside / "bashrc"
    victim.write_text("ORIGINAL HOST FILE\n")

    def plant(mount):
        (mount / SECOND / "workspace").mkdir(parents=True)
        plant_symlink(mount / SECOND / "workspace" / "SKILL.md", victim)

    # Act
    run_dir, _ = await run_hostile_walkthrough(tmp_path, plant)

    # Assert: the host file is intact; the workspace got its own regular copy
    assert victim.read_text() == "ORIGINAL HOST FILE\n"
    planted = run_dir / "skills" / SECOND / "workspace" / "SKILL.md"
    assert not planted.is_symlink()
    assert "name: forgetful-recall" in planted.read_text(encoding="utf-8")


async def test_symlinked_prompt_and_meta_do_not_write_host_files(tmp_path, outside):
    # Arrange: dangling links, so a followed write would *create* the host files
    created_by_prompt = outside / "new_file_from_prompt"
    created_by_meta = outside / "new_file_from_meta"

    def plant(mount):
        (mount / SECOND).mkdir()
        plant_symlink(mount / SECOND / "prompt.txt", created_by_prompt)
        plant_symlink(mount / SECOND / "meta.json", created_by_meta)

    # Act
    run_dir, _ = await run_hostile_walkthrough(tmp_path, plant)

    # Assert
    assert not created_by_prompt.exists()
    assert not created_by_meta.exists()
    second = run_dir / "skills" / SECOND
    assert not (second / "prompt.txt").is_symlink()
    assert not (second / "meta.json").is_symlink()
    assert json.loads((second / "meta.json").read_text(encoding="utf-8"))["skill"] == SECOND


async def test_symlinked_report_is_not_read_from_outside_the_run(tmp_path, outside):
    # Arrange: workspace/report.json -> a host json file holding something secret
    secret = outside / "host_secret.json"
    secret.write_text(json.dumps({"verdict": "TOP-SECRET-HOST-DATA"}))

    def plant(mount):
        (mount / SECOND / "workspace").mkdir(parents=True)
        plant_symlink(mount / SECOND / "workspace" / "report.json", secret)

    # Act
    run_dir, results = await run_hostile_walkthrough(tmp_path, plant)

    # Assert: not parsed, not echoed into the result or meta.json
    report_load = results[SECOND].report_load
    assert report_load.status == "missing"
    assert "symlink" in report_load.detail
    meta = (run_dir / "skills" / SECOND / "meta.json").read_text(encoding="utf-8")
    assert "TOP-SECRET-HOST-DATA" not in meta + report_load.detail


async def test_symlinked_events_log_is_not_read_from_outside_the_run(tmp_path, outside):
    # Arrange: the agent swaps its own events.jsonl for a link to a host jsonl whose
    # error event would otherwise land verbatim in meta.json
    host_log = outside / "host.jsonl"
    host_log.write_text(json.dumps({"type": "error", "content": "TOP-SECRET-HOST-DATA"}) + "\n")

    def plant(mount):
        (mount / FIRST / "events.jsonl").unlink()
        plant_symlink(mount / FIRST / "events.jsonl", host_log)

    # Act
    run_dir, results = await run_hostile_walkthrough(tmp_path, plant)

    # Assert: reads as no events, so the session is an ordinary "no result" error
    assert results[FIRST].status == "error"
    assert "without a result event" in results[FIRST].error
    meta = (run_dir / "skills" / FIRST / "meta.json").read_text(encoding="utf-8")
    assert "TOP-SECRET-HOST-DATA" not in meta


async def test_workspace_swapped_for_a_symlink_during_the_session_is_not_followed(
    tmp_path, outside,
):
    # Arrange: after the host prepared it, the agent replaces its workspace dir with a link
    # to a host directory that happens to hold a report.json
    (outside / "report.json").write_text(
        json.dumps({"skill": "x", "verdict": "pass", "steps": [], "issues": []}),
    )

    def plant(mount):
        workspace = mount / FIRST / "workspace"
        for entry in workspace.iterdir():
            entry.unlink()
        workspace.rmdir()
        plant_symlink(workspace, outside)

    # Act
    _, results = await run_hostile_walkthrough(tmp_path, plant)

    # Assert
    assert results[FIRST].report_load.status == "missing"


@pytest.mark.parametrize("planted", ["workspace", "skill_dir"])
async def test_symlinked_directories_are_replaced_not_written_through(
    tmp_path, outside, planted,
):
    # Arrange: the next skill's workspace (or whole dir) pre-planted as a link to a host dir
    def plant(mount):
        if planted == "workspace":
            (mount / SECOND).mkdir()
            plant_symlink(mount / SECOND / "workspace", outside)
        else:
            plant_symlink(mount / SECOND, outside)

    # Act
    run_dir, _ = await run_hostile_walkthrough(tmp_path, plant)

    # Assert: nothing was written into the host directory; the run has real directories
    assert list(outside.iterdir()) == []
    workspace = run_dir / "skills" / SECOND / "workspace"
    assert workspace.is_dir()
    assert not workspace.is_symlink()
    assert not (run_dir / "skills" / SECOND).is_symlink()
    assert (workspace / "SKILL.md").is_file()


async def test_symlinked_fixture_repo_never_runs_git_in_a_host_repository(tmp_path, outside):
    # Arrange: the encode-repo fixture dir pre-planted as a link to a real host repository
    host_repo = outside / "important-repo"
    host_repo.mkdir()
    git("init", "-q", cwd=host_repo)
    git("config", "user.email", "me@example.com", cwd=host_repo)
    git("config", "user.name", "Me", cwd=host_repo)
    (host_repo / "work.txt").write_text("precious\n")
    git("add", "-A", cwd=host_repo)
    git("commit", "-q", "-m", "my work", cwd=host_repo)
    head_before = git("rev-parse", "HEAD", cwd=host_repo)
    config_before = (host_repo / ".git" / "config").read_text()

    def plant(mount):
        (mount / FIXTURE_SKILL / "workspace").mkdir(parents=True)
        plant_symlink(mount / FIXTURE_SKILL / "workspace" / "fixture-repo", host_repo)

    # Act
    run_dir, _ = await run_hostile_walkthrough(tmp_path, plant, skills=(FIRST, FIXTURE_SKILL))

    # Assert: the host repository is untouched and the agent got a genuine fixture repo
    assert git("rev-parse", "HEAD", cwd=host_repo) == head_before
    assert (host_repo / ".git" / "config").read_text() == config_before
    assert sorted(path.name for path in host_repo.iterdir() if path.name != ".git") == [
        "work.txt",
    ]
    fixture = run_dir / "skills" / FIXTURE_SKILL / "workspace" / "fixture-repo"
    assert not fixture.is_symlink()
    assert_committed_fixture(fixture)


def make_fake_container(tmp_path):
    """An AgentContainer wired to a fake docker client that streams one UTF-8 chunk."""

    class Stream:
        _response = SimpleNamespace(close=lambda: None)

        def __iter__(self):
            return iter(["session says ok \u2014 done".encode()])

    api = SimpleNamespace(
        exec_create=lambda container_id, cmd: {"Id": "exec-1"},
        exec_start=lambda exec_id, stream: Stream(),
        exec_inspect=lambda exec_id: {"ExitCode": 0},
    )
    run_dir = tmp_path / "run"
    (run_dir / "skills" / FIRST).mkdir(parents=True)
    container = AgentContainer(HarnessConfig(), run_dir, server_url=THROWAWAY_URL)
    container._client = SimpleNamespace(api=api)  # noqa: SLF001
    container._container = SimpleNamespace(id="container-1")  # noqa: SLF001
    return container, run_dir / "skills" / FIRST


def test_session_log_is_written_to_a_regular_file(tmp_path):
    # Arrange
    container, skill_dir = make_fake_container(tmp_path)

    # Act
    exit_code, _ = container._exec(["true"], skill_dir / "session.log")  # noqa: SLF001

    # Assert
    assert exit_code == 0
    assert (skill_dir / "session.log").read_text(encoding="utf-8") == "session says ok \u2014 done"


def test_symlinked_session_log_does_not_overwrite_a_host_file(tmp_path, outside):
    # Arrange: the agent linked session.log to a host file before the exec output landed
    container, skill_dir = make_fake_container(tmp_path)
    victim = outside / "authorized_keys"
    victim.write_text("ssh-rsa ORIGINAL\n")
    plant_symlink(skill_dir / "session.log", victim)

    # Act
    container._exec(["true"], skill_dir / "session.log")  # noqa: SLF001

    # Assert
    assert victim.read_text() == "ssh-rsa ORIGINAL\n"
    assert not (skill_dir / "session.log").is_symlink()


# ---- safe_io primitives -------------------------------------------------------------


def test_read_bytes_refuses_a_symlinked_parent_directory(tmp_path, outside):
    # Arrange: root/linked -> outside, and outside/data holds bytes
    (outside / "data").write_bytes(b"host bytes")
    plant_symlink(tmp_path / "linked", outside)

    # Act / Assert
    with pytest.raises(UnsafePathError, match="symlink"):
        read_bytes(tmp_path / "linked" / "data", tmp_path)


def test_read_bytes_refuses_a_symlinked_file_even_without_a_root(tmp_path, outside):
    # Arrange
    (outside / "data").write_bytes(b"host bytes")
    plant_symlink(tmp_path / "file", outside / "data")

    # Act / Assert
    with pytest.raises(UnsafePathError, match="symlink"):
        read_bytes(tmp_path / "file")


def test_read_bytes_reads_regular_files_and_reports_missing_ones(tmp_path):
    # Arrange
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "data").write_bytes(b"\xe2\x80\x94")

    # Act / Assert
    assert read_bytes(tmp_path / "nested" / "data", tmp_path) == b"\xe2\x80\x94"
    with pytest.raises(FileNotFoundError):
        read_bytes(tmp_path / "nested" / "absent", tmp_path)
    with pytest.raises(FileNotFoundError):
        read_bytes(tmp_path / "absent" / "data", tmp_path)


@posix_only
def test_read_bytes_refuses_a_directory(tmp_path):
    # Arrange
    (tmp_path / "report.json").mkdir()

    # Act / Assert
    with pytest.raises(UnsafePathError, match="not a regular file"):
        read_bytes(tmp_path / "report.json", tmp_path)


@posix_only
def test_load_report_ignores_a_directory_named_report_json(tmp_path):
    # Arrange
    (tmp_path / "report.json").mkdir()

    # Act
    outcome = load_report(tmp_path / "report.json", tmp_path)

    # Assert: same finding as a missing report
    assert outcome.status == "missing"


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="needs POSIX named pipes")
def test_a_planted_fifo_does_not_block_the_host(tmp_path):
    # Arrange: opening a FIFO for reading blocks until a writer shows up
    fifo = tmp_path / "report.json"
    os.mkfifo(fifo)
    outcome = {}

    def read():
        try:
            read_bytes(fifo, tmp_path)
        except BaseException as exc:  # noqa: BLE001 - recorded for the assertions below
            outcome["error"] = exc

    reader = threading.Thread(target=read, daemon=True)

    # Act
    reader.start()
    reader.join(timeout=5)
    stuck = reader.is_alive()
    if stuck:  # release the blocked open() so the daemon thread does not linger
        os.close(os.open(fifo, os.O_RDWR))
        reader.join(timeout=5)

    # Assert
    assert not stuck, "reading a FIFO blocked the host"
    assert isinstance(outcome["error"], UnsafePathError)


def test_write_bytes_replaces_a_planted_symlink_without_touching_its_target(
    tmp_path, outside,
):
    # Arrange
    victim = outside / "victim"
    victim.write_text("ORIGINAL")
    plant_symlink(tmp_path / "out.txt", victim)

    # Act
    write_bytes(tmp_path / "out.txt", b"new", tmp_path)

    # Assert
    assert victim.read_text() == "ORIGINAL"
    assert (tmp_path / "out.txt").read_bytes() == b"new"
    assert not (tmp_path / "out.txt").is_symlink()


def test_write_text_overwrites_an_existing_regular_file_as_utf8(tmp_path):
    # Arrange
    (tmp_path / "out.txt").write_text("a much longer previous content", encoding="utf-8")

    # Act
    write_text(tmp_path / "out.txt", "short \u2014", tmp_path)

    # Assert
    assert (tmp_path / "out.txt").read_bytes() == "short \u2014".encode()


def test_make_dirs_replaces_a_symlinked_component(tmp_path, outside):
    # Arrange
    plant_symlink(tmp_path / "a", outside)

    # Act
    make_dirs(tmp_path / "a" / "b", tmp_path)

    # Assert
    assert (tmp_path / "a" / "b").is_dir()
    assert not (tmp_path / "a").is_symlink()
    assert list(outside.iterdir()) == []


def test_writes_outside_the_root_are_refused(tmp_path, outside):
    # Arrange
    root = tmp_path / "mount"
    root.mkdir()

    # Act / Assert
    with pytest.raises(UnsafePathError, match="not inside"):
        write_bytes(outside / "x", b"x", root)
    assert list(outside.iterdir()) == []


def test_replace_tree_swaps_whatever_the_agent_left_for_a_fresh_copy(tmp_path, outside):
    # Arrange: a trusted source tree; the destination is a link to a populated host dir
    source = tmp_path / "src"
    (source / "inner").mkdir(parents=True)
    (source / "inner" / "f.txt").write_text("fresh")
    (outside / "keep.txt").write_text("host")
    root = tmp_path / "mount"
    root.mkdir()
    plant_symlink(root / "dest", outside)

    # Act
    replace_tree(source, root / "dest", root)

    # Assert
    assert (root / "dest" / "inner" / "f.txt").read_text() == "fresh"
    assert not (root / "dest").is_symlink()
    assert [path.name for path in outside.iterdir()] == ["keep.txt"]

    # and a directory the agent pre-populated is replaced, not merged
    (root / "dest" / "stale.txt").write_text("agent")
    replace_tree(source, root / "dest", root)
    assert not (root / "dest" / "stale.txt").exists()
