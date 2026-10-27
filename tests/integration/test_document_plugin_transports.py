"""Document Plugin REST and MCP transport shapes."""

from contextlib import asynccontextmanager

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from httpx import ASGITransport, AsyncClient

from app.bootstrap import build_runtime, dispose_runtime
from app.config.settings import settings
from app.routes.api import documents
from app.routes.mcp import meta_tools


@pytest.fixture
async def document_plugin_app(document_plugin_runtime, request, monkeypatch):
    if getattr(request, "param", True) is False:
        monkeypatch.setattr(settings, "DOCUMENT_WRITE_PLUGIN", "")

    @asynccontextmanager
    async def lifespan(app):
        runtime = await build_runtime()
        app.document_service = runtime.services.document
        app.user_service = runtime.services.user
        app.registry = runtime.registry
        app._instance_permitted_tools = runtime.permitted_tools
        app._instance_scopes = runtime.instance_scopes
        try:
            yield
        finally:
            await dispose_runtime(runtime)

    app = FastMCP("Document Plugin test", lifespan=lifespan)
    meta_tools.register(app)
    documents.register(app)
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


async def test_document_mcp_warn_update_shape_rejection_and_read_isolation(document_plugin_app):
    client, _ = document_plugin_app
    allowed = await execute(client, "create_document", {
        "title": "Allowed Doc", "description": "Summary", "content": "Body", "tags": [],
    })
    assert "plugin_warnings" not in allowed
    document_id = allowed["id"]
    warned = await execute(client, "update_document", {
        "document_id": document_id, "tags": ["warn"],
    })
    assert warned["id"] == document_id
    assert warned["plugin_warnings"][0]["message"] == "Check the source."
    with pytest.raises(ToolError, match="WRITE_PLUGIN_REJECTED: Remove the blocked tag"):
        await execute(client, "update_document", {
            "document_id": document_id, "tags": ["blocked"],
        })
    with pytest.raises(
        ToolError, match="WRITE_PLUGIN_UNAVAILABLE: Document Write Plugin unavailable",
    ):
        await execute(client, "update_document", {
            "document_id": document_id, "tags": ["error"],
        })
    read = await execute(client, "get_document", {"document_id": document_id})
    assert read["tags"] == ["warn"]
    assert "plugin_warnings" not in read


async def test_document_mcp_delete_warn_reject_and_unavailable(document_plugin_app):
    client, _ = document_plugin_app

    async def create(tags):
        return await execute(client, "create_document", {
            "title": "Delete Doc", "description": "Summary", "content": "Body", "tags": tags,
        })

    plain_id = (await create([]))["id"]
    result = await execute(client, "delete_document", {"document_id": plain_id})
    assert result["success"] is True
    assert "plugin_warnings" not in result

    warn_id = (await create(["delete_warn"]))["id"]
    warned = await execute(client, "delete_document", {"document_id": warn_id})
    assert warned["success"] is True
    assert warned["plugin_warnings"][0]["message"] == "Check the source."

    blocked_id = (await create([]))["id"]
    await execute(client, "update_document", {"document_id": blocked_id, "tags": ["delete_blocked"]})
    with pytest.raises(ToolError, match="WRITE_PLUGIN_REJECTED: Remove the blocked tag"):
        await execute(client, "delete_document", {"document_id": blocked_id})
    assert (await execute(client, "get_document", {"document_id": blocked_id}))["id"] == blocked_id

    error_id = (await create([]))["id"]
    await execute(client, "update_document", {"document_id": error_id, "tags": ["delete_error"]})
    with pytest.raises(
        ToolError, match="WRITE_PLUGIN_UNAVAILABLE: Document Write Plugin unavailable",
    ):
        await execute(client, "delete_document", {"document_id": error_id})


async def test_document_rest_warnings_errors_and_flat_update(document_plugin_app):
    _, http = document_plugin_app
    created = await http.post("/api/v1/documents", json={
        "title": "REST Doc", "description": "Summary", "content": "Body", "tags": ["warn"],
    })
    assert created.status_code == 201
    payload = created.json()
    assert payload["plugin_warnings"][0]["message"] == "Check the source."
    document_id = payload["id"]
    updated = await http.put(f"/api/v1/documents/{document_id}", json={"tags": []})
    assert updated.status_code == 200
    assert updated.json()["id"] == document_id
    assert "plugin_warnings" not in updated.json()
    rejected = await http.put(f"/api/v1/documents/{document_id}", json={"tags": ["blocked"]})
    assert rejected.status_code == 400
    assert rejected.json()["error"] == "Remove the blocked tag."
    unavailable = await http.post("/api/v1/documents", json={
        "title": "REST Fail", "description": "Summary", "content": "Body", "tags": ["error"],
    })
    assert unavailable.status_code == 503
    assert unavailable.json()["error"] == "Document Write Plugin unavailable."
    read = await http.get(f"/api/v1/documents/{document_id}")
    assert "plugin_warnings" not in read.json()


async def test_document_rest_delete_warning_rejection_and_unavailability(document_plugin_app):
    _, http = document_plugin_app

    created = await http.post("/api/v1/documents", json={
        "title": "Del Plain", "description": "Summary", "content": "Body", "tags": [],
    })
    document_id = created.json()["id"]
    response = await http.delete(f"/api/v1/documents/{document_id}")
    assert response.status_code == 200
    assert response.json() == {"success": True}

    created = await http.post("/api/v1/documents", json={
        "title": "Del Warn", "description": "Summary", "content": "Body", "tags": ["delete_warn"],
    })
    document_id = created.json()["id"]
    response = await http.delete(f"/api/v1/documents/{document_id}")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["plugin_warnings"][0]["message"] == "Check the source."
    assert (await http.get(f"/api/v1/documents/{document_id}")).status_code == 404

    created = await http.post("/api/v1/documents", json={
        "title": "Del Blocked", "description": "Summary", "content": "Body", "tags": [],
    })
    document_id = created.json()["id"]
    await http.put(f"/api/v1/documents/{document_id}", json={"tags": ["delete_blocked"]})
    response = await http.delete(f"/api/v1/documents/{document_id}")
    assert response.status_code == 400
    assert response.json() == {"error": "Remove the blocked tag."}
    assert (await http.get(f"/api/v1/documents/{document_id}")).status_code == 200

    created = await http.post("/api/v1/documents", json={
        "title": "Del Error", "description": "Summary", "content": "Body", "tags": [],
    })
    document_id = created.json()["id"]
    await http.put(f"/api/v1/documents/{document_id}", json={"tags": ["delete_error"]})
    response = await http.delete(f"/api/v1/documents/{document_id}")
    assert response.status_code == 503
    assert response.json() == {"error": "Document Write Plugin unavailable."}
    assert (await http.get(f"/api/v1/documents/{document_id}")).status_code == 200


@pytest.mark.parametrize("document_plugin_app", [False], indirect=True)
async def test_document_rest_delete_without_plugin_stays_minimal_shape(document_plugin_app):
    _, http = document_plugin_app
    created = await http.post("/api/v1/documents", json={
        "title": "Plain", "description": "Summary", "content": "Body",
    })
    document_id = created.json()["id"]
    response = await http.delete(f"/api/v1/documents/{document_id}")
    assert response.status_code == 200
    assert response.json() == {"success": True}


async def test_document_mcp_warn_and_reject_create(document_plugin_app):
    client, _ = document_plugin_app
    allowed = await execute(client, "create_document", {
        "title": "Allowed Doc", "description": "Summary", "content": "Body", "tags": [],
    })
    assert "plugin_warnings" not in allowed
    warned = await execute(client, "create_document", {
        "title": "Warn Org", "description": "Summary", "content": "Body", "tags": ["warn"],
    })
    assert warned["plugin_warnings"][0]["message"] == "Check the source."
    with pytest.raises(ToolError, match="WRITE_PLUGIN_REJECTED: Remove the blocked tag"):
        await execute(client, "create_document", {
            "title": "Blocked", "description": "Summary", "content": "Body", "tags": ["blocked"],
        })
