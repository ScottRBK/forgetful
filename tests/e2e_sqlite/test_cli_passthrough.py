"""E2E tests for the CLI passthrough commands (docs/dev/cli_plan.md phase 3)

Drives main.cli() in-process with patched argv against a file-backed SQLite database
(state must survive multiple cli() invocations; in-memory SQLite is per-connection).
All feature flags are enabled so the discovery surface matches a full deployment.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

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
def cli_sqlite_env(tmp_path):
    """File-backed SQLite settings so state persists across cli() invocations."""
    original = {name: getattr(settings, name) for name in _PATCHED_FIELDS}
    settings.FORGETFUL_SERVER = ""  # never leak these tests onto a configured remote
    settings.DATABASE = "SQLite"
    settings.SQLITE_MEMORY = False
    settings.SQLITE_PATH = str(tmp_path / "cli-e2e.db")
    settings.EMBEDDING_PROVIDER = "FastEmbed"
    settings.RERANKING_ENABLED = False
    settings.FORGETFUL_SCOPES = "*"
    settings.SKILLS_ENABLED = True
    settings.FILES_ENABLED = True
    settings.PLANNING_ENABLED = True
    settings.ACTIVITY_ENABLED = False
    yield settings
    for name, value in original.items():
        setattr(settings, name, value)


def invoke_cli(monkeypatch, capsys, argv):
    monkeypatch.setattr(sys, "argv", ["forgetful", *argv])
    exit_code = main.cli()
    captured = capsys.readouterr()
    return exit_code or 0, captured.out, captured.err


def test_tools_list_prints_categories(cli_sqlite_env, monkeypatch, capsys):
    code, out, _ = invoke_cli(monkeypatch, capsys, ["tools", "list"])

    assert code == 0
    payload = json.loads(out)
    assert payload["total_count"] > 0
    assert len(payload["tools_by_category"]) >= 8


def test_tools_list_category_filter(cli_sqlite_env, monkeypatch, capsys):
    code, out, _ = invoke_cli(monkeypatch, capsys, ["tools", "list", "--category", "memory"])

    assert code == 0
    payload = json.loads(out)
    assert set(payload["tools_by_category"].keys()) == {"memory"}
    assert payload["filtered_by"] == "memory"


def test_tools_info_includes_parameter_schema(cli_sqlite_env, monkeypatch, capsys):
    code, out, _ = invoke_cli(monkeypatch, capsys, ["tools", "info", "query_memory"])

    assert code == 0
    payload = json.loads(out)
    assert payload["name"] == "query_memory"
    assert "json_schema" in payload
    assert any(param["name"] == "query" for param in payload["parameters"])


def test_call_create_then_query_finds_memory(cli_sqlite_env, monkeypatch, capsys):
    create_args = json.dumps({
        "title": "WSL2 DNS resolution fix",
        "content": "Set generateResolvConf false in wsl.conf and pin a static resolver",
        "context": "Recurring networking issue on the desktop dev machine",
        "keywords": ["wsl2", "dns"],
        "tags": ["networking"],
        "importance": 6,
    })
    code, out, _ = invoke_cli(monkeypatch, capsys, ["call", "create_memory", "--args", create_args])
    assert code == 0
    created = json.loads(out)
    assert isinstance(created["id"], int)

    query_args = json.dumps({"query": "WSL2 DNS", "query_context": "cli passthrough e2e"})
    code, out, _ = invoke_cli(monkeypatch, capsys, ["call", "query_memory", "--args", query_args])
    assert code == 0
    found = json.loads(out)
    assert any(memory["id"] == created["id"] for memory in found["primary_memories"])


def test_call_malformed_args_json_exits_with_usage_error(cli_sqlite_env, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["forgetful", "call", "create_memory", "--args", "{not json"])

    with pytest.raises(SystemExit) as excinfo:
        main.cli()

    assert excinfo.value.code == 2
    err = capsys.readouterr().err
    assert "--args" in err
    assert "JSON" in err


def test_call_json_flag_emits_parseable_output(cli_sqlite_env, monkeypatch, capsys):
    code, out, _ = invoke_cli(
        monkeypatch, capsys, ["call", "get_current_user", "--args", "{}", "--json"],
    )

    assert code == 0
    payload = json.loads(out)
    assert payload["name"] == settings.DEFAULT_USER_NAME


def test_call_unknown_tool_exits_one_with_suggestions(cli_sqlite_env, monkeypatch, capsys):
    code, out, err = invoke_cli(monkeypatch, capsys, ["call", "no_such_tool", "--args", "{}"])

    assert code == 1
    assert out == ""
    assert "Tool 'no_such_tool' not found in registry" in err
    assert "Available tools (first 10):" in err


def test_call_unknown_tool_json_mode_emits_error_object(cli_sqlite_env, monkeypatch, capsys):
    code, out, err = invoke_cli(
        monkeypatch, capsys, ["call", "no_such_tool", "--args", "{}", "--json"],
    )

    assert code == 1
    assert out == ""
    # Third-party libs (onnxruntime) may write warnings to stderr during model load;
    # the scriptable contract is that the error object is the last stderr line.
    payload = json.loads(err.strip().splitlines()[-1])
    assert "not found in registry" in payload["error"]


def test_python_main_py_propagates_cli_exit_codes():
    """`python main.py <subcommand>` must exit with the command's status, not 0.

    The `forgetful` console script wraps cli()'s return value in sys.exit(), but
    running the module directly needs main.py to do that itself. FORGETFUL_TOKEN
    forces the bearer branch (no OAuth/token-dir side effects) and port 9 refuses
    the connection immediately, so the command fails fast with exit code 1.
    """
    repo_root = Path(__file__).resolve().parents[2]
    env = {**os.environ, "FORGETFUL_TOKEN": "dummy-token"}

    result = subprocess.run(
        [
            sys.executable, "main.py",
            "call", "get_current_user", "--server", "http://127.0.0.1:9",
        ],
        cwd=repo_root, env=env, capture_output=True, text=True, timeout=120,
    )

    assert result.returncode == 1, (result.stdout, result.stderr)
