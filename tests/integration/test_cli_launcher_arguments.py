"""Integration tests for argument validation in the CLI parser and legacy launcher.

Covers three argparse hardening rules: --batch-size must be a positive integer,
--dry-run/--batch-size are re-embed-only flags in the legacy launcher, and config
values interpolated into help text must not break argparse's %-expansion.
Runners are replaced with recording fakes so no server or re-embed actually starts.
"""
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

import main
from app.config.settings import settings
from app.routes.cli.parser import build_parser
from app.services.re_embedding_service import ReEmbeddingService

# Legitimate IPv6 link-local host with a zone id: contains a literal '%'.
ZONE_ID_HOST = "fe80::1%eth0"


@pytest.fixture
def recorded_runners(monkeypatch):
    calls = {"serve": [], "reembed": []}

    def fake_serve(transport, host, port):
        calls["serve"].append((transport, host, port))

    async def fake_reembed(args):
        calls["reembed"].append({"batch_size": args.batch_size, "dry_run": args.dry_run})

    monkeypatch.setattr(main, "_serve", fake_serve)
    monkeypatch.setattr(main, "_run_reembed", fake_reembed)
    return calls


def _invoke(monkeypatch, argv):
    monkeypatch.setattr(sys, "argv", ["forgetful", *argv])
    return main.cli()


@pytest.fixture
def percent_host(monkeypatch):
    monkeypatch.setattr(settings, "SERVER_HOST", ZONE_ID_HOST)
    return ZONE_ID_HOST


# --- --batch-size must be a positive integer ---------------------------------


@pytest.mark.parametrize("bad_value", ["0", "-5", "abc", "1.5"])
@pytest.mark.parametrize(
    "argv_prefix",
    [["re-embed"], ["--re-embed"]],
    ids=["subcommand", "legacy-flag"],
)
def test_non_positive_batch_size_is_rejected_before_any_runner(
    monkeypatch, recorded_runners, capsys, argv_prefix, bad_value,
):
    with pytest.raises(SystemExit) as excinfo:
        _invoke(monkeypatch, [*argv_prefix, f"--batch-size={bad_value}"])

    assert excinfo.value.code == 2
    assert recorded_runners == {"serve": [], "reembed": []}
    assert "--batch-size" in capsys.readouterr().err


@pytest.mark.parametrize(
    "argv_prefix",
    [["re-embed"], ["--re-embed"]],
    ids=["subcommand", "legacy-flag"],
)
def test_positive_batch_size_is_still_accepted(monkeypatch, recorded_runners, argv_prefix):
    _invoke(monkeypatch, [*argv_prefix, "--batch-size", "1"])

    assert recorded_runners["reembed"] == [{"batch_size": 1, "dry_run": False}]


def test_re_embedding_service_rejects_non_positive_batch_size():
    for bad_value in (0, -3):
        with pytest.raises(ValueError, match="batch_size"):
            ReEmbeddingService(MagicMock(), AsyncMock(), batch_size=bad_value)


# --- legacy launcher: re-embed-only flags need --re-embed --------------------


@pytest.mark.parametrize(
    "argv",
    [
        ["--dry-run"],
        ["--batch-size", "5"],
        ["--transport", "http", "--dry-run"],
        ["--dry-run", "--batch-size", "5"],
    ],
    ids=["dry-run", "batch-size", "http-dry-run", "both"],
)
def test_legacy_reembed_only_flags_without_reembed_are_rejected(
    monkeypatch, recorded_runners, capsys, argv,
):
    with pytest.raises(SystemExit) as excinfo:
        _invoke(monkeypatch, argv)

    assert excinfo.value.code == 2
    assert recorded_runners == {"serve": [], "reembed": []}
    assert "--re-embed" in capsys.readouterr().err


def test_legacy_reembed_flags_with_reembed_still_route_to_reembed_runner(
    monkeypatch, recorded_runners,
):
    _invoke(monkeypatch, ["--re-embed", "--dry-run", "--batch-size", "7"])

    assert recorded_runners["reembed"] == [{"batch_size": 7, "dry_run": True}]
    assert recorded_runners["serve"] == []


def test_legacy_reembed_without_batch_size_keeps_default_of_twenty(
    monkeypatch, recorded_runners,
):
    _invoke(monkeypatch, ["--re-embed"])

    assert recorded_runners["reembed"] == [{"batch_size": 20, "dry_run": False}]


def test_legacy_bare_and_transport_flags_still_start_the_server(monkeypatch, recorded_runners):
    _invoke(monkeypatch, [])
    _invoke(monkeypatch, ["--transport", "http", "--port", "9000"])

    assert recorded_runners["serve"] == [
        ("stdio", settings.SERVER_HOST, settings.SERVER_PORT),
        ("http", settings.SERVER_HOST, 9000),
    ]
    assert recorded_runners["reembed"] == []


# --- '%' in config-derived help text -----------------------------------------


def test_serve_subcommand_help_renders_host_with_percent(percent_host):
    parser = build_parser()  # Python 3.14 validates help strings right here
    serve = parser._subparsers._group_actions[0].choices["serve"]

    assert percent_host in serve.format_help()
    assert parser.parse_args(["serve"]).host == percent_host


def test_legacy_launcher_help_renders_host_with_percent(
    monkeypatch, recorded_runners, percent_host, capsys,
):
    with pytest.raises(SystemExit) as excinfo:
        _invoke(monkeypatch, ["--help"])

    assert excinfo.value.code == 0
    assert percent_host in capsys.readouterr().out


def test_legacy_launcher_still_serves_with_percent_host(
    monkeypatch, recorded_runners, percent_host,
):
    _invoke(monkeypatch, ["--transport", "http"])

    assert recorded_runners["serve"] == [("http", percent_host, settings.SERVER_PORT)]


@pytest.mark.parametrize("argv", [["--version"], ["tools", "list", "--help"]])
def test_other_commands_survive_percent_host(monkeypatch, recorded_runners, percent_host, argv):
    # dispatch() builds the whole parser tree; the legacy launcher builds its own.
    with pytest.raises(SystemExit) as excinfo:
        _invoke(monkeypatch, argv)

    assert excinfo.value.code == 0
