"""Entity Relationship Plugin startup loading and REST, MCP and CLI transport shapes."""

import json
from contextlib import asynccontextmanager

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from httpx import ASGITransport, AsyncClient

from app.bootstrap import build_runtime, dispose_runtime
from app.config.settings import settings
from app.routes.api import entities
from app.routes.cli.parser import dispatch
from app.routes.mcp import meta_tools


@pytest.fixture
async def relationship_plugin_app(entity_relationship_plugin_runtime, request, monkeypatch):
    if getattr(request, "param", True) is False:
        monkeypatch.setattr(settings, "ENTITY_RELATIONSHIP_PLUGIN", "")

    @asynccontextmanager
    async def lifespan(app):
        runtime = await build_runtime()
        app.entity_service = runtime.services.entity
        app.user_service = runtime.services.user
        app.registry = runtime.registry
        app._instance_permitted_tools = runtime.permitted_tools
        app._instance_scopes = runtime.instance_scopes
        try:
            yield
        finally:
            await dispose_runtime(runtime)

    app = FastMCP("Entity Relationship Plugin test", lifespan=lifespan)
    meta_tools.register(app)
    entities.register(app)
    async with Client(app) as client:
        async with AsyncClient(
            transport=ASGITransport(app=app.http_app(), raise_app_exceptions=False),
            base_url="http://test",
        ) as http:
            yield client, http


async def execute(client, name, arguments):
    result = await client.call_tool(
        "execute_forgetful_tool", {"tool_name": name, "arguments": arguments},
    )
    return result.data


async def pair(client):
    person = await execute(client, "create_entity", {
        "name": "Synthetic Person", "entity_type": "Individual",
    })
    org = await execute(client, "create_entity", {
        "name": "Synthetic Org", "entity_type": "Organization",
    })
    return person["id"], org["id"]


async def test_mcp_endpoint_policy_warnings_and_errors(relationship_plugin_app):
    client, _ = relationship_plugin_app
    person_id, org_id = await pair(client)

    allowed = await execute(client, "create_entity_relationship", {
        "source_entity_id": person_id, "target_entity_id": org_id,
        "relationship_type": "works_for",
    })
    assert "plugin_warnings" not in allowed
    with pytest.raises(ToolError, match="WRITE_PLUGIN_REJECTED: works_for must target"):
        await execute(client, "create_entity_relationship", {
            "source_entity_id": org_id, "target_entity_id": person_id,
            "relationship_type": "works_for",
        })

    warned = await execute(client, "update_entity_relationship", {
        "relationship_id": allowed["id"], "relationship_type": "warn",
    })
    assert warned["relationship_type"] == "warn"
    assert warned["plugin_warnings"][0]["message"] == "Check the relationship."
    with pytest.raises(
        ToolError, match="WRITE_PLUGIN_UNAVAILABLE: Entity Relationship Plugin unavailable",
    ):
        await execute(client, "update_entity_relationship", {
            "relationship_id": allowed["id"], "relationship_type": "error",
        })

    read = await execute(client, "get_entity_relationships", {"entity_id": person_id})
    assert [item["relationship_type"] for item in read["relationships"]] == ["warn"]

    await execute(client, "update_entity_relationship", {
        "relationship_id": allowed["id"], "relationship_type": "delete_blocked",
    })
    with pytest.raises(ToolError, match="WRITE_PLUGIN_REJECTED: Relationship type not allowed"):
        await execute(client, "delete_entity_relationship", {"relationship_id": allowed["id"]})
    await execute(client, "update_entity_relationship", {
        "relationship_id": allowed["id"], "relationship_type": "advises",
    })
    deleted = await execute(client, "delete_entity_relationship", {
        "relationship_id": allowed["id"],
    })
    assert deleted["success"] is True
    assert deleted["deleted_id"] == allowed["id"]
    assert deleted["plugin_warnings"][0]["message"] == "Graph consumers notified."


async def test_rest_warnings_errors_and_flat_shapes(relationship_plugin_app):
    _, http = relationship_plugin_app
    person = (await http.post("/api/v1/entities", json={
        "name": "REST Person", "entity_type": "Individual",
    })).json()
    org = (await http.post("/api/v1/entities", json={
        "name": "REST Org", "entity_type": "Organization",
    })).json()
    base = f"/api/v1/entities/{person['id']}/relationships"

    created = await http.post(base, json={
        "target_entity_id": org["id"], "relationship_type": "warn",
    })
    assert created.status_code == 201
    payload = created.json()
    assert payload["relationship_type"] == "warn"
    assert payload["plugin_warnings"][0]["code"] == "rel"
    relationship_url = f"/api/v1/entities/relationships/{payload['id']}"

    rejected = await http.post(base, json={
        "target_entity_id": org["id"], "relationship_type": "blocked",
    })
    assert rejected.status_code == 400
    assert rejected.json() == {"error": "Relationship type not allowed."}
    unavailable = await http.put(relationship_url, json={"relationship_type": "error"})
    assert unavailable.status_code == 503
    assert unavailable.json() == {"error": "Entity Relationship Plugin unavailable."}

    updated = await http.put(relationship_url, json={"strength": 0.8})
    assert updated.status_code == 200
    assert updated.json()["strength"] == 0.8
    # The proposed relationship keeps its stored type, so the type policy still applies.
    assert updated.json()["plugin_warnings"][0]["code"] == "rel"

    deleted = await http.delete(relationship_url)
    assert deleted.status_code == 200
    assert deleted.json() == {
        "success": True,
        "plugin_warnings": [{
            "outcome": "warn", "message": "Graph consumers notified.", "code": "notify",
        }],
    }
    missing = await http.delete(relationship_url)
    assert missing.status_code == 404


@pytest.mark.parametrize("relationship_plugin_app", [False], indirect=True)
async def test_without_plugin_response_shapes_are_unchanged(relationship_plugin_app):
    client, http = relationship_plugin_app
    person_id, org_id = await pair(client)
    created = await execute(client, "create_entity_relationship", {
        "source_entity_id": person_id, "target_entity_id": org_id,
        "relationship_type": "blocked",
    })
    assert "plugin_warnings" not in created
    deleted = await http.delete(f"/api/v1/entities/relationships/{created['id']}")
    assert deleted.json() == {"success": True}


def test_local_cli_exposes_warnings_and_rejections(
    entity_relationship_plugin_runtime, monkeypatch, tmp_path, capsys,
):
    monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "relationship-cli.db"))

    def call(tool, arguments):
        code = dispatch(
            ["call", tool, "--args", json.dumps(arguments), "--local", "--json"],
            serve_runner=None, reembed_runner=None,
        )
        return code, capsys.readouterr()

    ids = []
    for name, entity_type in (("CLI Person", "Individual"), ("CLI Org", "Organization")):
        code, output = call("create_entity", {"name": name, "entity_type": entity_type})
        assert code == 0
        ids.append(json.loads(output.out)["id"])

    code, output = call("create_entity_relationship", {
        "source_entity_id": ids[0], "target_entity_id": ids[1], "relationship_type": "warn",
    })
    assert code == 0
    assert json.loads(output.out)["plugin_warnings"][0]["message"] == "Check the relationship."

    code, output = call("create_entity_relationship", {
        "source_entity_id": ids[0], "target_entity_id": ids[1], "relationship_type": "blocked",
    })
    assert code == 1
    assert "WRITE_PLUGIN_REJECTED: Relationship type not allowed." in output.err


@pytest.mark.parametrize(
    "reference", ["missing_plugin:plugin", "runtime_relationship_checks:decide", "not-a-ref"],
)
async def test_invalid_reference_fails_startup(
    entity_relationship_plugin_runtime, monkeypatch, reference,
):
    monkeypatch.setattr(settings, "ENTITY_RELATIONSHIP_PLUGIN", reference)
    with pytest.raises(ValueError, match="ENTITY_RELATIONSHIP_PLUGIN"):
        await build_runtime()
