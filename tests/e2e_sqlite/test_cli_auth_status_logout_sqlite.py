"""E2E tests for CLI auth status / token handling against the real in-process server.

Reuses the file-backed SQLite server fixtures of the CLI remote suite and drives
main.cli() end to end: FORGETFUL_TOKEN hygiene, `auth status` under a category-only
scope ceiling, and a token cache that was moved after login.
"""
import asyncio
import shutil
from pathlib import Path

import pytest

from app.config.settings import settings
from app.routes.cli import paths
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


# -- auth status under a category-only scope ceiling ---------------------------


def test_auth_status_is_authenticated_when_user_lookup_is_out_of_scope(
    category_scoped_server_url, monkeypatch, capsys,
):
    url = category_scoped_server_url

    # Control: the connection and credentials are fine, a permitted command works
    code, out, err = invoke_cli(
        monkeypatch, capsys, ["memory", "save", "x", "--title", "S", "--server", url],
    )
    assert code == 0, f"{out!r} {err!r}"

    monkeypatch.setattr(settings, "FORGETFUL_SERVER", url)
    code, out, err = invoke_cli(monkeypatch, capsys, ["auth", "status"])

    assert code == 0, f"exit={code} out={out!r} err={err!r}"
    assert f"Server: {url}" in out
    assert "outside the granted scopes" in out
    assert "not authenticated" not in err


def test_auth_status_still_shows_user_when_in_scope(http_server_url, monkeypatch, capsys):
    monkeypatch.setattr(settings, "FORGETFUL_SERVER", http_server_url)

    code, out, err = invoke_cli(monkeypatch, capsys, ["auth", "status"])

    assert code == 0, err
    assert "User:" in out
    assert "outside the granted scopes" not in out


# -- token cache moved after login --------------------------------------------


async def _seed_then_relocate(tmp_path: Path, url: str) -> None:
    """Log in (seed a token) under one directory, then move it to the live cache dir."""
    from fastmcp.client.auth import OAuth
    from mcp.shared.auth import OAuthToken

    from app.routes.cli.token_storage import oauth_token_file_tree_store

    old = tmp_path / "old_home" / "tokens"
    old.mkdir(parents=True)
    adapter = OAuth(
        mcp_url=url, token_storage=oauth_token_file_tree_store(old),
    ).token_storage_adapter
    await adapter.set_tokens(OAuthToken(access_token="seeded", token_type="Bearer"))

    new = paths.token_cache_dir()
    new.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(old), str(new))


def test_remote_command_survives_relocated_token_cache(
    http_server_url, tmp_path, monkeypatch, capsys,
):
    asyncio.run(_seed_then_relocate(tmp_path, http_server_url))

    code, out, err = invoke_cli(
        monkeypatch, capsys, ["project", "list", "--json", "--server", http_server_url],
    )

    assert code == 0, err
    assert "resolves outside the allowed directory" not in err


def test_auth_status_survives_relocated_token_cache(
    http_server_url, tmp_path, monkeypatch, capsys,
):
    asyncio.run(_seed_then_relocate(tmp_path, http_server_url))
    monkeypatch.setattr(settings, "FORGETFUL_SERVER", http_server_url)

    code, out, err = invoke_cli(monkeypatch, capsys, ["auth", "status"])

    assert code == 0, err
    assert "Cached credentials: yes" in out
    assert "Traceback" not in err


def test_auth_login_survives_relocated_token_cache(
    http_server_url, tmp_path, monkeypatch, capsys,
):
    asyncio.run(_seed_then_relocate(tmp_path, http_server_url))

    code, out, err = invoke_cli(
        monkeypatch, capsys, ["auth", "login", "--server", http_server_url],
    )

    assert code == 0, err
    assert f"Logged in to {http_server_url}" in out
