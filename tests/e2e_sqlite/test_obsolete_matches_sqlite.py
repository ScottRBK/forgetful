"""E2E SQLite tests for create_memory obsolete_matches."""
import pytest

from app.config.settings import settings


async def _create(mcp_client, title: str, content: str, keywords: list[str]):
    return await mcp_client.call_tool(
        "execute_forgetful_tool",
        {
            "tool_name": "create_memory",
            "arguments": {
                "title": title,
                "content": content,
                "context": "obsolete matches e2e",
                "keywords": keywords,
                "tags": ["obsolete-test"],
                "importance": 8,
            },
        },
    )


@pytest.mark.asyncio
async def test_recreating_superseded_memory_reports_match(mcp_client):
    a = await _create(
        mcp_client,
        "Obsolete source A",
        "Policy X requires weekly backups for all tenant databases.",
        ["policy", "backup", "tenant"],
    )
    b = await _create(
        mcp_client,
        "Replacement B",
        "Policy X requires daily backups for all tenant databases.",
        ["policy", "backup", "daily"],
    )
    a_id = a.data["id"]
    b_id = b.data["id"]
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
    a_prime = await _create(
        mcp_client,
        "Obsolete source A",
        "Policy X requires weekly backups for all tenant databases.",
        ["policy", "backup", "tenant"],
    )
    matches = a_prime.data.get("obsolete_matches") or []
    assert matches
    assert matches[0]["id"] == a_id
    assert matches[0]["superseded_by"] == b_id
    assert matches[0]["similarity"] >= settings.OBSOLETE_WARNING_THRESHOLD

    got = await mcp_client.call_tool(
        "execute_forgetful_tool",
        {"tool_name": "get_memory", "arguments": {"memory_id": a_prime.data["id"]}},
    )
    linked = got.data.get("linked_memory_ids") or []
    assert a_id not in linked


@pytest.mark.asyncio
async def test_obsolete_warning_disabled_returns_empty(mcp_client):
    a = await _create(
        mcp_client,
        "Disabled switch source",
        "Weekly backup policy for tenant databases in disabled test.",
        ["disabled", "backup", "tenant"],
    )
    b = await _create(
        mcp_client,
        "Disabled switch replacement",
        "Daily backup policy for tenant databases in disabled test.",
        ["disabled", "backup", "daily"],
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

    prev = settings.OBSOLETE_WARNING_ENABLED
    settings.OBSOLETE_WARNING_ENABLED = False
    try:
        a_prime = await _create(
            mcp_client,
            "Disabled switch source",
            "Weekly backup policy for tenant databases in disabled test.",
            ["disabled", "backup", "tenant"],
        )
        assert a_prime.data.get("obsolete_matches") == []
    finally:
        settings.OBSOLETE_WARNING_ENABLED = prev


@pytest.mark.asyncio
async def test_unrelated_content_no_match(mcp_client):
    old = await _create(
        mcp_client,
        "Old gardening tip",
        "Tomatoes need full sun and consistent watering in summer.",
        ["garden", "tomato"],
    )
    await mcp_client.call_tool(
        "execute_forgetful_tool",
        {
            "tool_name": "mark_memory_obsolete",
            "arguments": {"memory_id": old.data["id"], "reason": "outdated"},
        },
    )
    unrelated = await _create(
        mcp_client,
        "Quantum finance",
        "Monte Carlo simulation for derivative pricing under stochastic volatility.",
        ["finance", "quant"],
    )
    assert unrelated.data.get("obsolete_matches") == []


@pytest.mark.asyncio
async def test_threshold_boundary(mcp_client):
    a = await _create(
        mcp_client,
        "Boundary memory",
        "The quick brown fox jumps over the lazy dog near the river.",
        ["fox", "dog", "river"],
    )
    a_id = a.data["id"]
    await mcp_client.call_tool(
        "execute_forgetful_tool",
        {
            "tool_name": "mark_memory_obsolete",
            "arguments": {"memory_id": a_id, "reason": "superseded"},
        },
    )
    prev = settings.OBSOLETE_WARNING_THRESHOLD
    settings.OBSOLETE_WARNING_THRESHOLD = 0.999
    try:
        a_prime = await _create(
            mcp_client,
            "Boundary memory tweaked",
            "The quick brown fox jumps over the lazy dog near the creek.",
            ["fox", "dog", "creek"],
        )
        ids = [m["id"] for m in (a_prime.data.get("obsolete_matches") or [])]
        assert a_id not in ids
    finally:
        settings.OBSOLETE_WARNING_THRESHOLD = prev


@pytest.mark.asyncio
async def test_obsolete_without_superseded_by(mcp_client):
    a = await _create(
        mcp_client,
        "Superseded test fixture",
        "Legacy cron used to purge temp files every Sunday night.",
        ["cron", "legacy"],
    )
    a_id = a.data["id"]
    await mcp_client.call_tool(
        "execute_forgetful_tool",
        {
            "tool_name": "mark_memory_obsolete",
            "arguments": {"memory_id": a_id, "reason": "supersession test fixture"},
        },
    )
    a_prime = await _create(
        mcp_client,
        "Superseded test fixture",
        "Legacy cron used to purge temp files every Sunday night.",
        ["cron", "legacy"],
    )
    matches = a_prime.data.get("obsolete_matches") or []
    assert any(m["id"] == a_id and m["superseded_by"] is None for m in matches)


@pytest.mark.asyncio
async def test_limit_three_highest_first(mcp_client):
    base = "Shared boilerplate for limit-three obsolete match test item"
    obsolete_ids = []
    for i in range(4):
        r = await _create(
            mcp_client,
            f"Limit three {i}",
            f"{base} variant {i}",
            ["limit-three", f"v{i}"],
        )
        mid = r.data["id"]
        obsolete_ids.append(mid)
        await mcp_client.call_tool(
            "execute_forgetful_tool",
            {
                "tool_name": "mark_memory_obsolete",
                "arguments": {"memory_id": mid, "reason": "duplicate"},
            },
        )
    prime = await _create(
        mcp_client,
        "Limit three prime",
        f"{base} variant prime",
        ["limit-three", "prime"],
    )
    matches = prime.data.get("obsolete_matches") or []
    assert len(matches) == 3
    sims = [m["similarity"] for m in matches]
    assert sims == sorted(sims, reverse=True)
