"""E2E tests for CLI auth status / token handling against the real in-process server.

Reuses the file-backed SQLite server fixtures of the CLI remote suite and drives
main.cli() end to end: FORGETFUL_TOKEN hygiene, `auth status` under a category-only
scope ceiling, and a token cache that was moved after login.
"""

import pytest

from app.config.settings import settings
from tests.e2e_sqlite.test_cli_remote import cli_remote_env as cli_remote_env
from tests.e2e_sqlite.test_cli_remote import http_server_url as http_server_url
from tests.e2e_sqlite.test_cli_remote import invoke_cli

SECRET = "s3cr3t-token-VALUE-123"


@pytest.fixture
def category_scoped_server_url(cli_remote_env, request):
    """The real server with a scope ceiling that excludes the `users` category."""
    cli_remote_env.FORGETFUL_SCOPES = "read:memories,write:memories"
    return request.getfixturevalue("http_server_url")


# -- FORGETFUL_TOKEN hygiene ---------------------------------------------------


def test_tools_list_accepts_token_with_trailing_newline(http_server_url, monkeypatch, capsys):
    monkeypatch.setenv("FORGETFUL_TOKEN", f"{SECRET}\n")

    code, _, err = invoke_cli(monkeypatch, capsys, ["tools", "list", "--server", http_server_url])

    assert code == 0, err
    assert SECRET not in err


def test_malformed_token_is_rejected_without_echoing_it(http_server_url, monkeypatch, capsys):
    monkeypatch.setenv("FORGETFUL_TOKEN", f"{SECRET}\nsecond-line")

    code, out, err = invoke_cli(monkeypatch, capsys, ["tools", "list", "--server", http_server_url])

    assert code == 1
    assert "FORGETFUL_TOKEN" in err
    assert SECRET not in out + err


def test_auth_status_with_trailing_newline_token_authenticates(
    http_server_url, monkeypatch, capsys,
):
    monkeypatch.setattr(settings, "FORGETFUL_SERVER", http_server_url)
    monkeypatch.setenv("FORGETFUL_TOKEN", f"{SECRET}\n")

    code, out, err = invoke_cli(monkeypatch, capsys, ["auth", "status"])

    assert code == 0, err
    assert "User:" in out
    assert SECRET not in out + err
