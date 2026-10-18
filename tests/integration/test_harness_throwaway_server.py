"""Integration tests for the throwaway server's independence from its host.

The harness boots a real `forgetful serve` for an agent to walk through, so the
instance under test must not depend on who runs the harness: not on settings exported
in the shell or kept in the user-config dotenv file, not on which `forgetful` happens to
be first on PATH, and not on proxy variables. Everything here is host-side mechanics
exercised without booting a server (the real boot lives in
tests/e2e_sqlite/test_harness_throwaway_server_sqlite.py).
"""
import asyncio
import os
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from test_harness import server as server_mod
from test_harness.server import (
    HarnessInfraError,
    ThrowawayForgetful,
    _plain_client_factory,
)

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


# ---------------------------------------------------------------------------
# Loopback traffic must bypass HTTP(S)_PROXY
# ---------------------------------------------------------------------------

class _HealthyBackend(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        self.send_response(200 if self.path == "/health" else 404)
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):
        pass


def _unreachable_proxy(seen: list[str]):
    """Forward-proxy handler that records what it is asked for and answers 502, as a
    real proxy does for a host-local loopback address it cannot reach."""

    class _Proxy(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            seen.append(self.path)  # absolute-form URI when used as a forward proxy
            self.send_response(502)
            self.send_header("Content-Length", "0")
            self.end_headers()

        do_POST = do_GET  # noqa: N815

        def log_message(self, *args):
            pass

    return _Proxy


def _serve(handler) -> ThreadingHTTPServer:
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


@pytest.fixture
def proxy_requests(monkeypatch):
    """Point HTTP_PROXY at a proxy that cannot reach loopback, with NO_PROXY unset."""
    seen: list[str] = []
    proxy = _serve(_unreachable_proxy(seen))
    for var in ("NO_PROXY", "no_proxy", "ALL_PROXY", "all_proxy",
                "HTTPS_PROXY", "https_proxy"):
        monkeypatch.delenv(var, raising=False)
    proxy_url = f"http://127.0.0.1:{proxy.server_address[1]}"
    monkeypatch.setenv("HTTP_PROXY", proxy_url)
    monkeypatch.setenv("http_proxy", proxy_url)
    yield seen
    proxy.shutdown()


def test_health_probe_ignores_proxy_env(proxy_requests, tmp_path):
    # Arrange: a perfectly healthy loopback server
    backend = _serve(_HealthyBackend)
    try:
        server = ThrowawayForgetful(run_dir=tmp_path, boot_timeout=3)
        server.port = backend.server_address[1]
        server.process = _FakeProcess()

        # Act
        server._wait_until_healthy()
    finally:
        backend.shutdown()

    # Assert: it was found healthy without ever involving the proxy
    assert proxy_requests == []


def test_seeding_client_ignores_proxy_env(proxy_requests):
    # Arrange: a real MCP server over streamable HTTP on loopback
    import uvicorn
    from fastmcp import FastMCP

    mcp = FastMCP("probe")

    @mcp.tool
    def ping() -> str:
        return "pong"

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    uv = uvicorn.Server(uvicorn.Config(
        mcp.http_app(transport="http"), host="127.0.0.1", port=port, log_level="error",
    ))
    thread = threading.Thread(target=uv.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not uv.started and time.monotonic() < deadline:
        time.sleep(0.05)
    assert uv.started

    async def list_tool_names():
        client = _plain_client_factory(f"http://127.0.0.1:{port}/mcp", None)
        async with client:
            return [tool.name for tool in await client.list_tools()]

    # Act
    try:
        names = asyncio.run(asyncio.wait_for(list_tool_names(), timeout=10))
    finally:
        uv.should_exit = True
        thread.join(timeout=5)

    # Assert
    assert names == ["ping"]
    assert proxy_requests == []
