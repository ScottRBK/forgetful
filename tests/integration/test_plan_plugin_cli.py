"""Real CLI parser, local executor and HTTP MCP remote executor contracts."""

import json
import os
import subprocess
import sys

import pytest
from plan_plugin_helpers import loopback_plan_server, plan_app
from plan_plugin_helpers import plan_runtime as plan_runtime

from app.routes.cli.parser import dispatch


def cli_call(capsys, tool_name, arguments, *, server=None):
    argv = ["call", tool_name, "--args", json.dumps(arguments), "--json"]
    argv.extend(["--server", server] if server else ["--local"])
    code = dispatch(argv, serve_runner=None, reembed_runner=None)
    captured = capsys.readouterr()
    if code:
        errors = []
        for line in captured.err.splitlines():
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict) and set(value) == {"error"}:
                errors.append(value)
        assert len(errors) == 1, captured.err
        payload = errors[0]
    else:
        payload = json.loads(captured.out)
    return code, payload


def check_payload(code, payload, marker):
    assert code == (1 if marker in ("blocked", "error") else 0)
    if marker == "warn":
        assert payload["plugin_warnings"][0]["code"] == "PLAN_POLICY"
    elif marker == "plain":
        assert "plugin_warnings" not in payload
    else:
        assert ("PLAN_PLUGIN_REJECTED" if marker == "blocked" else "PLAN_PLUGIN_UNAVAILABLE") in str(payload)
        assert "SYNTHETIC_PRIVATE_ERROR" not in str(payload)


@pytest.mark.parametrize("marker", ["plain", "warn", "blocked", "error"])
def test_local_cli_plan_policy(plan_runtime, capsys, marker):
    code, project = cli_call(capsys, "create_project", {
        "name": "Local CLI plan", "description": "Real local parser", "project_type": "development",
    })
    assert code == 0
    code, payload = cli_call(capsys, "create_plan", {"project_id": project["id"], "title": marker})
    check_payload(code, payload, marker)
    if code == 0:
        read_code, read = cli_call(capsys, "get_plan", {"plan_id": payload["id"]})
        assert read_code == 0 and "plugin_warnings" not in read


def remote_cli_call(server, home, tool_name, arguments):
    """Run the real CLI in its own bounded process; never abandon a worker thread."""
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home),
               XDG_CONFIG_HOME=str(home / "config"))
    completed = subprocess.run(  # noqa: S603 - test-controlled arguments, no shell
        [sys.executable, "-c", "import faulthandler; faulthandler.dump_traceback_later(20); from main import cli; raise SystemExit(cli())",
         "call", tool_name, "--args", json.dumps(arguments), "--json", "--server", server],
        capture_output=True, text=True, encoding="utf-8", timeout=30, env=env, check=False,
    )
    if completed.returncode:
        errors = []
        for line in completed.stderr.splitlines():
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict) and set(value) == {"error"}:
                errors.append(value)
        assert len(errors) == 1, completed.stderr
        payload = errors[0]
    else:
        payload = json.loads(completed.stdout)
    return completed.returncode, payload


@pytest.mark.parametrize("marker", ["plain", "warn", "blocked", "error"])
def test_remote_cli_plan_policy_over_actual_http(plan_runtime, monkeypatch, tmp_path, marker):
    monkeypatch.setenv("FORGETFUL_TOKEN", "synthetic-test-only-not-a-credential")
    home = tmp_path / "remote-cli-home"
    home.mkdir()
    with loopback_plan_server(plan_app()) as server:
        code, project = remote_cli_call(server, home, "create_project", {
            "name": "Remote CLI plan", "description": "Actual loopback HTTP MCP", "project_type": "development",
        })
        assert code == 0
        code, payload = remote_cli_call(server, home, "create_plan", {
            "project_id": project["id"], "title": marker,
        })
        check_payload(code, payload, marker)
        if code == 0:
            read_code, read = remote_cli_call(server, home, "get_plan", {"plan_id": payload["id"]})
            assert read_code == 0 and "plugin_warnings" not in read
