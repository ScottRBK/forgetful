"""CLI passthrough for Entity Plugin warnings."""

import json

from app.config.settings import settings
from app.routes.cli.parser import dispatch


def test_local_entity_create_plugin_warnings(entity_plugin_runtime, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "entity-cli.db"))
    argv = [
        "call", "create_entity", "--args",
        '{"name": "CLI Org", "entity_type": "Organization", "tags": ["warn"]}',
        "--local", "--json",
    ]
    code = dispatch(argv, serve_runner=None, reembed_runner=None)
    output = capsys.readouterr()
    assert code == 0
    payload = json.loads(output.out)
    assert payload["plugin_warnings"][0]["message"] == "Check the source."
    argv_block = [
        "call", "create_entity", "--args",
        '{"name": "CLI Blocked", "entity_type": "Organization", "tags": ["blocked"]}',
        "--local", "--json",
    ]
    code = dispatch(argv_block, serve_runner=None, reembed_runner=None)
    output = capsys.readouterr()
    assert code == 1
    assert "WRITE_PLUGIN_REJECTED: Remove the blocked tag." in output.err


def test_local_entity_create_without_plugin_has_no_warnings_in_json(
    sqlite_runtime_settings, monkeypatch, tmp_path, capsys,
):
    monkeypatch.setattr(settings, "ENTITY_WRITE_PLUGIN", "")
    monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "entity-cli-plain.db"))
    code = dispatch(
        [
            "call", "create_entity", "--args",
            '{"name": "Plain Org", "entity_type": "Organization"}',
            "--local", "--json",
        ],
        serve_runner=None, reembed_runner=None,
    )
    output = capsys.readouterr()
    assert code == 0
    payload = json.loads(output.out)
    assert "plugin_warnings" not in payload
