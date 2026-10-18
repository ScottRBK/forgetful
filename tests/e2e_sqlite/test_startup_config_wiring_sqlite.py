"""E2E tests for startup configuration wiring on the in-memory SQLite stack

- The default HTTP serve path must run the shutdown teardown (dispose_runtime: drain
  pending activity handlers, dispose the database engine) when the process receives
  SIGTERM (what `docker stop` sends) or SIGINT, exactly like the CORS-enabled path.
- Provenance defaults that the settings validator accepts must never break a create.

The server tests boot the real app in a child process (signals cannot be delivered to an
in-process server) with a recording wrapper around dispose_runtime, so they do not depend
on log flushing during process death.
"""
import os
import signal
import socket
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import httpx
import pytest

from app.config.settings import PROVENANCE_MAX_LENGTHS, settings

_PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Runs the real `_serve` for the HTTP transport. dispose_runtime is wrapped to leave a
# synchronous marker file, so the test can tell "never started" from "started but cancelled"
# from "completed".
_SERVER_DRIVER = textwrap.dedent(
    """
    import sys
    from pathlib import Path

    import main

    marker = Path(sys.argv[1])
    original_dispose = main.dispose_runtime

    async def recording_dispose(runtime):
        marker.write_text("started")
        await original_dispose(runtime)
        marker.write_text("done")

    main.dispose_runtime = recording_dispose
    main._serve("http", "127.0.0.1", int(sys.argv[2]))
    """,
)


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _child_env(tmp_path: Path) -> dict[str, str]:
    env = dict(os.environ)
    env.update({
        "PYTHONPATH": str(_PROJECT_ROOT),
        # Keep the developer's ~/.config/forgetful/.env out of the child's settings.
        "XDG_CONFIG_HOME": str(tmp_path / "config"),
        "DATABASE": "SQLite",
        "SQLITE_MEMORY": "true",
        "EMBEDDING_PROVIDER": "FastEmbed",
        "RERANKING_ENABLED": "false",
        "ACTIVITY_ENABLED": "true",
        "CORS_ENABLED": "false",
        "FASTMCP_SERVER_AUTH": "",
        "FORGETFUL_SERVER": "",
        "LOG_LEVEL": "INFO",
    })
    return env


def _wait_until_healthy(process: subprocess.Popen, port: int, log_path: Path, timeout: float = 90) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            pytest.fail(f"server exited during boot (rc={process.returncode}):\n{log_path.read_text()[-3000:]}")
        try:
            if httpx.get(f"http://127.0.0.1:{port}/health", timeout=2).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.25)
    process.kill()
    pytest.fail(f"server not healthy after {timeout}s:\n{log_path.read_text()[-3000:]}")


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX signal delivery")
@pytest.mark.parametrize("sig", [signal.SIGTERM, signal.SIGINT], ids=["SIGTERM", "SIGINT"])
def test_default_http_serve_disposes_runtime_on_shutdown_signal(tmp_path, sig):
    """Regression: mcp.run() deferred the lifespan teardown until after uvicorn had re-raised the
    signal, so SIGTERM killed the process with no cleanup and SIGINT cancelled it mid-dispose."""
    # Arrange
    driver = tmp_path / "driver.py"
    driver.write_text(_SERVER_DRIVER)
    marker = tmp_path / "dispose.marker"
    log_path = tmp_path / "server.log"
    port = _free_port()
    with log_path.open("w") as log:
        process = subprocess.Popen(  # noqa: S603 - test-controlled arguments, no shell
            [sys.executable, str(driver), str(marker), str(port)],
            env=_child_env(tmp_path),
            cwd=tmp_path,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    try:
        _wait_until_healthy(process, port, log_path)

        # Act
        process.send_signal(sig)
        process.wait(timeout=30)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)

    # Assert
    state = marker.read_text() if marker.exists() else "never started"
    assert state == "done", f"dispose_runtime {state} after {sig.name}:\n{log_path.read_text()[-3000:]}"


@pytest.mark.parametrize(("setting", "limit"), sorted(PROVENANCE_MAX_LENGTHS.items()))
async def test_create_succeeds_with_provenance_defaults_at_the_allowed_cap(http_client, monkeypatch, setting, limit):
    """Settings reject over-long provenance defaults up front; a value at the cap must still
    flow through create and be returned (previously over-long values failed after the insert)."""
    monkeypatch.setattr(settings, setting, "v" * limit)

    response = await http_client.post("/api/v1/memories", json={
        "title": "Provenance cap memory",
        "content": "Created with an env provenance default at its maximum length",
        "context": "Boundary of the ENCODING_* / AGENT_* settings",
        "keywords": ["provenance"],
        "tags": ["config"],
        "importance": 5,
    })

    assert response.status_code == 201, response.text
    stored = await http_client.get(f"/api/v1/memories/{response.json()['id']}")
    assert stored.json()[setting.lower()] == "v" * limit
