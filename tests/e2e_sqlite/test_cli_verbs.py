"""E2E tests for the curated CLI verbs (docs/dev/cli_plan.md phase 5)

Full-stack cli() invocations over a file-backed SQLite database: memory save/get/
search/recent and project list, including project name resolution.
"""
import json
import sys

import pytest

import main
from app.config.settings import settings

_PATCHED_FIELDS = [
    "DATABASE",
    "SQLITE_MEMORY",
    "SQLITE_PATH",
    "EMBEDDING_PROVIDER",
    "RERANKING_ENABLED",
    "FORGETFUL_SCOPES",
    "FORGETFUL_SERVER",
    "SKILLS_ENABLED",
    "FILES_ENABLED",
    "PLANNING_ENABLED",
    "ACTIVITY_ENABLED",
]


@pytest.fixture
def cli_sqlite_env(tmp_path, monkeypatch):
    original = {name: getattr(settings, name) for name in _PATCHED_FIELDS}
    settings.DATABASE = "SQLite"
    settings.SQLITE_MEMORY = False
    settings.SQLITE_PATH = str(tmp_path / "cli-verbs-e2e.db")
    settings.EMBEDDING_PROVIDER = "FastEmbed"
    settings.RERANKING_ENABLED = False
    settings.FORGETFUL_SCOPES = "*"
    settings.FORGETFUL_SERVER = ""
    settings.SKILLS_ENABLED = False
    settings.FILES_ENABLED = False
    settings.PLANNING_ENABLED = False
    settings.ACTIVITY_ENABLED = False
    monkeypatch.delenv("FORGETFUL_TOKEN", raising=False)
    yield settings
    for name, value in original.items():
        setattr(settings, name, value)


def invoke_cli(monkeypatch, capsys, argv):
    monkeypatch.setattr(sys, "argv", ["forgetful", *argv])
    exit_code = main.cli()
    captured = capsys.readouterr()
    return exit_code or 0, captured.out, captured.err


def _save(monkeypatch, capsys, content, title, *extra):
    return invoke_cli(
        monkeypatch, capsys, ["memory", "save", content, "--title", title, *extra],
    )


def test_memory_save_prints_id_and_get_shows_it(cli_sqlite_env, monkeypatch, capsys):
    code, out, _ = _save(
        monkeypatch, capsys,
        "Use uv tool install for pinned global CLI tooling", "Pinned CLI tooling",
    )
    assert code == 0
    memory_id = int(out.split("memory ")[1].split(":")[0])

    code, out, _ = invoke_cli(monkeypatch, capsys, ["memory", "get", str(memory_id)])
    assert code == 0
    assert f"Memory {memory_id}: Pinned CLI tooling" in out
    assert "Use uv tool install" in out


def test_memory_search_finds_saved_memory_in_human_format(cli_sqlite_env, monkeypatch, capsys):
    code, out, _ = _save(
        monkeypatch, capsys,
        "Set generateResolvConf false to fix WSL2 DNS", "WSL2 DNS resolution fix",
        "--importance", "8",
    )
    assert code == 0

    code, out, _ = invoke_cli(monkeypatch, capsys, ["memory", "search", "WSL2 DNS"])
    assert code == 0
    line = next(ln for ln in out.splitlines() if "WSL2 DNS resolution fix" in ln)
    assert line.startswith("#1")
    assert "[8]" in line
    assert "(memory " in line


def test_memory_search_json_mode_emits_full_payload(cli_sqlite_env, monkeypatch, capsys):
    _save(monkeypatch, capsys, "JSON payload content", "JSON payload memory")

    code, out, _ = invoke_cli(
        monkeypatch, capsys, ["memory", "search", "JSON payload", "--json"],
    )

    assert code == 0
    payload = json.loads(out)
    assert any(m["title"] == "JSON payload memory" for m in payload["primary_memories"])


def test_memory_recent_orders_newest_first_and_respects_limit(
    cli_sqlite_env, monkeypatch, capsys,
):
    for index in range(1, 5):
        _save(monkeypatch, capsys, f"Recent content {index}", f"Recent memory {index}")

    code, out, _ = invoke_cli(monkeypatch, capsys, ["memory", "recent", "-n", "3"])

    assert code == 0
    lines = [ln for ln in out.splitlines() if "(memory " in ln]
    assert len(lines) == 3
    assert "Recent memory 4" in lines[0]
    assert "Recent memory 3" in lines[1]
    assert "Recent memory 2" in lines[2]


def test_project_list_outputs_projects(cli_sqlite_env, monkeypatch, capsys):
    project_args = json.dumps({
        "name": "Verbs project",
        "description": "Project for CLI verb tests",
        "project_type": "development",
    })
    code, _, _ = invoke_cli(
        monkeypatch, capsys, ["call", "create_project", "--args", project_args],
    )
    assert code == 0

    code, out, _ = invoke_cli(monkeypatch, capsys, ["project", "list"])
    assert code == 0
    assert "Verbs project" in out

    code, out, _ = invoke_cli(monkeypatch, capsys, ["project", "list", "--json"])
    assert code == 0
    payload = json.loads(out)
    assert any(p["name"] == "Verbs project" for p in payload["projects"])


def test_project_name_flag_resolves_and_scopes_search(cli_sqlite_env, monkeypatch, capsys):
    project_args = json.dumps({
        "name": "Scoped project",
        "description": "Target for -p name resolution",
        "project_type": "development",
    })
    code, out, _ = invoke_cli(
        monkeypatch, capsys, ["call", "create_project", "--args", project_args],
    )
    assert code == 0

    code, out, _ = _save(
        monkeypatch, capsys,
        "Memory that belongs to the scoped project", "Scoped memory",
        "-p", "Scoped project",
    )
    assert code == 0

    code, out, _ = invoke_cli(
        monkeypatch, capsys,
        ["memory", "search", "scoped project memory", "-p", "Scoped project"],
    )
    assert code == 0
    assert "Scoped memory" in out


def test_unknown_project_name_exits_one_with_available_names(
    cli_sqlite_env, monkeypatch, capsys,
):
    project_args = json.dumps({
        "name": "Only project",
        "description": "The one project that exists",
        "project_type": "development",
    })
    invoke_cli(monkeypatch, capsys, ["call", "create_project", "--args", project_args])

    code, out, err = invoke_cli(
        monkeypatch, capsys, ["memory", "search", "anything", "-p", "no-such-project"],
    )

    assert code == 1
    assert out == ""
    assert "no-such-project" in err
    assert "Only project" in err
