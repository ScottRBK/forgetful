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


async def test_server_flag_beats_forgetful_server_setting(monkeypatch):
    monkeypatch.setattr(settings, "FORGETFUL_SERVER", "http://from-settings:1")
    monkeypatch.delenv("FORGETFUL_TOKEN", raising=False)

    executor = await _build_executor(_args(["tools", "list", "--server", "http://from-flag:2"]))

    try:
        assert isinstance(executor, RemoteExecutor)
        assert executor.server_url == "http://from-flag:2/mcp"
    finally:
        await executor.close()


async def test_forgetful_server_setting_selects_remote(monkeypatch):
    monkeypatch.setattr(settings, "FORGETFUL_SERVER", "http://from-settings:1")
    monkeypatch.delenv("FORGETFUL_TOKEN", raising=False)

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
