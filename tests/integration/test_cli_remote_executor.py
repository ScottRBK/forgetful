"""Integration tests for RemoteExecutor, executor selection, and auth commands (phase 4)

The fastmcp client is the one external boundary the CLI has, so it is replaced with a
stub injected through the client-factory seam. Everything else (selection precedence,
URL normalization, .env line editing, token-dir lifecycle) runs real code.
"""

from app.config.settings import settings
from app.routes.cli import auth_commands
from app.routes.cli.local_executor import LocalExecutor
from app.routes.cli.parser import _build_executor, build_parser
from app.routes.cli.remote_executor import RemoteExecutor


class StubResult:
    def __init__(self, data):
        self.data = data
        self.is_error = False


class StubClient:
    """Records call_tool invocations; stands in for fastmcp.Client."""

    def __init__(self, responses=None):
        self.calls = []
        self.closed = False
        self.pinged = False
        self._responses = list(responses or [])

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        return StubResult(self._responses.pop(0) if self._responses else {"ok": True})

    async def ping(self):
        self.pinged = True

    async def close(self):
        self.closed = True


def _args(argv):
    return build_parser().parse_args(argv)


# =============================================================================
# RemoteExecutor proxying
# =============================================================================


async def test_execute_calls_meta_tool_and_unwraps_payload():
    stub = StubClient(responses=[{"id": 42, "title": "hi"}])
    executor = RemoteExecutor(
        "http://example.com:8020", client_factory=lambda url, token: stub,
    )

    result = await executor.execute("create_memory", {"title": "hi"})

    assert stub.calls == [
        ("execute_forgetful_tool", {"tool_name": "create_memory", "arguments": {"title": "hi"}}),
    ]
    assert result == {"id": 42, "title": "hi"}


async def test_list_tools_and_tool_info_proxy_discovery_meta_tools():
    stub = StubClient(responses=[
        {"tools_by_category": {}, "total_count": 0},
        {"name": "query_memory"},
    ])
    executor = RemoteExecutor(
        "http://example.com:8020/mcp", client_factory=lambda url, token: stub,
    )

    await executor.list_tools(category="memory")
    await executor.tool_info("query_memory")

    assert stub.calls[0] == ("discover_forgetful_tools", {"category": "memory"})
    assert stub.calls[1] == ("how_to_use_forgetful_tool", {"tool_name": "query_memory"})


async def test_close_closes_client():
    stub = StubClient()
    executor = RemoteExecutor("http://example.com:8020", client_factory=lambda url, token: stub)

    await executor.close()

    assert stub.closed


async def test_close_suppresses_client_teardown_errors():
    """close() runs in the command runner's finally block after the failure has
    already been reported; a connection that never opened must not raise again
    and bury the real error under a teardown traceback."""

    class ExplodingClient(StubClient):
        async def close(self):
            raise ConnectionError("All connection attempts failed")

    executor = RemoteExecutor(
        "http://example.com:8020", client_factory=lambda url, token: ExplodingClient(),
    )

    await executor.close()


def test_server_url_normalization_appends_mcp_path():
    factory = lambda url, token: StubClient()  # noqa: E731

    bare = RemoteExecutor("http://example.com:8020", client_factory=factory)
    trailing = RemoteExecutor("http://example.com:8020/", client_factory=factory)
    custom = RemoteExecutor("http://example.com:8020/custom", client_factory=factory)
    already = RemoteExecutor("http://example.com:8020/mcp", client_factory=factory)

    assert bare.server_url == "http://example.com:8020/mcp"
    assert trailing.server_url == "http://example.com:8020/mcp"
    assert custom.server_url == "http://example.com:8020/custom"
    assert already.server_url == "http://example.com:8020/mcp"


# =============================================================================
# Executor selection precedence: --local > --server > FORGETFUL_SERVER > local default
# =============================================================================


async def test_server_flag_beats_forgetful_server_setting(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "FORGETFUL_SERVER", "http://from-settings:1")
    monkeypatch.delenv("FORGETFUL_TOKEN", raising=False)
    # Tokenless remote -> OAuth factory; keep its token cache out of the real home dir
    monkeypatch.setattr("app.routes.cli.paths.config_dir", lambda: tmp_path / "config")

    executor = await _build_executor(_args(["tools", "list", "--server", "http://from-flag:2"]))

    try:
        assert isinstance(executor, RemoteExecutor)
        assert executor.server_url == "http://from-flag:2/mcp"
    finally:
        await executor.close()


async def test_forgetful_server_setting_selects_remote(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "FORGETFUL_SERVER", "http://from-settings:1")
    monkeypatch.delenv("FORGETFUL_TOKEN", raising=False)
    monkeypatch.setattr("app.routes.cli.paths.config_dir", lambda: tmp_path / "config")

    executor = await _build_executor(_args(["tools", "list"]))

    try:
        assert isinstance(executor, RemoteExecutor)
        assert executor.server_url == "http://from-settings:1/mcp"
    finally:
        await executor.close()


async def test_local_flag_forces_local_even_with_server_configured(
    monkeypatch, sqlite_runtime_settings,
):
    monkeypatch.setattr(settings, "FORGETFUL_SERVER", "http://from-settings:1")

    executor = await _build_executor(_args(["tools", "list", "--local"]))

    try:
        assert isinstance(executor, LocalExecutor)
    finally:
        await executor.close()


async def test_default_is_local_mode(monkeypatch, sqlite_runtime_settings):
    monkeypatch.setattr(settings, "FORGETFUL_SERVER", "")
    monkeypatch.delenv("FORGETFUL_TOKEN", raising=False)

    executor = await _build_executor(_args(["tools", "list"]))

    try:
        assert isinstance(executor, LocalExecutor)
    finally:
        await executor.close()


async def test_forgetful_token_env_selects_bearer_auth(monkeypatch):
    monkeypatch.setattr(settings, "FORGETFUL_SERVER", "http://remote:8020")
    monkeypatch.setenv("FORGETFUL_TOKEN", "secret-token")

    executor = await _build_executor(_args(["tools", "list"]))

    try:
        assert isinstance(executor, RemoteExecutor)
        assert executor._token == "secret-token"
    finally:
        await executor.close()


# =============================================================================
# auth commands
# =============================================================================


def test_upsert_env_var_updates_only_target_line(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "EMBEDDING_PROVIDER=Ollama\n"
        "FORGETFUL_SERVER=http://old:1/mcp\n"
        "LOG_LEVEL=DEBUG\n",
    )

    auth_commands.upsert_env_var(env_file, "FORGETFUL_SERVER", "http://new:2/mcp")

    assert env_file.read_text().splitlines() == [
        "EMBEDDING_PROVIDER=Ollama",
        "FORGETFUL_SERVER=http://new:2/mcp",
        "LOG_LEVEL=DEBUG",
    ]


def test_upsert_env_var_appends_and_creates_file_when_missing(tmp_path):
    env_file = tmp_path / "config" / ".env"

    auth_commands.upsert_env_var(env_file, "FORGETFUL_SERVER", "http://new:2/mcp")

    assert env_file.read_text().splitlines() == ["FORGETFUL_SERVER=http://new:2/mcp"]


async def test_login_pings_server_and_saves_server_url(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("LOG_LEVEL=DEBUG\n")
    token_dir = tmp_path / "tokens"
    stub = StubClient()

    code = await auth_commands.login(
        "http://remote:8020",
        env_file=env_file,
        token_dir=token_dir,
        client_factory=lambda url, token_dir: stub,
    )

    assert code == 0
    assert stub.pinged
    assert env_file.read_text().splitlines() == [
        "LOG_LEVEL=DEBUG",
        "FORGETFUL_SERVER=http://remote:8020/mcp",
    ]


async def test_login_failure_exits_one_and_leaves_config_untouched(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("LOG_LEVEL=DEBUG\n")

    class FailingClient(StubClient):
        async def ping(self):
            raise ConnectionError("connection refused")

    code = await auth_commands.login(
        "http://remote:8020",
        env_file=env_file,
        token_dir=tmp_path / "tokens",
        client_factory=lambda url, token_dir: FailingClient(),
    )

    assert code == 1
    assert env_file.read_text().splitlines() == ["LOG_LEVEL=DEBUG"]
    assert "connection refused" in capsys.readouterr().err


def test_logout_deletes_token_cache_dir(tmp_path, capsys):
    token_dir = tmp_path / "tokens"
    (token_dir / "servers").mkdir(parents=True)
    (token_dir / "servers" / "token.json").write_text("{}")

    code = auth_commands.logout(token_dir=token_dir)

    assert code == 0
    assert not token_dir.exists()


def test_logout_when_no_cached_tokens_still_succeeds(tmp_path, capsys):
    code = auth_commands.logout(token_dir=tmp_path / "missing")

    assert code == 0


async def test_auth_status_local_mode_reports_local(monkeypatch, capsys):
    monkeypatch.setattr(settings, "FORGETFUL_SERVER", "")

    code = await auth_commands.status()

    assert code == 0
    out = capsys.readouterr().out
    assert "Mode: local" in out
    assert settings.DATABASE in out


class _RecordingExecutor:
    """Stands in for RemoteExecutor and records how it was constructed."""

    built = {}

    def __init__(self, url, *, token=None, client_factory=None):
        type(self).built = {"token": token, "client_factory": client_factory}
        self.server_url = url

    async def execute(self, tool_name, arguments):
        return {"name": "default-user-name"}

    async def close(self):
        pass


async def test_auth_status_no_credentials_verifies_without_touching_cache(
    monkeypatch, tmp_path, capsys,
):
    """No token + empty cache: status verifies via a plain (no-OAuth) client.

    The default OAuth client registers and writes to the token cache on connect, so
    using it for a read-only status check silently resurrects the cache `logout` just
    cleared (and could pop a browser). Status must instead go through a no-auth client.
    """
    monkeypatch.delenv("FORGETFUL_TOKEN", raising=False)
    empty_cache = tmp_path / "tokens"  # never created
    monkeypatch.setattr(auth_commands, "token_cache_dir", lambda: empty_cache)
    monkeypatch.setattr(
        "app.routes.cli.remote_executor.RemoteExecutor", _RecordingExecutor,
    )

    code = await auth_commands.status(server="http://remote:8020")

    assert code == 0
    # Verified through the no-auth path, NOT the default OAuth (cache-writing) factory.
    assert _RecordingExecutor.built["token"] is None
    assert _RecordingExecutor.built["client_factory"] is not None
    out = capsys.readouterr().out
    assert "User: default-user-name" in out
    assert "Cached credentials: no" in out
    assert not empty_cache.exists()  # status wrote nothing to disk


async def test_auth_status_with_cached_tokens_reuses_oauth_client(
    monkeypatch, tmp_path, capsys,
):
    """An existing cache means we're logged in: status reads it via the default OAuth
    client and must NOT downgrade to the no-auth client (which can't authenticate
    against a secured server)."""
    monkeypatch.delenv("FORGETFUL_TOKEN", raising=False)
    cache = tmp_path / "tokens"
    cache.mkdir()
    (cache / "token.json").write_text("{}")
    monkeypatch.setattr(auth_commands, "token_cache_dir", lambda: cache)
    monkeypatch.setattr(
        "app.routes.cli.remote_executor.RemoteExecutor", _RecordingExecutor,
    )

    code = await auth_commands.status(server="http://remote:8020")

    assert code == 0
    assert _RecordingExecutor.built["token"] is None
    assert _RecordingExecutor.built["client_factory"] is None  # default OAuth path
    out = capsys.readouterr().out
    assert "Cached credentials: yes" in out
