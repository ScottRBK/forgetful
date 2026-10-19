"""The quality-gate runner wires every stage to a real gate and enforces ordering/skips."""

import os
import subprocess
import sys

import pytest

from scripts.quality import cli, core, registry, security, testing


def test_every_stage_gate_is_registered():
    for stage, groups in registry.STAGES.items():
        assert groups, stage
        for group in groups:
            assert group, stage
            for name in group:
                assert name in registry.GATES, f"{stage} references unknown gate {name}"


def test_required_tools_are_gated_before_push():
    pre_push = {name for group in registry.STAGES["pre-push"] for name in group}
    assert {
        "ruff", "mypy", "pylint", "bandit", "vulture", "semgrep", "radon-cc", "radon-mi",
        "tests", "e2e-postgres", "coverage", "compat", "memray", "trivy", "qodana",
        "gitnexus", "mutation",
    } <= pre_push


def test_selected_honours_skip_only_and_opt_in(monkeypatch):
    monkeypatch.delenv("SKIP", raising=False)
    monkeypatch.delenv("ONLY", raising=False)
    monkeypatch.delenv("MUTATION", raising=False)
    assert registry.selected("ruff")
    assert not registry.selected("mutation")
    monkeypatch.setenv("MUTATION", "1")
    assert registry.selected("mutation")
    monkeypatch.setenv("SKIP", "ruff, mypy")
    assert not registry.selected("ruff")
    assert not registry.selected("mypy")
    assert registry.selected("pylint")
    monkeypatch.setenv("ONLY", "pylint")
    assert registry.selected("pylint")
    assert not registry.selected("bandit")


def test_dotenv_exposes_only_requested_keys(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(
        "# comment\nOTHER=should-not-leak\nexport QODANA_TOKEN='tok-123'\n", encoding="utf-8",
    )
    monkeypatch.setattr(core, "ROOT", tmp_path)
    monkeypatch.delenv("QODANA_TOKEN", raising=False)
    assert core.load_dotenv_values(("QODANA_TOKEN",)) == {"QODANA_TOKEN": "tok-123"}
    monkeypatch.setenv("QODANA_TOKEN", "from-env")
    assert core.load_dotenv_values(("QODANA_TOKEN",)) == {"QODANA_TOKEN": "from-env"}


def test_dotenv_ignores_empty_values(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("QODANA_TOKEN=\n", encoding="utf-8")
    monkeypatch.setattr(core, "ROOT", tmp_path)
    monkeypatch.delenv("QODANA_TOKEN", raising=False)
    assert core.load_dotenv_values(("QODANA_TOKEN",)) == {}


def scrubbed_git_env():
    """The environment without any ``GIT_*`` variable.

    A Git hook exports ``GIT_INDEX_FILE``, ``GIT_DIR`` and friends. A git command run for a temporary
    repository that inherits them acts on the repository being committed to (or fails), so every
    git call in these tests starts from a clean environment.
    """
    return {name: value for name, value in os.environ.items() if not name.startswith("GIT_")}


def git(*args, cwd):
    return subprocess.run(  # noqa: S603
        ["git", *args],  # noqa: S607
        cwd=cwd, env=scrubbed_git_env(), check=True, capture_output=True, text=True,
    )


@pytest.fixture(autouse=True)
def _runner_git_calls_ignore_hook_environment(monkeypatch):
    """The runner under test shells out to git too; keep a surrounding hook's variables from leaking in."""
    for name in [name for name in os.environ if name.startswith("GIT_")]:
        monkeypatch.delenv(name)


def test_git_helper_ignores_the_environment_a_git_hook_exports(tmp_path, monkeypatch):
    bogus_git_dir = tmp_path / "bogus-git-dir"
    monkeypatch.setenv("GIT_INDEX_FILE", str(tmp_path / "bogus-index"))
    monkeypatch.setenv("GIT_DIR", str(bogus_git_dir))
    repo, linked = tmp_path / "repo", tmp_path / "linked"
    repo.mkdir()
    git("init", "-q", cwd=repo)
    git("-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
        "commit", "-q", "--allow-empty", "-m", "x", cwd=repo)
    git("worktree", "add", "-q", str(linked), cwd=repo)
    assert (repo / ".git").is_dir()
    assert (linked / ".git").is_file()
    assert not bogus_git_dir.exists()
    assert not (tmp_path / "bogus-index").exists()


def test_scrubbed_subprocesses_do_not_inherit_the_hook_environment(monkeypatch):
    monkeypatch.setenv("GIT_INDEX_FILE", "/nonexistent/index")
    monkeypatch.setenv("GIT_DIR", "/nonexistent/git-dir")
    probe = [sys.executable, "-c",
             "import os; print(sorted(k for k in os.environ if k.startswith('GIT_')))"]
    assert core.capture(probe)[1].strip() == "['GIT_DIR', 'GIT_INDEX_FILE']"
    assert core.capture(probe, scrub_git=True)[1].strip() == "[]"
    keep = core.capture(probe, scrub_git=True, env={"GIT_KEEP": "1"})
    assert keep[1].strip() == "['GIT_KEEP']"


def test_every_test_running_gate_scrubs_the_hook_environment(monkeypatch):
    seen = []

    def fake(argv, **kwargs):
        seen.append(kwargs.get("scrub_git", False))
        return 0, ""

    monkeypatch.setattr(testing, "check", lambda argv, **kw: (fake(argv, **kw)[0] == 0, ""))
    monkeypatch.setattr(testing, "run", fake)
    monkeypatch.setattr(testing, "docker_ready", lambda: True)
    monkeypatch.setattr(testing.shutil, "which", lambda _name: "/usr/bin/uv")
    ctx = core.Ctx(stage="ci", files=None)
    for gate in (testing.gate_snapshots, testing.gate_tests_fast, testing.gate_e2e_postgres,
                 testing.gate_compat, testing.gate_memray):
        seen.clear()
        gate(ctx)
        assert seen == [True], gate.__name__


def test_a_linked_worktree_reads_the_main_checkouts_dotenv(tmp_path, monkeypatch):
    main, linked = tmp_path / "main", tmp_path / "linked"
    main.mkdir()
    git("init", "-q", cwd=main)
    git("-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
        "commit", "-q", "--allow-empty", "-m", "x", cwd=main)
    git("worktree", "add", "-q", str(linked), cwd=main)
    (main / ".env").write_text("QODANA_TOKEN=from-main\n", encoding="utf-8")
    monkeypatch.setattr(core, "ROOT", linked)
    monkeypatch.delenv("QODANA_TOKEN", raising=False)
    assert core.dotenv_paths() == [linked / ".env", (main / ".env").resolve()]
    assert core.load_dotenv_values(("QODANA_TOKEN",)) == {"QODANA_TOKEN": "from-main"}
    (linked / ".env").write_text("QODANA_TOKEN=own\n", encoding="utf-8")
    assert core.load_dotenv_values(("QODANA_TOKEN",)) == {"QODANA_TOKEN": "own"}


def test_trivy_is_found_only_through_trivy_bin_path_or_docker(tmp_path, monkeypatch):
    stale = tmp_path / ".local" / "bin" / "trivy-bin"
    stale.mkdir(parents=True)
    (stale / "trivy").write_text("#!/bin/sh\n", encoding="utf-8")
    monkeypatch.setattr(security.Path, "home", classmethod(lambda _cls: tmp_path))
    monkeypatch.delenv("TRIVY_BIN", raising=False)
    monkeypatch.setattr(security.shutil, "which", lambda _name: None)
    monkeypatch.setattr(security, "docker_ready", lambda: False)
    with pytest.raises(core.Skip, match="trivy unavailable"):
        security.trivy_cmd()
    explicit = tmp_path / "my-trivy"
    explicit.write_text("#!/bin/sh\n", encoding="utf-8")
    monkeypatch.setenv("TRIVY_BIN", str(explicit))
    assert security.trivy_cmd()[0] == str(explicit)


def test_qodana_is_skipped_without_cli_or_token(tmp_path, monkeypatch):
    ctx = core.Ctx(stage="pre-push", files=None)
    monkeypatch.setattr(security.shutil, "which", lambda _name: None)
    with pytest.raises(core.Skip, match="CLI"):
        security.gate_qodana(ctx)
    monkeypatch.setattr(security.shutil, "which", lambda _name: "/usr/bin/qodana")
    monkeypatch.setattr(core, "ROOT", tmp_path)
    monkeypatch.setattr(core, "dotenv_paths", lambda: [tmp_path / ".env"])
    monkeypatch.delenv("QODANA_TOKEN", raising=False)
    with pytest.raises(core.Skip, match="QODANA_TOKEN"):
        security.gate_qodana(ctx)


def test_scoped_ctx_filters_python_files():
    ctx = core.Ctx(stage="pre-commit", files=["app/a.py", "README.md", "tests/t.py"])
    assert ctx.scoped
    assert ctx.py_files() == ["app/a.py", "tests/t.py"]
    assert ctx.py_files(("app/",)) == ["app/a.py"]
    assert not core.Ctx(stage="ci", files=None).scoped
    with pytest.raises(core.Skip):
        core.scoped_paths(core.Ctx(stage="pre-commit", files=["README.md"]), ["."], ("",))


def test_stage_stops_at_first_failing_group(monkeypatch, capsys):
    calls = []

    def fake(name, ok=True):
        def gate(_ctx):
            calls.append(name)
            return ok, f"{name} output"
        return gate

    monkeypatch.setattr(registry, "GATES", {
        "a": (fake("a"), ""), "b": (fake("b", ok=False), ""), "c": (fake("c"), ""),
    })
    monkeypatch.setattr(registry, "STAGES", {"ci": [["a"], ["b"], ["c"]]})
    monkeypatch.delenv("SKIP", raising=False)
    monkeypatch.delenv("ONLY", raising=False)
    assert cli.run_stage("ci") == 1
    assert calls == ["a", "b"]
    assert "b output" in capsys.readouterr().out

    calls.clear()
    monkeypatch.setenv("SKIP", "b")
    assert cli.run_stage("ci") == 0
    assert calls == ["a", "c"]
    assert cli.run_stage("nope") == 2


def test_skip_reason_is_reported_not_failed(monkeypatch):
    def gate(_ctx):
        raise core.Skip("tool missing")

    monkeypatch.setattr(registry, "GATES", {"x": (gate, "")})
    result = cli.run_gate("x", core.Ctx(stage="ci", files=None))
    assert (result.status, result.note) == ("SKIP", "tool missing")


def test_install_hooks_points_git_at_githooks(tmp_path, monkeypatch):
    git("init", "-q", str(tmp_path), cwd=tmp_path)
    hooks = tmp_path / ".githooks"
    hooks.mkdir()
    (hooks / "pre-commit").write_text("#!/bin/sh\n", encoding="utf-8")
    monkeypatch.setattr(core, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    assert cli.install_hooks() == 0
    value = git("config", "core.hooksPath", cwd=tmp_path).stdout.strip()
    assert value == ".githooks"
    assert cli.uninstall_hooks() == 0


def _mutmut(monkeypatch, run_result, results_text):
    monkeypatch.setenv("MUTATION_TARGETS", "app.utils.*")
    monkeypatch.delenv("MUTATION_MAX_SURVIVORS", raising=False)

    def fake_run(argv, **_kwargs):
        return run_result if "run" in argv else (0, results_text)

    monkeypatch.setattr(testing, "run", fake_run)
    return testing.gate_mutation(core.Ctx(stage="manual", files=None))


def test_mutant_statuses_keep_only_targeted_modules():
    results = "Survived:\n    app.utils.a.x_f__mutmut_1: survived\n    app.other.b.x_g__mutmut_2: survived\n"
    assert testing.mutant_statuses(results, ["app.utils.*"]) == {"app.utils.a.x_f__mutmut_1": "survived"}


def test_mutation_gate_fails_when_the_suite_cannot_run(monkeypatch):
    ok, out = _mutmut(monkeypatch, (1, "failed to collect stats. runner returned 1"), "")
    assert not ok
    assert "could not run the test suite" in out


def test_mutation_gate_never_passes_on_untested_mutants(monkeypatch):
    ok, out = _mutmut(monkeypatch, (0, ""), "app.utils.a.x_f__mutmut_1: not checked\n")
    assert not ok
    assert "never tested" in out


def test_mutation_gate_counts_survivors_against_the_tolerance(monkeypatch):
    ok, out = _mutmut(monkeypatch, (0, ""), "app.utils.a.x_f__mutmut_1: survived\n")
    assert not ok
    assert "1 mutants not killed" in out
    monkeypatch.setenv("MUTATION_MAX_SURVIVORS", "1")
    assert testing.gate_mutation(core.Ctx(stage="manual", files=None)) == (True, "")


def test_mutation_gate_passes_when_everything_is_killed(monkeypatch):
    assert _mutmut(monkeypatch, (0, ""), "") == (True, "")
