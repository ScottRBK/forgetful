"""Integration tests for the harness container's image build, bind mounts and credentials.

Covers the host-side mechanics of `test_harness/container.py` that decide whether a run can
start at all: where the mount sources point, which user the container runs as and who can
read the staged credentials, how a forced image rebuild behaves, and how a missing tool or
SDK is reported. The docker SDK and every subprocess are faked at the edge, so no daemon,
network or model is involved; the real container round-trip stays with live harness runs.
"""
import asyncio
import importlib
import os
import shutil
import subprocess
import sys
import types
from pathlib import Path

import pytest

from test_harness import __main__ as harness_main
from test_harness import container as container_mod
from test_harness.__main__ import config_from_argv, main
from test_harness.config import HarnessConfig
from test_harness.container import (
    AgentContainer,
    ensure_image,
    export_requirements,
)
from test_harness.server import HarnessInfraError

SERVER_URL = "http://host.docker.internal:59999"
posix_only = pytest.mark.skipif(sys.platform == "win32", reason="POSIX modes and uids")


class _StopRun(Exception):
    """Raised by the fake containers.run so a run ends once the mounts are handed over."""


@pytest.fixture
def staged():
    """Staging registry that cleans up its /tmp dirs (in production stop() owns this)."""
    dirs: list[Path] = []
    yield dirs
    for staging in dirs:
        shutil.rmtree(staging, ignore_errors=True)


@pytest.fixture
def fake_docker(monkeypatch):
    """Stand-in for docker-py (an optional dependency group): only what container.py uses."""
    errors = types.SimpleNamespace()
    errors.DockerException = type("DockerException", (Exception,), {})
    errors.NotFound = type("NotFound", (errors.DockerException,), {})
    errors.ImageNotFound = type("ImageNotFound", (errors.NotFound,), {})
    state = types.SimpleNamespace(image_labels=None, runs=[], run_error=None)

    class _Images:
        def get(self, name):
            if state.image_labels is None:
                raise errors.ImageNotFound(name)
            return types.SimpleNamespace(labels=state.image_labels)

    class _Containers:
        def get(self, name):
            raise errors.NotFound(name)

        def run(self, **kwargs):
            state.runs.append(kwargs)
            if state.run_error is not None:
                raise state.run_error
            return types.SimpleNamespace(
                id="fake-container", stop=lambda timeout=0: None, remove=lambda: None,
            )

    client = types.SimpleNamespace(images=_Images(), containers=_Containers())
    module = types.ModuleType("docker")
    module.errors = errors
    module.from_env = lambda: client
    monkeypatch.setitem(sys.modules, "docker", module)
    return state


@pytest.fixture
def host_home(tmp_path, monkeypatch):
    """A HOME holding the opencode auth file, so provisioning finds credentials."""
    home = tmp_path / "home"
    auth = home / ".local" / "share" / "opencode" / "auth.json"
    auth.parent.mkdir(parents=True)
    auth.write_text("{}")
    monkeypatch.setenv("HOME", str(home))
    return home


def _fake_uv_build(repo_root: Path):
    """subprocess.run stand-in whose `uv build -o X` resolves a relative X against the
    child's cwd, exactly like the real uv does."""

    def fake_run(cmd, *args, cwd=None, **kwargs):
        assert cmd[:2] == ["uv", "build"], cmd
        out = Path(cwd or os.getcwd()) / cmd[cmd.index("-o") + 1]
        out.mkdir(parents=True, exist_ok=True)
        (out / "forgetful-0.0.0-py3-none-any.whl").write_text("wheel")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    return fake_run


# --- relative paths must not reach dockerd or uv ------------------------------------


def test_relative_output_flag_is_resolved_to_an_absolute_path(tmp_path, monkeypatch):
    # Arrange: harness launched from an arbitrary cwd with a relative artifacts root
    monkeypatch.chdir(tmp_path)

    # Act
    config = config_from_argv(["--output", "uat-runs"])

    # Assert: dockerd reads a bind source that doesn't start with "/" as a named volume
    assert config.output_dir.is_absolute()
    assert config.output_dir == (tmp_path / "uat-runs").resolve()


def test_relative_env_dirs_are_resolved_and_home_is_expanded(tmp_path, monkeypatch):
    # Arrange
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("TEST_HARNESS_OUTPUT_DIR", "rel/out")
    monkeypatch.setenv("TEST_HARNESS_SKILLS_DIR", "~/skills")

    # Act
    config = HarnessConfig()

    # Assert
    assert config.output_dir == (tmp_path / "rel" / "out").resolve()
    assert config.skills_dir == (tmp_path / "home" / "skills").resolve()


def test_run_with_relative_output_mounts_absolute_dirs_holding_the_wheel(
    tmp_path, monkeypatch, fake_docker, host_home,
):
    # Arrange: launched from a cwd that is not the repo root, `--output runs`; only the
    # edges are faked (image build, throwaway server, uv build)
    work = tmp_path / "work"
    work.mkdir()
    fake_repo = tmp_path / "repo"
    fake_repo.mkdir()
    monkeypatch.chdir(work)
    monkeypatch.setattr(container_mod, "_REPO_ROOT", fake_repo)
    monkeypatch.setattr(harness_main, "ensure_image", lambda rebuild=False, log=print: None)

    class _FakeServer:
        url = "http://127.0.0.1:59999"

        def __init__(self, run_dir):
            self.run_dir = run_dir

        def start(self):
            pass

        async def seed_skills(self, skills_dir, catalog):
            pass

        def stop(self):
            pass

    monkeypatch.setattr(harness_main, "ThrowawayForgetful", _FakeServer)
    monkeypatch.setattr(container_mod.subprocess, "run", _fake_uv_build(fake_repo))
    fake_docker.run_error = _StopRun()
    config = config_from_argv(["--output", "runs", "--skills", "forgetful-remember"])

    # Act
    with pytest.raises(_StopRun):
        asyncio.run(harness_main._run(config))

    # Assert: every bind source is absolute, and the dir mounted at /harness is the one
    # `uv build -o` wrote the wheel into (it runs with cwd=<repo root>)
    (kwargs,) = fake_docker.runs
    sources = list(kwargs["volumes"])
    assert all(os.path.isabs(source) for source in sources), sources
    harness_src = next(s for s, spec in kwargs["volumes"].items() if spec["bind"] == "/harness")
    assert list(Path(harness_src).glob("*.whl"))
    assert (Path(harness_src) / "runner.py").exists()


def test_container_given_a_relative_run_dir_still_mounts_absolute_dirs(
    tmp_path, monkeypatch, fake_docker, host_home,
):
    # Arrange: AgentContainer used directly, so the config never had a chance to resolve
    work = tmp_path / "work"
    work.mkdir()
    fake_repo = tmp_path / "repo"
    fake_repo.mkdir()
    monkeypatch.chdir(work)
    monkeypatch.setattr(container_mod, "_REPO_ROOT", fake_repo)
    monkeypatch.setattr(container_mod.subprocess, "run", _fake_uv_build(fake_repo))
    monkeypatch.setattr(AgentContainer, "_exec", lambda self, cmd, log_path=None: (0, ""))
    (work / "runs" / "run1").mkdir(parents=True)
    agent = AgentContainer(HarnessConfig(), Path("runs/run1"), SERVER_URL)

    # Act
    agent.start()
    agent.stop()

    # Assert
    (kwargs,) = fake_docker.runs
    assert all(os.path.isabs(source) for source in kwargs["volumes"])
    harness_src = next(s for s, spec in kwargs["volumes"].items() if spec["bind"] == "/harness")
    assert list(Path(harness_src).glob("*.whl"))


# --- tool and SDK failures are infra failures (exit 2), not tracebacks ---------------


def _spawn_failure(tool):
    return FileNotFoundError(2, "No such file or directory", tool)


@pytest.mark.parametrize(
    "error",
    [
        _spawn_failure("uv"),
        subprocess.CalledProcessError(1, ["uv", "export"], output="", stderr="lock stale"),
    ],
    ids=["uv-missing", "uv-export-fails"],
)
def test_export_requirements_failure_is_an_infra_error(monkeypatch, error):
    # Arrange
    def fake_run(cmd, *args, **kwargs):
        raise error

    monkeypatch.setattr(container_mod.subprocess, "run", fake_run)

    # Act / Assert
    with pytest.raises(HarnessInfraError, match="uv"):
        export_requirements()


def test_export_failure_message_carries_uv_stderr(monkeypatch):
    # Arrange
    def fake_run(cmd, *args, **kwargs):
        raise subprocess.CalledProcessError(2, cmd, output="", stderr="lock out of date")

    monkeypatch.setattr(container_mod.subprocess, "run", fake_run)

    # Act / Assert
    with pytest.raises(HarnessInfraError, match="lock out of date"):
        export_requirements()


def test_missing_docker_cli_during_image_build_is_an_infra_error(
    tmp_path, monkeypatch, fake_docker,
):
    # Arrange: uv export works, the docker CLI cannot even be spawned
    monkeypatch.setattr(container_mod, "_DOCKER_DIR", tmp_path)
    monkeypatch.setattr(container_mod, "export_requirements", lambda: "pkg==1\n")

    def fake_run(cmd, *args, **kwargs):
        raise _spawn_failure(cmd[0])

    monkeypatch.setattr(container_mod.subprocess, "run", fake_run)

    # Act / Assert
    with pytest.raises(HarnessInfraError, match="docker"):
        ensure_image(rebuild=True, log=lambda *_: None)


def test_missing_uv_while_building_the_wheel_is_an_infra_error(tmp_path, monkeypatch):
    # Arrange
    def fake_run(cmd, *args, **kwargs):
        raise _spawn_failure(cmd[0])

    monkeypatch.setattr(container_mod.subprocess, "run", fake_run)

    # Act / Assert
    with pytest.raises(HarnessInfraError, match="uv"):
        container_mod._prepare_harness_mount(tmp_path)


def test_main_exits_2_when_uv_cannot_be_spawned(tmp_path, monkeypatch, fake_docker, capsys):
    # Arrange: documented contract - 1 means partial UAT, 2 means the harness is broken
    def fake_run(cmd, *args, **kwargs):
        raise _spawn_failure(cmd[0])

    monkeypatch.setattr(container_mod.subprocess, "run", fake_run)

    # Act
    code = main(["--output", str(tmp_path / "runs")])

    # Assert
    assert code == 2
    assert "infra error" in capsys.readouterr().err


# --- a missing docker SDK is reported clearly, even with the repo's docker/ dir ------


@pytest.fixture
def no_docker_sdk(tmp_path, monkeypatch):
    """`import docker` as seen after `uv sync` without the harness group: the SDK is gone
    but the repo's top-level docker/ dir (compose files, no __init__.py) is importable as
    an empty namespace package."""
    shadow = tmp_path / "shadow"
    (shadow / "docker").mkdir(parents=True)
    (shadow / "docker" / "docker-compose.yml").write_text("services: {}\n")

    def real_sdk_dir(entry):
        return os.path.isfile(os.path.join(entry or ".", "docker", "__init__.py"))

    monkeypatch.setattr(sys, "path", [str(shadow), *(p for p in sys.path if not real_sdk_dir(p))])
    for name in [m for m in sys.modules if m == "docker" or m.startswith("docker.")]:
        monkeypatch.delitem(sys.modules, name)
    importlib.invalidate_caches()
    assert "docker" not in sys.modules
    return shadow


def test_missing_sdk_shadowed_by_repo_docker_dir_is_an_infra_error(no_docker_sdk):
    # Act / Assert: not an AttributeError from `docker.errors` / `docker.from_env`
    with pytest.raises(HarnessInfraError, match="--group harness"):
        container_mod._docker_client()


def test_missing_sdk_without_any_docker_dir_is_an_infra_error(no_docker_sdk, monkeypatch):
    # Arrange: nothing named docker anywhere on the path -> plain ModuleNotFoundError
    monkeypatch.setattr(
        sys, "path",
        [p for p in sys.path if not os.path.isdir(os.path.join(p or ".", "docker"))],
    )
    importlib.invalidate_caches()

    # Act / Assert
    with pytest.raises(HarnessInfraError, match="--group harness"):
        container_mod._docker_client()


def test_run_checks_the_sdk_before_creating_the_run_dir_or_building(
    no_docker_sdk, tmp_path, monkeypatch,
):
    # Arrange: without the SDK the container step fails anyway, but only after the image
    # build, the server boot and the skill seeding have been paid for
    def unexpected(*args, **kwargs):
        raise AssertionError("work was started before the SDK was verified")

    monkeypatch.setattr(harness_main, "ensure_image", unexpected)
    monkeypatch.setattr(harness_main, "ThrowawayForgetful", unexpected)
    config = config_from_argv(["--output", str(tmp_path / "runs")])

    # Act / Assert
    with pytest.raises(HarnessInfraError, match="--group harness"):
        asyncio.run(harness_main._run(config))
    assert not (tmp_path / "runs").exists()


def test_container_start_without_sdk_is_an_infra_error_and_stop_is_safe(
    no_docker_sdk, tmp_path,
):
    # Arrange
    agent = AgentContainer(HarnessConfig(), tmp_path, SERVER_URL)

    # Act / Assert
    with pytest.raises(HarnessInfraError, match="--group harness"):
        agent.start()
    agent.stop()  # runs from a finally; must not raise a second time


def test_main_exits_2_with_install_hint_when_sdk_is_missing(no_docker_sdk, tmp_path, capsys):
    # Act
    code = main(["--output", str(tmp_path / "runs")])

    # Assert
    assert code == 2
    assert "--group harness" in capsys.readouterr().err


