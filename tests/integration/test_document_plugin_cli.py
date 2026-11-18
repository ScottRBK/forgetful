"""CLI passthrough for Document Plugin warnings."""

import json

from app.config.settings import settings
from app.routes.cli.parser import dispatch


def test_local_document_create_plugin_warnings(document_plugin_runtime, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "document-cli.db"))
    argv = [
        "call", "create_document", "--args",
        '{"title": "CLI Doc", "description": "Summary", "content": "Body", "tags": ["warn"]}',
        "--local", "--json",
    ]
    code = dispatch(argv, serve_runner=None, reembed_runner=None)
    output = capsys.readouterr()
    assert code == 0
    payload = json.loads(output.out)
    assert payload["plugin_warnings"][0]["message"] == "Check the source."
    argv_block = [
        "call", "create_document", "--args",
        '{"title": "CLI Blocked Doc", "description": "Summary", "content": "Body", "tags": ["blocked"]}',
        "--local", "--json",
    ]
    code = dispatch(argv_block, serve_runner=None, reembed_runner=None)
    output = capsys.readouterr()
    assert code == 1
    assert "WRITE_PLUGIN_REJECTED: Remove the blocked tag." in output.err


def test_local_document_create_without_plugin_has_no_warnings_in_json(
    sqlite_runtime_settings, monkeypatch, tmp_path, capsys,
):
    monkeypatch.setattr(settings, "DOCUMENT_WRITE_PLUGIN", "")
    monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "document-cli-plain.db"))
    code = dispatch(
        [
            "call", "create_document", "--args",
            '{"title": "Plain Doc", "description": "Summary", "content": "Body"}',
            "--local", "--json",
        ],
        serve_runner=None, reembed_runner=None,
    )
    output = capsys.readouterr()
    assert code == 0
    payload = json.loads(output.out)
    assert "plugin_warnings" not in payload
