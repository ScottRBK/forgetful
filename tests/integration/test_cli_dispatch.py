"""Integration tests for CLI dispatch (docs/dev/cli_plan.md phase 2)

main.cli() must keep every documented legacy invocation working (bare -> stdio server,
--transport/--re-embed/--version flags) while routing the new subcommand spellings
(serve, re-embed) to the same runners. Runners are replaced with recording fakes so no
server or re-embed actually starts.
"""
import sys

import pytest

import main
from app.config.settings import settings
from app.version import get_version


@pytest.fixture
def recorded_runners(monkeypatch):
    """Replace the serve/re-embed runner seams with recording fakes."""
    calls = {}

    def fake_serve(transport, host, port):
        calls["serve"] = {"transport": transport, "host": host, "port": port}

    async def fake_reembed(args):
        calls["reembed"] = {"batch_size": args.batch_size, "dry_run": args.dry_run}

    monkeypatch.setattr(main, "_serve", fake_serve)
    monkeypatch.setattr(main, "_run_reembed", fake_reembed)
    return calls


def _invoke(monkeypatch, argv):
    monkeypatch.setattr(sys, "argv", ["forgetful", *argv])
    return main.cli()


def test_bare_invocation_boots_stdio_server(monkeypatch, recorded_runners):
    _invoke(monkeypatch, [])

    assert recorded_runners["serve"] == {
        "transport": "stdio",
        "host": settings.SERVER_HOST,
        "port": settings.SERVER_PORT,
    }


def test_legacy_http_flags_route_to_serve_runner(monkeypatch, recorded_runners):
    _invoke(monkeypatch, ["--transport", "http", "--port", "9000"])

    assert recorded_runners["serve"]["transport"] == "http"
    assert recorded_runners["serve"]["port"] == 9000


def test_serve_subcommand_routes_to_same_runner(monkeypatch, recorded_runners):
    _invoke(monkeypatch, ["serve", "--transport", "http"])

    assert recorded_runners["serve"]["transport"] == "http"
    assert recorded_runners["serve"]["port"] == settings.SERVER_PORT


def test_legacy_re_embed_flag_routes_to_reembed_runner(monkeypatch, recorded_runners):
    _invoke(monkeypatch, ["--re-embed", "--dry-run"])

    assert recorded_runners["reembed"] == {"batch_size": 20, "dry_run": True}
    assert "serve" not in recorded_runners


def test_re_embed_subcommand_routes_to_reembed_runner(monkeypatch, recorded_runners):
    _invoke(monkeypatch, ["re-embed", "--dry-run"])

    assert recorded_runners["reembed"] == {"batch_size": 20, "dry_run": True}
    assert "serve" not in recorded_runners


def test_re_embed_subcommand_accepts_batch_size(monkeypatch, recorded_runners):
    _invoke(monkeypatch, ["re-embed", "--batch-size", "5"])

    assert recorded_runners["reembed"] == {"batch_size": 5, "dry_run": False}


def test_version_flag_prints_version_and_exits_zero(monkeypatch, recorded_runners, capsys):
    with pytest.raises(SystemExit) as excinfo:
        _invoke(monkeypatch, ["--version"])

    assert excinfo.value.code == 0
    assert get_version() in capsys.readouterr().out


def test_unknown_token_exits_with_usage_error(monkeypatch, recorded_runners, capsys):
    with pytest.raises(SystemExit) as excinfo:
        _invoke(monkeypatch, ["frobnicate"])

    assert excinfo.value.code == 2
    assert not recorded_runners
