"""CLI parser/execution/output with production runtime and persistent temporary SQLite."""

import json

import pytest
from test_write_plugin_runtime import plugin_runtime as plugin_runtime

from app.config.settings import settings
from app.routes.cli.parser import dispatch


@pytest.mark.parametrize("content", ["allow", "warn", "blocked"])
@pytest.mark.parametrize("as_json", [False, True])
def test_local_save_exit_output_and_persistence(
    plugin_runtime, monkeypatch, tmp_path, capsys, content, as_json,
):
    monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "cli.db"))
    argv = ["memory", "save", content, "--title", "CLI test", "--local"]
    if as_json:
        argv.append("--json")
    code = dispatch(argv, serve_runner=None, reembed_runner=None)
    output = capsys.readouterr()
    assert code == (1 if content == "blocked" else 0)
    if as_json:
        payload = json.loads(
            output.err.splitlines()[-1] if content == "blocked" else output.out,
        )
        if content == "warn":
            assert payload["plugin_warnings"][0]["message"] == "Check the source."
        elif content == "allow":
            assert "plugin_warnings" not in payload
        else:
            assert "WRITE_PLUGIN_REJECTED" in str(payload)
    else:
        if content == "warn":
            assert "Created memory" in output.out
            assert "Warning: Check the source." in output.out
        elif content == "allow":
            assert "Created memory" in output.out
            assert "Warning:" not in output.out
        else:
            assert "WRITE_PLUGIN_REJECTED: Remove the blocked tag." in output.err
    assert dispatch(
        ["memory", "recent", "--local", "--json"], serve_runner=None, reembed_runner=None,
    ) == 0
    listing = json.loads(capsys.readouterr().out)
    assert listing["total_count"] == (0 if content == "blocked" else 1)


@pytest.mark.parametrize("operation,tool", [
    ("obsolete", "mark_memory_obsolete"), ("restore", "unobsolete_memory"),
])
def test_local_lifecycle_warning_error_and_success_shapes(
    plugin_runtime, monkeypatch, tmp_path, capsys, operation, tool,
):
    from test_write_plugin_runtime import data

    monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "lifecycle.db"))

    def call(name, arguments):
        code = dispatch(
            ["call", name, "--args", json.dumps(arguments), "--local", "--json"],
            serve_runner=None, reembed_runner=None,
        )
        output = capsys.readouterr()
        return code, json.loads(output.err.splitlines()[-1] if code else output.out)

    for marker in ("plain", "warn", "blocked", "error", "post_error"):
        tag = "post_error" if marker == "post_error" else f"{operation}_{marker}"
        code, created = call("create_memory", data([tag]).model_dump(exclude_unset=True))
        assert code == 0
        mid = created["id"]
        if operation == "restore":
            assert call("mark_memory_obsolete", {"memory_id": mid, "reason": "Old fact"})[0] == 0
        args = {"memory_id": mid}
        if operation == "obsolete":
            args["reason"] = "Old fact"

        code, payload = call(tool, args)

        assert code == (1 if marker in ("blocked", "error") else 0)
        if marker == "plain":
            assert payload == {"success": True}
        elif marker in ("warn", "post_error"):
            assert payload["success"] is True
            assert payload["plugin_warnings"][0]["outcome"] == "warn"
        else:
            expected = (
                "WRITE_PLUGIN_REJECTED" if marker == "blocked" else "WRITE_PLUGIN_UNAVAILABLE"
            )
            assert expected in str(payload)
        _, saved = call("get_memory", {"memory_id": mid})
        assert saved["is_obsolete"] is ((operation == "obsolete") == (code == 0))
