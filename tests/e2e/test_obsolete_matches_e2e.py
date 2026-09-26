"""Postgres e2e tests for obsolete_matches on create_memory."""
import pytest

from app.config.settings import settings

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.asyncio(loop_scope="session"),
]


@pytest.mark.asyncio
async def test_recreating_superseded_memory_reports_match(mcp_client):
    a = await mcp_client.call_tool(
        "execute_forgetful_tool",
        {
            "tool_name": "create_memory",
            "arguments": {
                "title": "Pg obsolete A",
                "content": "Runbook step 4 restarts the payment worker service.",
                "context": "pg obsolete",
                "keywords": ["runbook", "payment"],
                "tags": ["pg-obsolete"],
                "importance": 8,
            },
        },
    )
    b = await mcp_client.call_tool(
        "execute_forgetful_tool",
        {
            "tool_name": "create_memory",
            "arguments": {
                "title": "Pg replacement B",
                "content": "Runbook step 4 restarts the billing worker service.",
                "context": "pg obsolete",
                "keywords": ["runbook", "billing"],
                "tags": ["pg-obsolete"],
                "importance": 8,
            },
        },
    )
    a_id, b_id = a.data["id"], b.data["id"]
    await mcp_client.call_tool(
        "execute_forgetful_tool",
        {
            "tool_name": "mark_memory_obsolete",
            "arguments": {
                "memory_id": a_id,
                "reason": "superseded",
                "superseded_by": b_id,
            },
        },
    )
    a_prime = await mcp_client.call_tool(
        "execute_forgetful_tool",
        {
            "tool_name": "create_memory",
            "arguments": {
                "title": "Pg obsolete A",
                "content": "Runbook step 4 restarts the payment worker service.",
                "context": "pg obsolete",
                "keywords": ["runbook", "payment"],
                "tags": ["pg-obsolete"],
                "importance": 8,
            },
        },
    )
    matches = a_prime.data.get("obsolete_matches") or []
    assert matches and matches[0]["id"] == a_id
    assert matches[0]["superseded_by"] == b_id
    assert matches[0]["similarity"] >= settings.OBSOLETE_WARNING_THRESHOLD
