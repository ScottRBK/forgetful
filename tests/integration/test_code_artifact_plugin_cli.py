"""CLI passthrough for Code Artifact Plugin warnings and before-handler errors."""

import json

from app.config.settings import settings
from app.routes.cli.parser import dispatch


def _args(**changes) -> dict:
    base = {
        "title": "CLI artifact",
        "description": "Artifact created through the CLI",
        "code": "def cli_helper():\n    return 1\n",
        "language": "python",
        "tags": [],
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


def test_cli_create_surfaces_a_warning(
    code_artifact_plugin_runtime, monkeypatch, tmp_path, capsys,
):
    _prepare(monkeypatch, tmp_path, "artifact-cli-warn.db")

    code = _call("create_code_artifact", _args(tags=["warn"]))
    output = capsys.readouterr()

    assert code == 0
    payload = json.loads(output.out)
    assert payload["plugin_warnings"][0]["message"] == "Check the source."
    assert payload["plugin_warnings"][0]["code"] == "source"


def test_cli_create_rejection_is_an_error_not_a_silent_success(
    code_artifact_plugin_runtime, monkeypatch, tmp_path, capsys,
):
    _prepare(monkeypatch, tmp_path, "artifact-cli-reject.db")

    code = _call("create_code_artifact", _args(tags=["blocked"]))
    output = capsys.readouterr()

    assert code == 1
    assert "WRITE_PLUGIN_REJECTED: Remove the blocked tag." in output.err
    assert output.out.strip() == ""


def test_cli_create_without_plugin_omits_warnings(
    sqlite_runtime_settings, monkeypatch, tmp_path, capsys,
):
    monkeypatch.setattr(settings, "CODE_ARTIFACT_WRITE_PLUGIN", "")
    _prepare(monkeypatch, tmp_path, "artifact-cli-plain.db")

    code = _call("create_code_artifact", _args(tags=["blocked"]))
    output = capsys.readouterr()

    assert code == 0
    assert "plugin_warnings" not in json.loads(output.out)


def test_cli_delete_surfaces_a_warning(
    code_artifact_plugin_runtime, monkeypatch, tmp_path, capsys,
):
    _prepare(monkeypatch, tmp_path, "artifact-cli-delete.db")

    assert _call("create_code_artifact", _args(tags=["delete_warn"])) == 0
    created = json.loads(capsys.readouterr().out)

    code = _call("delete_code_artifact", {"artifact_id": created["id"]})
    output = capsys.readouterr()

    assert code == 0
    payload = json.loads(output.out)
    assert payload["success"] is True
    assert payload["plugin_warnings"][0]["message"] == "Check the source."


def test_cli_delete_rejection_is_an_error(
    code_artifact_plugin_runtime, monkeypatch, tmp_path, capsys,
):
    _prepare(monkeypatch, tmp_path, "artifact-cli-delete-reject.db")

    assert _call("create_code_artifact", _args(tags=["delete_blocked"])) == 0
    created = json.loads(capsys.readouterr().out)

    code = _call("delete_code_artifact", {"artifact_id": created["id"]})
    output = capsys.readouterr()

    assert code == 1
    assert "WRITE_PLUGIN_REJECTED: Remove the blocked tag." in output.err


def test_cli_noop_update_reports_no_warnings(
    code_artifact_plugin_runtime, monkeypatch, tmp_path, capsys,
):
    _prepare(monkeypatch, tmp_path, "artifact-cli-noop.db")

    assert _call("create_code_artifact", _args()) == 0
    created = json.loads(capsys.readouterr().out)

    code = _call(
        "update_code_artifact",
        {"artifact_id": created["id"], "description": "Artifact created through the CLI"},
    )
    output = capsys.readouterr()

    assert code == 0
    assert "plugin_warnings" not in json.loads(output.out)
