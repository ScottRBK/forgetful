"""Real CLI process over HTTP MCP; reuse the established bounded server fixture."""
import json
import os
import subprocess
import sys

import pytest

from app.config.settings import settings
from tests.e2e_sqlite.test_cli_remote import (
    cli_remote_env as cli_remote_env,
)
from tests.e2e_sqlite.test_cli_remote import (
    http_server_url as http_server_url,
)
from tests.skill_bundle_cases import skill_bundle
from tests.skill_bundle_feedback_cases import check_help


@pytest.fixture
def bundle_server_url(cli_remote_env, monkeypatch, request):
    with monkeypatch.context() as patch:
        patch.setattr(settings, "SKILLS_ENABLED", True)
        patch.setattr(settings, "FILES_ENABLED", True)
        # Resolve the established server only after feature settings are set.
        yield request.getfixturevalue("http_server_url")


def test_remote_cli_bundle_roundtrip(bundle_server_url, tmp_path):
    for parts in (("AppData", "Local"), ("AppData", "Roaming")):
        tmp_path.joinpath(*parts).mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, HOME=str(tmp_path), USERPROFILE=str(tmp_path),
               XDG_CONFIG_HOME=str(tmp_path / "config"), XDG_DATA_HOME=str(tmp_path / "data"),
               XDG_CACHE_HOME=str(tmp_path / "cache"), XDG_STATE_HOME=str(tmp_path / "state"),
               FORGETFUL_TOKEN="synthetic-bundle-cli-token")

    def call(tool, arguments):
        completed = subprocess.run(  # noqa: S603 - synthetic argv, loopback server, no shell
            [sys.executable, "-c", "from main import cli; raise SystemExit(cli())",
             "call", tool, "--args", json.dumps(arguments), "--json", "--server", bundle_server_url],
            capture_output=True, text=True, encoding="utf-8", timeout=30, env=env, check=False,
        )
        assert completed.returncode == 0, completed.stderr
        return json.loads(completed.stdout)

    for tool in ("import_skill_bundle", "export_skill_bundle"):
        info = subprocess.run(  # noqa: S603 - synthetic argv and owned loopback server
            [sys.executable, "-c", "from main import cli; raise SystemExit(cli())",
             "tools", "info", tool, "--json", "--server", bundle_server_url],
            capture_output=True, text=True, timeout=30, env=env, check=False,
        )
        assert info.returncode == 0, info.stderr
        check_help(json.loads(info.stdout))
    created = call("import_skill_bundle", {"bundle": skill_bundle()})
    exported = call("export_skill_bundle", {"skill_id": created["skill"]["id"]})
    assert len(exported["resources"]) == 3
    assert {r["kind"] for r in exported["resources"]} == {"document", "code_artifact", "file"}
