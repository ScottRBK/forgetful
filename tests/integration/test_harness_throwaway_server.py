"""Integration tests for the throwaway server's independence from its host.

The harness boots a real `forgetful serve` for an agent to walk through, so the
instance under test must not depend on who runs the harness: not on settings exported
in the shell or kept in the user-config dotenv file, not on which `forgetful` happens to
be first on PATH, and not on proxy variables. Everything here is host-side mechanics
exercised without booting a server (the real boot lives in
tests/e2e_sqlite/test_harness_throwaway_server_sqlite.py).
"""
import os
import sys
from pathlib import Path

import pytest

from test_harness import server as server_mod
from test_harness.server import HarnessInfraError, ThrowawayForgetful

# ---------------------------------------------------------------------------
# Which forgetful is launched
# ---------------------------------------------------------------------------

class _FakeProcess:
    pid = 0

    def poll(self):
        return None

    def terminate(self):
        pass

    def wait(self, timeout=None):
        return 0

    def kill(self):
        pass


def _fake_env(root: Path, name: str, *, with_script: bool) -> Path:
    """A venv-shaped dir: <root>/<name>/bin/python (+ forgetful). Returns its bin dir."""
    bin_dir = root / name / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "python").write_text("")
    if with_script:
        (bin_dir / "forgetful").write_text("")
    return bin_dir


@pytest.fixture
def launched(monkeypatch):
    """argv of every server launch; no process is started and boot is declared done."""
    argvs: list[list[str]] = []

    def fake_popen(argv, **kwargs):
        argvs.append([str(arg) for arg in argv])
        return _FakeProcess()

    monkeypatch.setattr(server_mod.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(ThrowawayForgetful, "_wait_until_healthy", lambda self: None)
    return argvs


def _start(run_dir: Path) -> None:
    server = ThrowawayForgetful(run_dir)
    server.start()
    server.stop()


def test_server_comes_from_the_running_interpreter_not_a_path_shadow(
    tmp_path, monkeypatch, launched,
):
    # Arrange: the harness runs in one environment while another environment's
    # forgetful (a uv tool install, another venv, the other Python of the 3.12/3.14
    # matrix) comes first on PATH
    own_bin = _fake_env(tmp_path, "own", with_script=True)
    foreign_bin = _fake_env(tmp_path, "foreign", with_script=True)
    monkeypatch.setattr(sys, "executable", str(own_bin / "python"))
    monkeypatch.setenv("PATH", f"{foreign_bin}{os.pathsep}{os.environ['PATH']}")
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    # Act
    _start(run_dir)

    # Assert
    assert launched[0][0] == str(own_bin / "forgetful")


def test_server_starts_from_an_unactivated_environment(tmp_path, monkeypatch, launched):
    # Arrange: `.venv/bin/python -m pytest` with no venv bin dir on PATH at all
    own_bin = _fake_env(tmp_path, "own", with_script=True)
    monkeypatch.setattr(sys, "executable", str(own_bin / "python"))
    monkeypatch.setenv("PATH", str(tmp_path))
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    # Act
    _start(run_dir)

    # Assert
    assert launched[0][0] == str(own_bin / "forgetful")


def test_interpreter_without_its_own_script_falls_back_to_path(
    tmp_path, monkeypatch, launched,
):
    # Arrange: a bare system python with a globally installed forgetful on PATH
    bare_bin = _fake_env(tmp_path, "bare", with_script=False)
    global_bin = _fake_env(tmp_path, "global", with_script=True)
    (global_bin / "forgetful").chmod(0o755)
    monkeypatch.setattr(sys, "executable", str(bare_bin / "python"))
    monkeypatch.setenv("PATH", str(global_bin))
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    # Act
    _start(run_dir)

    # Assert
    assert Path(launched[0][0]) == global_bin / "forgetful"


def test_missing_console_script_is_a_harness_infra_error(
    tmp_path, monkeypatch, launched,
):
    # Arrange
    bare_bin = _fake_env(tmp_path, "bare", with_script=False)
    monkeypatch.setattr(sys, "executable", str(bare_bin / "python"))
    monkeypatch.setenv("PATH", str(tmp_path))
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    # Act / Assert
    with pytest.raises(HarnessInfraError, match="forgetful console script"):
        ThrowawayForgetful(run_dir).start()
    assert launched == []
