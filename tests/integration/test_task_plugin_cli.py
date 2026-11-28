"""CLI passthrough for Task Plugin warnings and before-handler errors.

Task deletion has no MCP tool, so there is no CLI path for it; its warnings and
rejections surface on REST only. That gap is documented rather than papered over
with an invented tool.
"""

import json

from app.config.settings import settings
from app.routes.cli.parser import dispatch


def _call(tool: str, arguments: dict) -> int:
    return dispatch(
        ["call", tool, "--args", json.dumps(arguments), "--local", "--json"],
        serve_runner=None, reembed_runner=None,
    )


def _prepare(monkeypatch, tmp_path, db_name: str) -> None:
    monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / db_name))
    monkeypatch.setattr(settings, "PLANNING_ENABLED", True)


def _create_plan(capsys) -> int:
    """Create a project, then an active plan inside it, then return the plan id."""
    assert _call("create_project", {
        "name": "CLI project", "description": "Scope for task plugin tests",
        "project_type": "development",
    }) == 0
    project = json.loads(capsys.readouterr().out)

    assert _call("create_plan", {
        "title": "CLI plan", "goal": "Ship the thing", "project_id": project["id"],
    }) == 0
    plan = json.loads(capsys.readouterr().out)

    assert _call("update_plan", {"plan_id": plan["id"], "status": "active"}) == 0
    capsys.readouterr()
    return plan["id"]


def test_cli_create_surfaces_a_warning(task_plugin_runtime, monkeypatch, tmp_path, capsys):
    _prepare(monkeypatch, tmp_path, "task-cli-warn.db")
    plan_id = _create_plan(capsys)

    code = _call("create_task", {"plan_id": plan_id, "title": "warn task"})
    output = capsys.readouterr()

    assert code == 0, output.err
    payload = json.loads(output.out)
    assert payload["plugin_warnings"][0]["message"] == "Check the source."
    assert payload["plugin_warnings"][0]["code"] == "source"


def test_cli_create_rejection_is_an_error_not_a_silent_success(
    task_plugin_runtime, monkeypatch, tmp_path, capsys,
):
    _prepare(monkeypatch, tmp_path, "task-cli-reject.db")
    plan_id = _create_plan(capsys)

    code = _call("create_task", {"plan_id": plan_id, "title": "blocked task"})
    output = capsys.readouterr()

    assert code == 1
    assert "WRITE_PLUGIN_REJECTED: Blocked by policy." in output.err
    assert output.out.strip() == ""


def test_cli_create_without_plugin_omits_warnings(
    sqlite_runtime_settings, monkeypatch, tmp_path, capsys,
):
    monkeypatch.setattr(settings, "TASK_WRITE_PLUGIN", "")
    _prepare(monkeypatch, tmp_path, "task-cli-plain.db")
    plan_id = _create_plan(capsys)

    code = _call("create_task", {"plan_id": plan_id, "title": "blocked task"})
    output = capsys.readouterr()

    assert code == 0
    assert "plugin_warnings" not in json.loads(output.out)


def test_cli_noop_update_reports_no_warnings(
    task_plugin_runtime, monkeypatch, tmp_path, capsys,
):
    _prepare(monkeypatch, tmp_path, "task-cli-noop.db")
    plan_id = _create_plan(capsys)
    assert _call("create_task", {"plan_id": plan_id, "title": "Stable task"}) == 0
    created = json.loads(capsys.readouterr().out)

    code = _call("update_task", {"task_id": created["id"], "title": "Stable task"})
    output = capsys.readouterr()

    assert code == 0
    assert "plugin_warnings" not in json.loads(output.out)
