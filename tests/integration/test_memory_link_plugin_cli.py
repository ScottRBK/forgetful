"""Real CLI parser and local runtime or HTTP MCP remote execution."""
import pytest
from memory_link_plugin_helpers import link_app, memory_arguments
from memory_link_plugin_helpers import link_runtime as link_runtime
from plan_plugin_helpers import loopback_plan_server
from test_plan_plugin_cli import assert_lookups_isolated, cli_call, remote_cli_call


@pytest.mark.parametrize("marker", ["disabled", "plain", "warn", "reject", "error"])
@pytest.mark.parametrize("remote", [False, True])
def test_memory_link_cli_policies(link_runtime, monkeypatch, tmp_path, capsys, marker, remote):
    if marker == "disabled":
        from app.config.settings import settings
        monkeypatch.setattr(settings, "MEMORY_LINK_PLUGIN", "")

    def exercise(call):
        code, source = call("create_memory", memory_arguments("source"))
        assert code == 0
        code, target = call("create_memory", memory_arguments("target", [] if marker in ("plain", "disabled") else [marker]))
        assert code == 0
        code, payload = call("link_memories", {"memory_id": source["id"], "related_ids": [target["id"]]})
        assert code == (1 if marker in ("reject", "error") else 0)
        if code:
            assert ("WRITE_PLUGIN_REJECTED" if marker == "reject" else "WRITE_PLUGIN_UNAVAILABLE") in str(payload)
            assert "SYNTHETIC_PRIVATE_ERROR" not in str(payload)
        else:
            if marker == "disabled":
                assert payload == {"linked_memory_ids": [target["id"]]}
            else:
                assert payload["link_outcomes"] == [{"target_id": target["id"], "status": "created"}]
            assert ("plugin_warnings" in payload) is (marker == "warn")
            code, removed = call("unlink_memories", {"memory_id": source["id"], "related_ids": [target["id"]]})
            assert code == 0
            if marker == "disabled":
                assert removed == {"success": True}
            else:
                assert removed["link_outcomes"][0]["status"] == "removed"
        code, read = call("get_memory", {"memory_id": source["id"]})
        assert code == 0 and "link_outcomes" not in read and "plugin_warnings" not in read

    if remote:
        monkeypatch.setenv("FORGETFUL_TOKEN", "synthetic-test-only-not-a-credential")
        home = tmp_path / "remote-cli-home"
        home.mkdir()
        assert_lookups_isolated(home)
        with loopback_plan_server(link_app()) as server:
            exercise(lambda name, args: remote_cli_call(server, home, name, args))
    else:
        exercise(lambda name, args: cli_call(capsys, name, args))
