"""Integration tests for the CLI auth status / logout / token-cache hardening.

External boundaries are faked: a loopback HTTP server stands in for a secured remote
(401 on /mcp, OAuth endpoints that would register a client or start a browser flow),
and RemoteExecutor is swapped for a recording stub where only the wiring matters.
The token cache itself is the real on-disk FileTreeStore under tmp_path.
"""
import asyncio
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from app.config.settings import settings
from app.routes.cli import auth_commands, parser
from app.routes.cli import paths as cli_paths
from app.routes.cli.parser import _build_executor, _run_auth_command, build_parser

SECRET = "s3cr3t-token-VALUE-123"
SCOPE_DENIED = (
    "Tool 'get_current_user' is not permitted under current scopes. "
    "Required scope: 'read:users'"
)


def _args(argv):
    return build_parser().parse_args(argv)


@pytest.fixture
def token_cache(tmp_path, monkeypatch) -> Path:
    """Isolate the CLI config dir and return the token cache location inside it."""
    monkeypatch.setattr(cli_paths, "config_dir", lambda: tmp_path / "config")
    monkeypatch.delenv("FORGETFUL_TOKEN", raising=False)
    return cli_paths.token_cache_dir()


async def _seed_cache(cache: Path, url: str, *, access_token: str) -> None:
    """Write a genuine URL-scoped token and client registration, as a login would."""
    from fastmcp.client.auth import OAuth
    from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

    from app.routes.cli.token_storage import oauth_token_file_tree_store

    cache.mkdir(parents=True, exist_ok=True)
    adapter = OAuth(
        mcp_url=url, token_storage=oauth_token_file_tree_store(cache),
    ).token_storage_adapter
    await adapter.set_tokens(OAuthToken(access_token=access_token, token_type="Bearer"))
    await adapter.set_client_info(OAuthClientInformationFull(
        client_id="cached-client-id",
        redirect_uris=["http://localhost:1/callback"],
        token_endpoint_auth_method="none",
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"],
    ))


def _snapshot(directory: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(directory)): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


class _StubExecutor:
    """Stands in for RemoteExecutor: records construction, replays a canned outcome."""

    built: dict = {}
    outcome: object = {"name": "stub-user"}

    def __init__(self, url, *, token=None, client_factory=None):
        type(self).built = {"token": token, "client_factory": client_factory}
        self.server_url = url

    async def execute(self, tool_name, arguments):
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome

    async def close(self):
        pass


@pytest.fixture
def stub_executor(monkeypatch):
    monkeypatch.setattr("app.routes.cli.remote_executor.RemoteExecutor", _StubExecutor)
    _StubExecutor.built = {}
    _StubExecutor.outcome = {"name": "stub-user"}
    return _StubExecutor


# =============================================================================
# FORGETFUL_TOKEN normalisation (shared by tool commands and auth status)
# =============================================================================


async def test_forgetful_token_env_is_stripped_for_tool_commands(monkeypatch):
    monkeypatch.setattr(settings, "FORGETFUL_SERVER", "http://remote:8020")
    monkeypatch.setenv("FORGETFUL_TOKEN", f"  {SECRET}\r\n")

    executor = await _build_executor(_args(["tools", "list"]))

    try:
        assert executor._token == SECRET
    finally:
        await executor.close()


async def test_blank_forgetful_token_env_falls_back_to_oauth(monkeypatch, token_cache):
    monkeypatch.setattr(settings, "FORGETFUL_SERVER", "http://remote:8020")
    monkeypatch.setenv("FORGETFUL_TOKEN", "  \n")

    executor = await _build_executor(_args(["tools", "list"]))

    try:
        assert executor._token is None
    finally:
        await executor.close()


@pytest.mark.parametrize("bad_token", [f"{SECRET}\nX-Injected: 1", f"{SECRET}\x7f", f"{SECRET}-é"])
async def test_tool_command_rejects_malformed_token_without_echoing_it(
    monkeypatch, capsys, bad_token,
):
    monkeypatch.setattr(settings, "FORGETFUL_SERVER", "http://remote:8020")
    monkeypatch.setenv("FORGETFUL_TOKEN", bad_token)

    code = await parser._run_tool_command(_args(["tools", "list", "--json"]))

    captured = capsys.readouterr()
    assert code == 1
    assert "FORGETFUL_TOKEN" in captured.err
    assert SECRET not in captured.err + captured.out


async def test_auth_status_strips_forgetful_token(monkeypatch, token_cache, stub_executor, capsys):
    monkeypatch.setenv("FORGETFUL_TOKEN", f"{SECRET}\n")

    code = await auth_commands.status(server="http://remote:8020")

    assert code == 0
    assert stub_executor.built["token"] == SECRET
    assert stub_executor.built["client_factory"] is None


async def test_auth_status_rejects_malformed_token_without_echoing_it(
    monkeypatch, token_cache, stub_executor, capsys,
):
    monkeypatch.setattr(settings, "FORGETFUL_SERVER", "http://remote:8020")
    monkeypatch.setenv("FORGETFUL_TOKEN", f"{SECRET}\nsecond-line")

    code = await _run_auth_command(_args(["auth", "status"]))

    captured = capsys.readouterr()
    assert code == 1
    assert "FORGETFUL_TOKEN" in captured.err
    assert SECRET not in captured.err + captured.out
    assert stub_executor.built == {}


def test_bearer_token_env_helper_is_shared():
    """parser and auth_commands must normalise FORGETFUL_TOKEN through one helper."""
    from app.routes.cli import remote_executor

    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("FORGETFUL_TOKEN", f"\t{SECRET} ")
        assert remote_executor.bearer_token_from_env() == SECRET
        patch.setenv("FORGETFUL_TOKEN", "")
        assert remote_executor.bearer_token_from_env() is None
        patch.delenv("FORGETFUL_TOKEN")
        assert remote_executor.bearer_token_from_env() is None
        patch.setenv("FORGETFUL_TOKEN", "bad\ntoken")
        with pytest.raises(ValueError) as excinfo:
            remote_executor.bearer_token_from_env()
        assert "bad" not in str(excinfo.value)


# =============================================================================
# auth status never runs the interactive OAuth flow
# =============================================================================


async def test_auth_status_sends_cached_access_token_as_plain_bearer(
    token_cache, stub_executor, capsys,
):
    await _seed_cache(token_cache, "http://remote:8020/mcp", access_token="cached-access")

    code = await auth_commands.status(server="http://remote:8020/mcp")

    assert code == 0
    # A plain bearer client: no OAuth provider (so no registration/browser/cache writes)
    assert stub_executor.built == {"token": "cached-access", "client_factory": None}
    assert "Cached credentials: yes" in capsys.readouterr().out


async def test_auth_status_env_token_beats_cached_token(
    monkeypatch, token_cache, stub_executor,
):
    await _seed_cache(token_cache, "http://remote:8020/mcp", access_token="cached-access")
    monkeypatch.setenv("FORGETFUL_TOKEN", SECRET)

    await auth_commands.status(server="http://remote:8020/mcp")

    assert stub_executor.built["token"] == SECRET


class _FakeSecuredServer:
    """Loopback server: 401 on /mcp; the OAuth endpoints a login flow would hit."""

    def __init__(self):
        self.requests: list[tuple[str, str, str | None]] = []
        self._lock = threading.Lock()
        self._authorize_hits = 0
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args, **kwargs):
                pass

            def _respond(self):
                length = int(self.headers.get("Content-Length") or 0)
                if length:
                    self.rfile.read(length)
                path = self.path.split("?")[0]
                with outer._lock:
                    outer.requests.append((self.command, path, self.headers.get("Authorization")))
                    if path == "/authorize":
                        outer._authorize_hits += 1
                status, body, headers = outer._answer(self.command, path)
                self.send_response(status)
                for name, value in headers.items():
                    self.send_header(name, value)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            do_GET = do_POST = do_DELETE = _respond

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self._server.server_address[1]}/mcp"

    def _answer(self, method, path):
        if path == "/mcp":
            return 401, b"unauthorized", {"WWW-Authenticate": "Bearer"}
        if path == "/authorize":
            return (400 if self._authorize_hits == 1 else 200), b"x", {}
        if path == "/register" and method == "POST":
            body = json.dumps({
                "client_id": "newly-registered-client",
                "redirect_uris": ["http://localhost:1/callback"],
                "token_endpoint_auth_method": "none",
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
            }).encode()
            return 201, body, {"Content-Type": "application/json"}
        return 404, b"not found", {}

    def __enter__(self):
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *exc_info):
        self._server.shutdown()
        self._server.server_close()


async def test_auth_status_with_rejected_cached_token_stays_read_only(
    monkeypatch, token_cache, capsys,
):
    """A stale/revoked cached token makes the server answer 401. status must report it
    and exit 1 - not register a client, open a browser, wait for a callback, or
    delete/replace the cached credentials."""
    opened: list[str] = []
    monkeypatch.setattr(webbrowser, "open", lambda url, *a, **k: opened.append(url) or True)

    with _FakeSecuredServer() as server:
        await _seed_cache(token_cache, server.url, access_token="stale-token")
        before = _snapshot(token_cache)
        assert any(b"cached-client-id" in blob for blob in before.values())

        code = await asyncio.wait_for(auth_commands.status(server=server.url), timeout=20)

    err = capsys.readouterr().err
    seen = [(method, path) for method, path, _ in server.requests]
    assert code == 1
    assert "not authenticated" in err
    assert ("POST", "/register") not in seen
    assert not any(path == "/authorize" for _, path in seen)
    assert opened == []
    assert _snapshot(token_cache) == before
    # The cached token was what got sent
    assert {auth for _, path, auth in server.requests if path == "/mcp"} == {"Bearer stale-token"}
