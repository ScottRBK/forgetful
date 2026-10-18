"""Integration tests for argument validation in the CLI parser.

--batch-size must be a positive integer, so a bad value is rejected by argparse before
any re-embed work starts. Runners are replaced with recording fakes so no server or
re-embed actually starts.
"""
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

import main
from app.services.re_embedding_service import ReEmbeddingService


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
