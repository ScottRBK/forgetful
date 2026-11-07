"""Real generic CLI package calls, including import into a fresh database."""
import json

from app.config.settings import settings
from tests.e2e_sqlite.test_cli_passthrough import cli_sqlite_env as cli_sqlite_env
from tests.e2e_sqlite.test_cli_passthrough import invoke_cli
from tests.skill_bundle_cases import skill_bundle


def test_cli_roundtrip_into_fresh_database(cli_sqlite_env, tmp_path, monkeypatch, capsys):
    def call(tool, **arguments):
        encoded = json.dumps(arguments)
        assert len(encoded.encode("utf-8")) < 120000
        code, out, err = invoke_cli(monkeypatch, capsys, [
            "call", tool, "--args", encoded, "--local", "--json",
        ])
        assert code == 0, err
        return json.loads(out)

    info_code, out, err = invoke_cli(monkeypatch, capsys, [
        "tools", "info", "import_skill_bundle", "--local", "--json",
    ])
    assert info_code == 0, err
    assert json.loads(out)["name"] == "import_skill_bundle"
    original = call("import_skill_bundle", bundle=skill_bundle())
    exported = call("export_skill_bundle", skill_id=original["skill"]["id"])
    source_database = settings.SQLITE_PATH
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "independent-target.db"))
    assert settings.SQLITE_PATH != source_database
    assert not (tmp_path / "independent-target.db").exists()
    call("create_document", title="Target seed", description="Different native ID space", content="seed")
    recreated = call("import_skill_bundle", bundle=exported)
    source_doc = next(m["resource_id"] for m in original["members"] if m["kind"] == "document")
    target_doc = next(m["resource_id"] for m in recreated["members"] if m["kind"] == "document")
    assert source_doc != target_doc
    assert call("export_skill_bundle", skill_id=recreated["skill"]["id"]) == exported


def test_local_cli_component_scope_is_enforced(cli_sqlite_env, monkeypatch, capsys):
    monkeypatch.setattr(settings, "FORGETFUL_SCOPES", "write:skills,read")
    code, out, err = invoke_cli(monkeypatch, capsys, [
        "call", "import_skill_bundle", "--local", "--json",
        "--args", json.dumps({"bundle": skill_bundle()}),
    ])
    assert code == 1 and out == ""
    assert "create_document" in err and "create_file" in err
