"""Integration tests for the harness run lifecycle (test_harness/__main__.py + container.py).

Teardown order and exception safety, exercised without a docker daemon. Only the
outside world is faked: the docker SDK (a daemon stand-in plus a fake `docker` module,
since the optional `harness` dependency group is not installed here), the throwaway
server and the agent walkthrough. `_run` and the real `AgentContainer` start/stop code
paths are what run.
"""
import subprocess
import sys
import tempfile
import types
from pathlib import Path

import pytest

import test_harness.__main__ as harness_main
import test_harness.container as container_mod
import test_harness.server as server_mod
from test_harness.config import HarnessConfig
from test_harness.container import AgentContainer
from test_harness.server import HarnessInfraError, ThrowawayForgetful

THROWAWAY_PORT = 59999


class FakeDockerError(Exception):
    """Stands in for docker.errors.DockerException."""


class FakeNotFound(FakeDockerError):
    """Stands in for docker.errors.NotFound."""


FAKE_DOCKER = types.ModuleType("docker")
FAKE_DOCKER.errors = types.SimpleNamespace(
    DockerException=FakeDockerError, NotFound=FakeNotFound,
)


class FakeStream:
    _response = types.SimpleNamespace(close=lambda: None)

    def __init__(self, text: str):
        self._text = text

    def __iter__(self):
        return iter([self._text.encode()])


class FakeDockerContainer:
    def __init__(self, daemon, name, run_kwargs):
        self.id = f"fake-{name}"
        self.name = name
        self.run_kwargs = run_kwargs
        self._daemon = daemon

    def stop(self, timeout=10):
        if self._daemon.stop_error is not None:
            raise self._daemon.stop_error

    def remove(self, force=False):
        if self._daemon.remove_error is not None:
            raise self._daemon.remove_error
        self._daemon.registry.remove(self)


class FakeDaemon:
    """A docker client double: containers registry plus a scripted exec API."""

    def __init__(self):
        self.registry: list[FakeDockerContainer] = []
        self.created: list[FakeDockerContainer] = []
        self.commands: list[list[str]] = []
        self.stop_error: Exception | None = None
        self.remove_error: Exception | None = None
        self.server_reachable = True
        self.containers = types.SimpleNamespace(get=self._get, run=self._run)
        self.api = types.SimpleNamespace(
            exec_create=self._exec_create,
            exec_start=self._exec_start,
            exec_inspect=self._exec_inspect,
        )

    def _get(self, name):
        for item in self.registry:
            if item.name == name:
                return item
        raise FakeNotFound(name)

    def _run(self, **kwargs):
        item = FakeDockerContainer(self, kwargs["name"], kwargs)
        self.registry.append(item)
        self.created.append(item)
        return item

    def _exec_create(self, container_id, cmd):
        self.commands.append(cmd)
        return {"Id": str(len(self.commands) - 1)}

    def _outcome(self, exec_id) -> tuple[int, str]:
        cmd = self.commands[int(exec_id)]
        if "--health" in cmd:
            return 0, "HEALTHY=True\n"
        if any(part.endswith("/health") for part in cmd):
            if self.server_reachable:
                return 0, ""
            return 1, "URLError: <urlopen error [Errno 111] Connection refused>\n"
        return 0, ""

    def _exec_start(self, exec_id, stream=True):
        return FakeStream(self._outcome(exec_id)[1])

    def _exec_inspect(self, exec_id):
        return {"ExitCode": self._outcome(exec_id)[0]}


class LifecycleEnv:
    def __init__(self, daemon, config, stage_root):
        self.daemon = daemon
        self.config = config
        self.events: list[str] = []
        self.walked: list[str] = []
        self.stage_root = stage_root

    def staged_dirs(self) -> list[Path]:
        return sorted(self.stage_root.glob("uat-mount-*"))


@pytest.fixture
def env(tmp_path, monkeypatch):
    daemon = FakeDaemon()
    auth = tmp_path / "auth.json"
    auth.write_text("{}")
    stage_root = tmp_path / "stage"
    stage_root.mkdir()
    skills_dir = tmp_path / "skills"
    (skills_dir / "forgetful-recall").mkdir(parents=True)
    (skills_dir / "forgetful-recall" / "SKILL.md").write_text("# recall\n")
    (tmp_path / "runs").mkdir()
    config = HarnessConfig(
        skills=["forgetful-recall"], skills_dir=skills_dir, output_dir=tmp_path / "runs",
    )
    lifecycle = LifecycleEnv(daemon, config, stage_root)
    real_provision = container_mod.provision_agent

    def prepare_mount(run_dir):
        harness_dir = run_dir / "harness"
        harness_dir.mkdir(exist_ok=True)
        return harness_dir

    class FakeServer:
        def __init__(self, run_dir):
            self.url = f"http://127.0.0.1:{THROWAWAY_PORT}"

        def start(self):
            lifecycle.events.append("server.start")

        def stop(self):
            lifecycle.events.append("server.stop")

        async def seed_skills(self, skills_dir, names):
            return []

    class RecordingWalkthrough:
        def __init__(self, **kwargs):
            pass

        async def run_skill(self, skill):
            lifecycle.walked.append(skill)
            return types.SimpleNamespace(skill=skill, status="completed")

        def write_summary(self, results):
            pass

    monkeypatch.setitem(sys.modules, "docker", FAKE_DOCKER)
    monkeypatch.setattr(tempfile, "tempdir", str(stage_root))
    monkeypatch.setattr(container_mod, "_docker_client", lambda: daemon)
    monkeypatch.setattr(
        container_mod, "provision_agent",
        lambda agent_type, staged: real_provision(agent_type, staged, auth_path=auth),
    )
    monkeypatch.setattr(container_mod, "_prepare_harness_mount", prepare_mount)
    monkeypatch.setattr(harness_main, "ensure_image", lambda rebuild=False: None)
    monkeypatch.setattr(harness_main, "ThrowawayForgetful", FakeServer)
    monkeypatch.setattr(harness_main, "Walkthrough", RecordingWalkthrough)
    monkeypatch.setattr(harness_main, "_print_summary", lambda results, run_dir: None)
    return lifecycle


# --- exception-safe teardown -------------------------------------------------


async def test_docker_transport_error_in_stop_does_not_orphan_the_server(env):
    # Arrange: a daemon restart mid-run surfaces as a plain transport error, which
    # docker-py does not wrap into DockerException
    env.daemon.stop_error = ConnectionResetError("docker daemon went away")

    # Act
    exit_code = await harness_main._run(env.config)

    # Assert: every resource is released regardless
    assert exit_code == 0
    assert "server.stop" in env.events
    assert env.daemon.registry == []
    assert env.staged_dirs() == []


async def test_unexpected_container_teardown_error_still_stops_the_server(
    env, monkeypatch,
):
    # Arrange
    def broken_stop(self):
        raise RuntimeError("teardown blew up")

    monkeypatch.setattr(AgentContainer, "stop", broken_stop)

    # Act / Assert: the error is not masked, and the server is stopped anyway
    with pytest.raises(RuntimeError, match="teardown blew up"):
        await harness_main._run(env.config)
    assert env.events[-1] == "server.stop"


async def test_failed_server_boot_is_torn_down_and_closes_its_log(env, monkeypatch):
    # Arrange: the real ThrowawayForgetful whose child exits straight away
    servers: list[ThrowawayForgetful] = []
    real_popen = subprocess.Popen

    class BootsBadly(ThrowawayForgetful):
        def __init__(self, run_dir):
            super().__init__(run_dir)
            servers.append(self)

    def exits_immediately(args, **kwargs):
        return real_popen([sys.executable, "-c", "raise SystemExit(3)"], **kwargs)

    monkeypatch.setattr(harness_main, "ThrowawayForgetful", BootsBadly)
    monkeypatch.setattr(server_mod.shutil, "which", lambda name: name)
    monkeypatch.setattr(server_mod.subprocess, "Popen", exits_immediately)

    # Act / Assert
    with pytest.raises(HarnessInfraError, match="exited during boot"):
        await harness_main._run(env.config)
    (server,) = servers
    assert server._log_file is None, "server.log handle leaked after a failed boot"


@pytest.mark.parametrize("failing_step", ["stop", "remove"])
def test_container_stop_is_best_effort_per_step(env, tmp_path, capsys, failing_step):
    # Arrange
    (tmp_path / "run").mkdir()
    container = AgentContainer(env.config, tmp_path / "run", "http://host.docker.internal:1")
    container.start()
    assert env.staged_dirs(), "start() should have staged credential copies"
    setattr(env.daemon, f"{failing_step}_error", ConnectionResetError("daemon gone"))

    # Act: neither a failed stop nor a failed remove may escape or skip the rest
    container.stop()
    container.stop()

    # Assert
    if failing_step == "stop":
        assert env.daemon.registry == [], "remove must still be attempted"
    assert env.staged_dirs() == [], "credential copies must always be deleted"
    assert "daemon gone" in capsys.readouterr().err
