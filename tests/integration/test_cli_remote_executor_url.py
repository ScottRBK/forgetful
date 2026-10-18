"""Integration tests for CLI server URL normalisation and credential redaction.

Covers regressions around the remote CLI server URL:

* an upper-case ``HTTP://`` / ``HTTPS://`` scheme passed validation but fastmcp could not
  infer a transport from it;
* ``/mcp`` was appended to the raw string, so URLs with a query or fragment grew a
  doubled mount path every time they were normalised again;
* credentials embedded in the server URL were echoed by ``auth login`` / ``auth status``
  and persisted into the user env file.

The fastmcp client is stubbed through the client-factory seam where one is needed.
"""

from urllib.parse import urlsplit

import pytest

from app.config.settings import settings
from app.routes.cli import auth_commands, remote_executor
from app.routes.cli.parser import _run_auth_command, _run_tool_command, build_parser
from app.routes.cli.remote_executor import RemoteExecutor, normalize_server_url
from app.routes.cli.render import emit_error, redact_urls_in_text
from app.utils.url_helpers import redact_url

SECRET = "s3cretPassw0rd"
USER = "alice"
URL_WITH_SECRET = f"http://{USER}:{SECRET}@127.0.0.1:18765"


def _args(argv):
    return build_parser().parse_args(argv)


class StubResult:
    def __init__(self, data):
        self.data = data
        self.is_error = False


class StubClient:
    """Stands in for fastmcp.Client; optionally fails with a message naming the URL."""

    def __init__(self, error=None, data=None):
        self._error = error
        self._data = data if data is not None else {"name": "carol"}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def ping(self):
        if self._error:
            raise self._error

    async def call_tool(self, name, arguments):
        if self._error:
            raise self._error
        return StubResult(self._data)

    async def close(self):
        return None


# =============================================================================
# Scheme normalisation
# =============================================================================
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("HTTP://localhost:8020", "http://localhost:8020/mcp"),
        ("HTTPS://example.com", "https://example.com/mcp"),
        ("Http://localhost:8020", "http://localhost:8020/mcp"),
        ("HTTPS://Example.com/custom", "https://Example.com/custom"),
    ],
)
def test_normalize_lowercases_the_scheme(raw, expected):
    assert normalize_server_url(raw) == expected


@pytest.mark.parametrize("raw", ["HTTP://localhost:8020", "HTTPS://example.com"])
def test_remote_executor_builds_a_real_client_for_an_uppercase_scheme(raw):
    # Default factory -> real fastmcp.Client; transport inference happens at construction.
    executor = RemoteExecutor(raw, token="t")

    assert executor.server_url == normalize_server_url(raw)
    assert urlsplit(executor.server_url).scheme in {"http", "https"}


# =============================================================================
# Mount path handling: only the path component is edited
# =============================================================================
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://host.example.com/?key=abc", "https://host.example.com/mcp?key=abc"),
        ("https://host.example.com?x=1", "https://host.example.com/mcp?x=1"),
        ("https://host.example.com/#frag", "https://host.example.com/mcp#frag"),
        ("https://host.example.com?x=1#frag", "https://host.example.com/mcp?x=1#frag"),
        ("host.example.com:8020?x=1", "https://host.example.com:8020/mcp?x=1"),
        ("localhost:8020/?x=1", "http://localhost:8020/mcp?x=1"),
        # An explicit path is kept (minus a trailing slash), query intact.
        ("https://host.example.com/custom/?x=1", "https://host.example.com/custom?x=1"),
        ("https://host.example.com/custom/", "https://host.example.com/custom"),
    ],
)
def test_mount_path_lands_in_the_path_not_the_query_or_fragment(raw, expected):
    assert normalize_server_url(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "https://host.example.com/?key=abc",
        "https://host.example.com?x=1",
        "https://host.example.com/#frag",
        "HTTPS://host.example.com",
        "localhost:8020",
        "https://host.example.com/custom/",
        f"http://{USER}:{SECRET}@host.example.com:8020",
    ],
)
def test_normalize_is_idempotent(raw):
    once = normalize_server_url(raw)

    assert normalize_server_url(once) == once


def test_stored_url_is_not_grown_by_renormalising_in_remote_executor():
    # auth login stores the normalised URL; every later command normalises it again.
    stored = normalize_server_url("https://host.example.com/?key=abc")
    seen = {}

    def factory(url, token):
        seen["url"] = url
        return StubClient()

    RemoteExecutor(stored, token="t", client_factory=factory)

    assert seen["url"] == stored
    assert urlsplit(stored).path == "/mcp"


# =============================================================================
# Credentials embedded in the server URL
# =============================================================================
@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (URL_WITH_SECRET, "http://***:***@127.0.0.1:18765"),
        (f"https://{SECRET}@host/mcp", "https://***:***@host/mcp"),
        ("http://localhost:8020/mcp", "http://localhost:8020/mcp"),
    ],
)
def test_redact_url_masks_userinfo_only(url, expected):
    assert redact_url(url) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            f"Client error '401 Unauthorized' for url '{URL_WITH_SECRET}/mcp'",
            "Client error '401 Unauthorized' for url 'http://***:***@127.0.0.1:18765/mcp'",
        ),
        (
            f"redirected from {URL_WITH_SECRET}/a to https://{SECRET}@other/b",
            "redirected from http://***:***@127.0.0.1:18765/a to https://***:***@other/b",
        ),
        ("mail me at bob@example.com (no URL)", "mail me at bob@example.com (no URL)"),
        ("plain http://host:8020/mcp?e=a@b", "plain http://host:8020/mcp?e=a@b"),
        ("", ""),
    ],
)
def test_redact_urls_in_text_masks_every_embedded_userinfo(text, expected):
    assert redact_urls_in_text(text) == expected


@pytest.mark.parametrize("as_json", [False, True])
def test_emit_error_redacts_url_credentials(as_json, capsys):
    emit_error(f"failed for {URL_WITH_SECRET}/mcp", as_json)

    err = capsys.readouterr().err
    assert SECRET not in err
    assert USER not in err
    assert "127.0.0.1:18765/mcp" in err


def test_unsupported_scheme_error_does_not_echo_credentials():
    with pytest.raises(ValueError, match="Unsupported server URL scheme") as excinfo:
        normalize_server_url(f"ftp://{USER}:{SECRET}@example.com")

    assert SECRET not in str(excinfo.value)
    assert USER not in str(excinfo.value)


async def test_login_neither_persists_nor_echoes_url_credentials(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("LOG_LEVEL=DEBUG\n")
    seen = []

    def factory(url, token_dir):
        seen.append(url)
        return StubClient()

    code = await auth_commands.login(
        URL_WITH_SECRET,
        env_file=env_file,
        token_dir=tmp_path / "tokens",
        client_factory=factory,
    )

    assert code == 0
    out = capsys.readouterr()
    assert SECRET not in out.out + out.err
    assert USER not in out.out + out.err
    assert "Logged in to http://127.0.0.1:18765/mcp" in out.out
    assert SECRET not in env_file.read_text()
    assert env_file.read_text().splitlines() == [
        "LOG_LEVEL=DEBUG",
        "FORGETFUL_SERVER=http://127.0.0.1:18765/mcp",
    ]
    # The OAuth client (and so the token cache key) uses the same credential-free URL
    # that is persisted, so later commands find the cached tokens again.
    assert seen == ["http://127.0.0.1:18765/mcp"]
    assert "FORGETFUL_TOKEN" in out.err  # tells the user where credentials belong


async def test_login_without_credentials_prints_no_credentials_notice(tmp_path, capsys):
    code = await auth_commands.login(
        "http://remote:8020",
        env_file=tmp_path / ".env",
        token_dir=tmp_path / "tokens",
        client_factory=lambda url, token_dir: StubClient(),
    )

    assert code == 0
    assert capsys.readouterr().err == ""


async def test_login_failure_message_does_not_echo_credentials(tmp_path, capsys):
    env_file = tmp_path / ".env"
    failing = StubClient(error=RuntimeError("unauthorized for http://remote:8020/mcp"))

    code = await auth_commands.login(
        f"http://{USER}:{SECRET}@remote:8020",
        env_file=env_file,
        token_dir=tmp_path / "tokens",
        client_factory=lambda url, token_dir: failing,
    )

    assert code == 1
    err = capsys.readouterr().err
    assert SECRET not in err
    assert not env_file.exists()


@pytest.fixture
def status_env(monkeypatch, tmp_path):
    monkeypatch.setattr(auth_commands, "token_cache_dir", lambda: tmp_path / "tokens")
    monkeypatch.setattr(settings, "FORGETFUL_SERVER", URL_WITH_SECRET)
    monkeypatch.delenv("FORGETFUL_TOKEN", raising=False)


async def test_status_redacts_url_credentials(status_env, monkeypatch, capsys):
    seen = []

    def factory(url, _token=None):
        seen.append(url)
        return StubClient()

    monkeypatch.setattr(auth_commands, "_plain_client_factory", factory)

    code = await _run_auth_command(_args(["auth", "status"]))

    assert code == 0
    out = capsys.readouterr()
    assert SECRET not in out.out + out.err
    assert USER not in out.out + out.err
    assert "Server: http://***:***@127.0.0.1:18765/mcp" in out.out
    # Connection behaviour is unchanged: only what is shown is masked.
    assert seen == [f"{URL_WITH_SECRET}/mcp"]


async def test_status_error_path_redacts_url_credentials(status_env, monkeypatch, capsys):
    error = RuntimeError(f"Client error '401 Unauthorized' for url '{URL_WITH_SECRET}/mcp'")
    monkeypatch.setattr(
        auth_commands, "_plain_client_factory", lambda url, _t=None: StubClient(error=error),
    )

    code = await _run_auth_command(_args(["auth", "status"]))

    assert code == 1
    err = capsys.readouterr().err
    assert SECRET not in err
    assert USER not in err
    assert "Server: http://***:***@127.0.0.1:18765/mcp" in err
    assert "401 Unauthorized" in err


@pytest.mark.parametrize("extra", [[], ["--json"]])
async def test_tool_command_error_does_not_echo_url_credentials(
    extra, monkeypatch, capsys,
):
    monkeypatch.delenv("FORGETFUL_TOKEN", raising=False)
    monkeypatch.setattr(
        remote_executor,
        "_default_client_factory",
        lambda url, token: StubClient(
            error=RuntimeError(f"Client error '401 Unauthorized' for url '{url}'"),
        ),
    )

    code = await _run_tool_command(
        _args(["tools", "list", "--server", URL_WITH_SECRET, *extra]),
    )

    assert code == 1
    err = capsys.readouterr().err
    assert "401 Unauthorized" in err
    assert SECRET not in err
    assert USER not in err
