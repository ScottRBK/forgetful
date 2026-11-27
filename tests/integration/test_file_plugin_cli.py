"""CLI passthrough for File Plugin warnings and before-handler errors."""

import json

from app.config.settings import settings
from app.routes.cli.parser import dispatch

PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg=="


def _args(**changes) -> dict:
    base = {
        "filename": "cli.png", "description": "CLI file",
        "data": PNG, "mime_type": "image/png", "tags": [],
    }
    base.update(changes)
    return base


def _call(tool: str, arguments: dict) -> int:
    """Run one local CLI call against the SQLite database in settings."""
    return dispatch(
        ["call", tool, "--args", json.dumps(arguments), "--local", "--json"],
        serve_runner=None, reembed_runner=None,
    )


def _prepare(monkeypatch, tmp_path, db_name: str) -> None:
    monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / db_name))
    monkeypatch.setattr(settings, "FILES_ENABLED", True)


def test_cli_create_surfaces_a_warning(file_plugin_runtime, monkeypatch, tmp_path, capsys):
    _prepare(monkeypatch, tmp_path, "file-cli-warn.db")

    code = _call("create_file", _args(tags=["warn"]))
    output = capsys.readouterr()

    assert code == 0
    payload = json.loads(output.out)
    assert payload["plugin_warnings"][0]["message"] == "Check the source."
    assert payload["plugin_warnings"][0]["code"] == "source"


def test_cli_create_rejection_is_an_error_not_a_silent_success(
    file_plugin_runtime, monkeypatch, tmp_path, capsys,
):
    _prepare(monkeypatch, tmp_path, "file-cli-reject.db")

    code = _call("create_file", _args(tags=["blocked"]))
    output = capsys.readouterr()

    assert code == 1
    assert "WRITE_PLUGIN_REJECTED: Remove the blocked tag." in output.err
    # Nothing is written, and no success payload is printed.
    assert output.out.strip() == ""


def test_cli_create_without_plugin_omits_warnings(
    sqlite_runtime_settings, monkeypatch, tmp_path, capsys,
):
    monkeypatch.setattr(settings, "FILE_WRITE_PLUGIN", "")
    _prepare(monkeypatch, tmp_path, "file-cli-plain.db")

    code = _call("create_file", _args(tags=["blocked"]))
    output = capsys.readouterr()

    assert code == 0
    assert "plugin_warnings" not in json.loads(output.out)


def test_cli_delete_surfaces_a_warning(file_plugin_runtime, monkeypatch, tmp_path, capsys):
    _prepare(monkeypatch, tmp_path, "file-cli-delete.db")

    assert _call(
        "create_file", _args(tags=["delete_warn"]),
    ) == 0
    created = json.loads(capsys.readouterr().out)

    code = _call("delete_file", {"file_id": created["id"]})
    output = capsys.readouterr()

    assert code == 0
    payload = json.loads(output.out)
    assert payload["success"] is True
    assert payload["plugin_warnings"][0]["message"] == "Check the source."


def test_cli_delete_rejection_is_an_error(file_plugin_runtime, monkeypatch, tmp_path, capsys):
    _prepare(monkeypatch, tmp_path, "file-cli-delete-reject.db")

    assert _call(
        "create_file", _args(tags=["delete_blocked"]),
    ) == 0
    created = json.loads(capsys.readouterr().out)

    code = _call("delete_file", {"file_id": created["id"]})
    output = capsys.readouterr()

    assert code == 1
    assert "WRITE_PLUGIN_REJECTED: Remove the blocked tag." in output.err


def test_cli_noop_update_reports_no_warnings(file_plugin_runtime, monkeypatch, tmp_path, capsys):
    _prepare(monkeypatch, tmp_path, "file-cli-noop.db")

    assert _call("create_file", _args()) == 0
    created = json.loads(capsys.readouterr().out)

    # Resend the stored description: a no-op PATCH must not run a handler.
    code = _call(
        "update_file", {"file_id": created["id"], "description": "CLI file"},
    )
    output = capsys.readouterr()

    assert code == 0
    assert "plugin_warnings" not in json.loads(output.out)
