"""E2E tests for CLI project resolution and human-output safety

Full-stack cli() invocations over a file-backed SQLite database: deterministic -p
resolution, terminal-safe rendering of stored text, the obsolete marker in
`memory get` and stdout encoding safety after a committed write.
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
def cli_env(tmp_path, monkeypatch):
    original = {name: getattr(settings, name) for name in _PATCHED_FIELDS}
    settings.DATABASE = "SQLite"
    settings.SQLITE_MEMORY = False
    settings.SQLITE_PATH = str(tmp_path / "cli-verbs-render-e2e.db")
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


def _create_project(monkeypatch, capsys, name):
    arguments = json.dumps({"name": name, "description": "d", "project_type": "development"})
    code, out, err = invoke_cli(
        monkeypatch, capsys, ["call", "create_project", "--args", arguments, "--json"],
    )
    assert code == 0, err
    return json.loads(out)["id"]


def test_exact_case_project_name_is_reachable_by_name(cli_env, monkeypatch, capsys):
    upper_id = _create_project(monkeypatch, capsys, "Alpha")
    lower_id = _create_project(monkeypatch, capsys, "alpha")
    assert upper_id != lower_id

    code, out, err = invoke_cli(
        monkeypatch, capsys, ["memory", "save", "exact case body", "--title", "t", "-p", "Alpha", "--json"],
    )

    assert code == 0, err
    assert json.loads(out)["project_ids"] == [upper_id]


def test_identical_project_names_are_reported_as_ambiguous(cli_env, monkeypatch, capsys):
    first = _create_project(monkeypatch, capsys, "Twin")
    second = _create_project(monkeypatch, capsys, "Twin")

    code, out, err = invoke_cli(
        monkeypatch, capsys, ["memory", "save", "body", "--title", "t", "-p", "Twin"],
    )

    assert code == 1
    assert out == ""
    assert "Ambiguous project 'Twin'" in err
    assert str(first) in err and str(second) in err


def test_digit_only_project_name_resolves_by_name(cli_env, monkeypatch, capsys):
    project_id = _create_project(monkeypatch, capsys, "2024")
    assert project_id != 2024

    code, out, err = invoke_cli(
        monkeypatch, capsys,
        ["memory", "save", "numeric project body", "--title", "Numeric project memory", "-p", "2024"],
    )
    assert code == 0, err

    code, out, err = invoke_cli(monkeypatch, capsys, ["memory", "recent", "-p", "2024"])
    assert code == 0, err
    assert "Numeric project memory" in out

    code, out, err = invoke_cli(monkeypatch, capsys, ["memory", "recent", "-p", str(project_id)])
    assert code == 0, err
    assert "Numeric project memory" in out


def test_non_ascii_digit_project_value_reports_unknown_project(cli_env, monkeypatch, capsys):
    _create_project(monkeypatch, capsys, "Real project")

    code, out, err = invoke_cli(monkeypatch, capsys, ["memory", "recent", "-p", "²"])

    assert code == 1
    assert "Unknown project" in err
    assert "invalid literal" not in err


@pytest.mark.parametrize(
    "argv",
    [
        ["memory", "save", "note body", "--title", "T", "-p", ""],
        ["memory", "recent", "-p", ""],
        ["memory", "search", "note body", "-c", "ctx", "-p", ""],
    ],
)
def test_empty_project_value_is_rejected_and_nothing_is_saved(cli_env, monkeypatch, capsys, argv):
    _create_project(monkeypatch, capsys, "Alpha")

    code, out, err = invoke_cli(monkeypatch, capsys, argv)

    assert code == 1
    assert out == ""
    assert "Unknown project ''" in err
    _, recent_out, _ = invoke_cli(monkeypatch, capsys, ["memory", "recent", "--json"])
    assert json.loads(recent_out)["memories"] == []
