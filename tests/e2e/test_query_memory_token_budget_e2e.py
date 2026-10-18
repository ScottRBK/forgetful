"""E2E test (PostgreSQL) that primaries do not use up the per-primary linked memory quota."""
import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")

SETTINGS_OVERRIDE = {"MEMORY_NUM_AUTO_LINK": 0, "RERANKING_ENABLED": False}


async def _create(client, title, content, importance):
    result = await client.call_tool("execute_forgetful_tool", {
        "tool_name": "create_memory",
        "arguments": {
            "title": title,
            "content": content,
            "context": "Checking the linked memory quota",
            "keywords": [],
            "tags": [],
            "importance": importance,
        },
    })
    return result.data["id"]


@pytest.mark.e2e
async def test_primaries_do_not_use_up_linked_memory_quota_e2e(mcp_client):
    primaries = [
        await _create(
            mcp_client,
            f"Kubernetes cluster rollout strategy {i}",
            "Deploy the kubernetes cluster with a rolling rollout strategy",
            9,
        )
        for i in range(4)
    ]
    others = [
        await _create(
            mcp_client,
            f"Banana bread recipe {i}",
            "Mash ripe bananas, mix with flour and sugar, bake until golden",
            5,
        )
        for i in range(6)
    ]
    # The first primary is linked to the 3 other primaries (importance 9) and 6 unrelated memories (importance 5)
    await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "link_memories",
        "arguments": {"memory_id": primaries[0], "related_ids": primaries[1:] + others},
    })

    result = await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "query_memory",
        "arguments": {
            "query": "kubernetes cluster rollout strategy",
            "query_context": "looking up deployment notes",
            "k": 4,
            "max_links_per_primary": 3,
        },
    })

    assert sorted(m["id"] for m in result.data["primary_memories"]) == sorted(primaries)
    linked_ids = [lm["memory"]["id"] for lm in result.data["linked_memories"]]
    assert len(linked_ids) == 3
    assert set(linked_ids) <= set(others)
