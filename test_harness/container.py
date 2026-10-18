"""Containerized agent execution: the OS-level write barrier around the walkthrough.

Tool scoping is not a sandbox (agent-shell enforces nothing under auto-approve), so the
agent runs inside a container that can only see the mounted skill artifacts and staged
credential copies. Mechanics are ported from eval-harness's DockerRunner: staged
writable credential mounts, one long-lived container driven by execs, an in-container
`timeout --kill-after` wrapper as the real wall-clock guard, and stop/remove plus
staged-dir cleanup on the way out.

The image bakes the locked dependency tree (rebuilt automatically when the lock
drifts); the working tree itself is installed as a wheel at container start, so every
run walks the current checkout without an image rebuild. Docker imports stay lazy:
this module is importable without the `harness` dependency group.
"""
import asyncio
import hashlib
import shutil
import subprocess
import sys
import tempfile
import threading
from os import chmod
from pathlib import Path

from test_harness.config import HarnessConfig
from test_harness.server import HarnessInfraError
from test_harness.walkthrough import SessionOutcome

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DOCKER_DIR = Path(__file__).resolve().parent / "docker"
_HASH_LABEL = "forgetful.harness.requirements-hash"
_OPENCODE_AUTH = Path("~/.local/share/opencode/auth.json")
_INSTALL_TIMEOUT = 300
_HEALTH_TIMEOUT = 180
_HOST_EXEC_GRACE = 120

IMAGE = "forgetful-test-harness:latest"
SKILLS_MOUNT = "/skills"
HARNESS_MOUNT = "/harness"
DECOY_DB = "/tmp/local-decoy.db"  # noqa: S108 - container-side path, dies with the container


def build_container_env(server_url: str) -> dict[str, str]:
    """The isolation fence, container edition: both routes point at run-scoped
    targets (mem 1701). The container is born with only this environment, so there
    are no real credentials to scrub - just none to introduce."""
    return {
        "FORGETFUL_SERVER": server_url,
        "DATABASE": "SQLite",
        "SQLITE_MEMORY": "false",
        "SQLITE_PATH": DECOY_DB,
        "EMBEDDING_PROVIDER": "FastEmbed",
        "EMBEDDING_MODEL": "BAAI/bge-small-en-v1.5",
        "EMBEDDING_DIMENSIONS": "384",
        "RERANKING_ENABLED": "false",
    }


def exec_command(timeout: float, skill: str) -> list[str]:
    """Session command with the OS-level timeout: host-side cancellation cannot kill
    a process inside the container (mem 1654), `timeout --kill-after` can."""
    return [
        "timeout", "--kill-after=30s", str(int(timeout)),
        "python", "-u", f"{HARNESS_MOUNT}/runner.py",
        "--skill-dir", f"{SKILLS_MOUNT}/{skill}",
    ]


def staged_mount(
    files: list[Path], container_dir: str, staged: list[Path],
) -> dict[str, dict[str, str]]:
    """Copy files into a throwaway dir and bind that dir read-write.

    Writable because agent-shell rewrites config files in place; copies so the host
    originals are never touched. 0o777/0o644 lets the container's non-root user
    traverse a cross-UID bind. Caller cleans up everything appended to `staged`.
    """
    staging = Path(tempfile.mkdtemp(prefix="uat-mount-"))
    chmod(staging, 0o777)  # noqa: S103 - required for cross-UID Docker binds
    for source in files:
        shutil.copy2(source, staging / source.name)
        chmod(staging / source.name, 0o644)
    staged.append(staging)
    return {str(staging): {"bind": container_dir, "mode": "rw"}}


def provision_agent(
    agent_type: str, staged: list[Path], auth_path: Path = _OPENCODE_AUTH,
) -> dict[str, dict[str, str]]:
    if agent_type != "opencode":
        raise HarnessInfraError(
            f"agent {agent_type!r} is not containerized yet - v1 walks opencode only",
        )
    auth = auth_path.expanduser()
    if not auth.exists():
        raise HarnessInfraError(
            f"opencode auth file not found at {auth} (run `opencode auth login` on the host)",
        )
    volumes = staged_mount([auth], "/home/node/.local/share/opencode", staged)
    volumes |= staged_mount(
        [_DOCKER_DIR / "opencode.json"], "/home/node/.config/opencode", staged,
    )
    return volumes


def export_requirements() -> str:
    result = subprocess.run(
        [
            "uv", "export", "--frozen", "--no-dev", "--no-emit-project",
            "--format", "requirements-txt",
        ],
        cwd=_REPO_ROOT, capture_output=True, text=True, check=True,
    )
    return result.stdout


def requirements_hash(requirements: str) -> str:
    return hashlib.sha256(requirements.encode()).hexdigest()[:16]


def _docker_client():
    import docker

    try:
        return docker.from_env()
    except docker.errors.DockerException as exc:
        raise HarnessInfraError(
            f"docker is not available ({exc}) - is Docker Desktop running?",
        ) from exc


def ensure_image(rebuild: bool = False, log=print) -> None:
    """Build the harness image when it is absent or its baked dependency tree no
    longer matches the lock file - stale images have burned real runs before
    (eval-harness mem 1622), so the lock hash is checked, not assumed."""
    import docker

    requirements = export_requirements()
    digest = requirements_hash(requirements)
    if not rebuild:
        try:
            image = _docker_client().images.get(IMAGE)
            if image.labels.get(_HASH_LABEL) == digest:
                return
            log(f"{IMAGE} was baked against different locked deps - rebuilding")
        except docker.errors.ImageNotFound:
            log(f"{IMAGE} not found - first build pulls node and the locked deps")

    (_DOCKER_DIR / "requirements.lock").write_text(requirements)
    log(f"building {IMAGE} ...")
    build = subprocess.run(
        [
            "docker", "build", "-t", IMAGE,
            "--label", f"{_HASH_LABEL}={digest}", str(_DOCKER_DIR),
        ],
        check=False,
    )
    if build.returncode != 0:
        raise HarnessInfraError(f"docker build failed (exit {build.returncode})")


def _prepare_harness_mount(run_dir: Path) -> Path:
    """Stage the read-only /harness mount: the working-tree wheel plus the runner."""
    harness_dir = run_dir / "harness"
    harness_dir.mkdir(exist_ok=True)
    build = subprocess.run(
        ["uv", "build", "--wheel", "-o", str(harness_dir)],
        cwd=_REPO_ROOT, capture_output=True, text=True, check=False,
    )
    if build.returncode != 0:
        raise HarnessInfraError(f"uv build --wheel failed:\n{build.stderr}")
    shutil.copy2(_DOCKER_DIR / "runner.py", harness_dir / "runner.py")
    return harness_dir


class AgentContainer:
    """One container per run, one exec per skill session.

    Created with the fenced environment baked in (the server URL must be known first),
    `sleep infinity` as PID 1, and the working tree installed on top of the image's
    locked deps. `stop()` is safe to call from a finally regardless of how far
    `start()` got - including while `start()` is still running in its worker thread
    (a cancelled `asyncio.to_thread` cannot interrupt it): `stop()` raises a flag that
    `start()` checks between its steps, and whichever side finds a container or staged
    credential copy releases it.
    """

    def __init__(self, config: HarnessConfig, run_dir: Path, server_url: str):
        self.config = config
        self.run_dir = run_dir
        self.server_url = server_url
        self._staged: list[Path] = []
        self._client = None
        self._container = None
        self._stopping = threading.Event()
        self._lock = threading.Lock()

    def start(self) -> None:
        import docker

        self._client = _docker_client()
        volumes = provision_agent(self.config.agent_type, self._staged)
        self._abort_if_stopping()
        skills_dir = self.run_dir / "skills"
        skills_dir.mkdir(exist_ok=True)
        volumes[str(skills_dir)] = {"bind": SKILLS_MOUNT, "mode": "rw"}
        volumes[str(_prepare_harness_mount(self.run_dir))] = {
            "bind": HARNESS_MOUNT, "mode": "ro",
        }
        self._abort_if_stopping()

        name = f"forgetful-uat-{self.run_dir.name}"
        try:
            self._client.containers.get(name).remove(force=True)
        except docker.errors.NotFound:
            pass

        environment = {
            **build_container_env(self.server_url),
            "AGENT_TYPE": self.config.agent_type,
            "AGENT_MODEL": self.config.model,
            "AGENT_EFFORT": self.config.effort or "",
            "DISALLOWED_TOOLS": "web_search,web_fetch",
        }
        try:
            self._container = self._client.containers.run(
                image=IMAGE,
                command=["sleep", "infinity"],
                volumes=volumes,
                environment=environment,
                detach=True,
                name=name,
            )
        except docker.errors.DockerException as exc:
            raise HarnessInfraError(f"could not start {IMAGE}: {exc}") from exc
        # stop() may have run while containers.run() was in flight and found nothing
        # to remove; the container is assigned before this check, so one side sees it
        self._abort_if_stopping()

        install = (
            "uv pip install --python /opt/venv/bin/python --no-deps --quiet "
            f"{HARNESS_MOUNT}/*.whl"
        )
        exit_code, output = self._exec(
            ["timeout", str(_INSTALL_TIMEOUT), "sh", "-c", install],
        )
        if exit_code != 0:
            raise HarnessInfraError(
                f"working-tree install failed (exit {exit_code}):\n{output}",
            )

    def health_check(self) -> None:
        """One-shot agent+model probe inside the container. The verdict comes from
        stdout markers, not the exit code: opencode prints provider errors and exits
        0, so only the timeout wrapper or a real crash leaves non-zero."""
        cmd = [
            "timeout", "--kill-after=10s", str(_HEALTH_TIMEOUT),
            "python", "-u", f"{HARNESS_MOUNT}/runner.py", "--health",
        ]
        exit_code, output = self._exec(cmd)
        if exit_code in (124, 137):
            raise HarnessInfraError(f"agent health check timed out after {_HEALTH_TIMEOUT}s")
        if exit_code != 0:
            raise HarnessInfraError(f"agent health check crashed (exit {exit_code}):\n{output}")
        if not any(line.strip() == "HEALTHY=True" for line in output.splitlines()):
            raise HarnessInfraError(f"agent unhealthy in container:\n{output.strip()}")

    async def run_session(
        self, *, skill: str, skill_dir: Path, workspace: Path, prompt: str, timeout: float,
    ) -> SessionOutcome:
        cmd = exec_command(timeout, skill)
        try:
            # The in-container `timeout` is the enforcement; this host-side deadline
            # only trips if the exec itself wedges - an infra failure, not a finding.
            async with asyncio.timeout(timeout + _HOST_EXEC_GRACE):
                exit_code, output = await asyncio.to_thread(
                    self._exec, cmd, skill_dir / "session.log",
                )
        except TimeoutError as exc:
            raise HarnessInfraError(
                f"docker exec for {skill} outlived the in-container timeout",
            ) from exc
        if exit_code in (124, 137):
            return SessionOutcome(
                kind="timeout", detail=f"killed by in-container timeout ({timeout:g}s)",
            )
        if exit_code != 0:
            tail = "\n".join(output.splitlines()[-15:])
            raise HarnessInfraError(f"runner exited {exit_code} for {skill}:\n{tail}")
        return SessionOutcome(kind="ran")

    def _exec(self, cmd: list[str], log_path: Path | None = None) -> tuple[int, str]:
        exec_id = self._client.api.exec_create(self._container.id, cmd)["Id"]
        stream = self._client.api.exec_start(exec_id, stream=True)
        buffer = ""
        try:
            for chunk in stream:
                buffer += chunk.decode(errors="replace")
        finally:
            # docker-py leaves the underlying response open; without this a GC race
            # throws "I/O operation on closed file" at interpreter exit (mem 1645)
            stream._response.close()  # noqa: SLF001
        if log_path is not None:
            log_path.write_text(buffer)
        return self._client.api.exec_inspect(exec_id)["ExitCode"], buffer

    def stop(self) -> None:
        """Release everything this object holds; idempotent and never raises for a
        docker failure. Safe while `start()` is still running in another thread."""
        self._stopping.set()
        self._release()

    def _abort_if_stopping(self) -> None:
        """Called by `start()` between steps: bail out (cleaning up whatever it has
        made so far) once `stop()` has been requested."""
        if self._stopping.is_set():
            self._release()
            raise HarnessInfraError("container start abandoned: the harness is shutting down")

    def _release(self) -> None:
        with self._lock:
            container, self._container = self._container, None
        try:
            if container is not None:
                self._remove(container)
        finally:
            # one at a time: start() may still be appending a staged dir
            while True:
                try:
                    staging = self._staged.pop()
                except IndexError:
                    break
                shutil.rmtree(staging, ignore_errors=True)

    def _remove(self, container) -> None:
        """Stop, then force-remove, as independent best-effort steps: a dead docker
        daemon raises requests' transport errors (not DockerException) from either
        call, and a failed stop must not leave the container undeleted."""
        for step, action in (
            ("stop", lambda: container.stop(timeout=5)),
            ("remove", lambda: container.remove(force=True)),
        ):
            try:
                action()
            except Exception as exc:
                print(
                    f"warning: could not {step} container "
                    f"forgetful-uat-{self.run_dir.name}: {exc}",
                    file=sys.stderr,
                )
