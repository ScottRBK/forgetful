"""Actual REST and MCP responses, including atomic preflight for MCP multi-unlink."""
import importlib

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from httpx import ASGITransport, AsyncClient
from memory_link_plugin_helpers import execute, link_app, memory_arguments
from memory_link_plugin_helpers import link_runtime as link_runtime

from app.config.settings import settings


@pytest.fixture
async def link_clients(link_runtime):
    app = link_app()
    async with Client(app) as client:
        async with AsyncClient(transport=ASGITransport(app=app.http_app(), raise_app_exceptions=False),
                               base_url="http://test") as http:
            yield app, client, http


async def create(client, title, tags=None):
    return (await execute(client, "create_memory", memory_arguments(title, tags)))["id"]


async def test_mcp_batch_unlink_preflights_every_target_before_any_removal(link_clients, link_runtime):
    _, client, _ = link_clients
    source, allowed, blocked = [await create(client, name) for name in ("source", "allowed", "blocked")]
    linked = await execute(client, "link_memories", {"memory_id": source, "related_ids": [allowed, blocked]})
    assert [item["status"] for item in linked["link_outcomes"]] == ["created", "created"]
    await execute(client, "update_memory", {"memory_id": blocked, "tags": ["reject"]})
    module = importlib.import_module(link_runtime)
    module.after_calls.clear()
    with pytest.raises(ToolError, match="WRITE_PLUGIN_REJECTED"):
        await execute(client, "unlink_memories", {"memory_id": source, "related_ids": [allowed, blocked]})
    read = await execute(client, "get_memory", {"memory_id": source})
    assert set(read["linked_memory_ids"]) == {allowed, blocked}
    assert "link_outcomes" not in read and "plugin_warnings" not in read
    assert module.after_calls == []
    await execute(client, "update_memory", {"memory_id": blocked, "tags": []})
    removed = await execute(client, "unlink_memories", {"memory_id": source, "related_ids": [allowed, blocked]})
    assert removed["success"] is True
    assert [item["status"] for item in removed["link_outcomes"]] == ["removed", "removed"]
    assert len(module.after_calls) == 1 and len(module.after_calls[0].pairs) == 2
    noop = await execute(client, "unlink_memories", {"memory_id": source, "related_ids": [allowed, blocked]})
    assert noop["success"] is False
    assert [item["status"] for item in noop["link_outcomes"]] == ["noop", "noop"]
    assert len(module.after_calls) == 1


async def test_rest_link_warn_reject_unavailable_and_unlink_noop(link_clients):
    _, client, http = link_clients
    source = await create(client, "source")
    warned = await create(client, "warned", ["warn"])
    blocked = await create(client, "blocked", ["reject"])
    unavailable = await create(client, "unavailable", ["error"])
    for target, status in ((blocked, 400), (unavailable, 503)):
        response = await http.post(f"/api/v1/memories/{source}/links", json={"related_ids": [target]})
        assert response.status_code == status
        assert "SYNTHETIC_PRIVATE_ERROR" not in response.text
    response = await http.post(f"/api/v1/memories/{source}/links", json={"related_ids": [warned]})
    assert response.status_code == 200
    payload = response.json()
    assert payload["linked_ids"] == [warned]
    assert payload["link_outcomes"] == [{"target_id": warned, "status": "created"}]
    assert payload["plugin_warnings"][0]["code"] == "LINK_POLICY"
    removed = await http.delete(f"/api/v1/memories/{source}/links/{warned}")
    assert removed.status_code == 200 and removed.json()["link_outcomes"][0]["status"] == "removed"
    noop = await http.delete(f"/api/v1/memories/{source}/links/{warned}")
    assert noop.status_code == 404 and noop.json()["link_outcomes"][0]["status"] == "noop"


async def test_no_plugin_preserves_exact_legacy_link_and_unlink_json(link_runtime, monkeypatch):
    monkeypatch.setattr(settings, "MEMORY_LINK_PLUGIN", "")
    app = link_app()
    async with Client(app) as client:
        async with AsyncClient(transport=ASGITransport(app=app.http_app()), base_url="http://test") as http:
            source, target = [await create(client, title) for title in ("source", "target")]
            linked = await http.post(f"/api/v1/memories/{source}/links", json={"related_ids": [target]})
            assert linked.content == f'{{"linked_ids":[{target}]}}'.encode()
            rest_removed = await http.delete(f"/api/v1/memories/{source}/links/{target}")
            assert rest_removed.content == b'{"success":true}'
            await execute(client, "link_memories", {"memory_id": source, "related_ids": [target]})
            removed = await execute(client, "unlink_memories", {"memory_id": source, "related_ids": [target]})
            assert removed == {"success": True}
            linked = await execute(client, "link_memories", {"memory_id": source, "related_ids": [target]})
            assert linked == {"linked_memory_ids": [target]}


async def test_mcp_automatic_create_exposes_actual_outcomes_and_warning(link_clients, monkeypatch):
    _, client, _ = link_clients
    allowed = await create(client, "allowed")
    blocked = await create(client, "blocked", ["reject"])
    monkeypatch.setattr(settings, "MEMORY_NUM_AUTO_LINK", 5)
    result = await execute(client, "create_memory", memory_arguments("auto source"))
    assert result["linked_memory_ids"] == [allowed]
    assert {item["target_id"]: item["status"] for item in result["link_outcomes"]} == {
        allowed: "created", blocked: "rejected",
    }
    assert result["plugin_warnings"]
