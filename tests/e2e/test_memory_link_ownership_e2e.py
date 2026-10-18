"""PostgreSQL E2E tests: memory links must never cross user boundaries.

PostgreSQL has no row-level security policies in this repository, so the
repository query itself has to be user-filtered. Mirrors the SQLite two-user tests.
"""
import pytest

from app.config.settings import settings

pytestmark = pytest.mark.asyncio(loop_scope="session")

SETTINGS_OVERRIDE = {"MEMORY_NUM_AUTO_LINK": 0}
NONEXISTENT_MEMORY_ID = 999_999


async def _create_memory(mcp_client, title: str) -> int:
    result = await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "create_memory", "arguments": {
            "title": title,
            "content": f"Body of {title}",
            "context": "Testing cross-user link ownership",
            "keywords": [title.lower().replace(" ", "-")],
            "tags": ["link-ownership"],
            "importance": 6,
        },
    })
    return result.data["id"]


async def _get_linked_ids(mcp_client, memory_id: int) -> list[int]:
    result = await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "get_memory", "arguments": {"memory_id": memory_id},
    })
    return result.data["linked_memory_ids"]


async def _link(mcp_client, memory_id: int, related_ids: list[int]) -> list[int]:
    result = await mcp_client.call_tool("execute_forgetful_tool", {
        "tool_name": "link_memories",
        "arguments": {"memory_id": memory_id, "related_ids": related_ids},
    })
    return result.data["linked_memory_ids"]


@pytest.mark.e2e
async def test_link_memories_skips_other_users_memory_e2e(mcp_client, monkeypatch):
    """Linking to another user's memory is skipped and leaves both memories unlinked."""
    own_id = await _create_memory(mcp_client, "Alice private note")

    with monkeypatch.context() as other_user:
        other_user.setattr(settings, "DEFAULT_USER_ID", "link-ownership-user-b")
        other_user.setattr(settings, "DEFAULT_USER_EMAIL", "link-ownership-b@example.test")
        foreign_id = await _create_memory(mcp_client, "Bob private note")

    assert await _link(mcp_client, own_id, [foreign_id]) == []

    assert await _get_linked_ids(mcp_client, own_id) == []
    with monkeypatch.context() as other_user:
        other_user.setattr(settings, "DEFAULT_USER_ID", "link-ownership-user-b")
        other_user.setattr(settings, "DEFAULT_USER_EMAIL", "link-ownership-b@example.test")
        assert await _get_linked_ids(mcp_client, foreign_id) == []


@pytest.mark.e2e
async def test_link_memories_foreign_id_indistinguishable_from_missing_e2e(
    mcp_client, monkeypatch,
):
    """Foreign ids are skipped exactly like unknown ids, while own ids still link."""
    own_id = await _create_memory(mcp_client, "Alice source note")
    own_target_id = await _create_memory(mcp_client, "Alice target note")

    with monkeypatch.context() as other_user:
        other_user.setattr(settings, "DEFAULT_USER_ID", "link-ownership-user-b")
        other_user.setattr(settings, "DEFAULT_USER_EMAIL", "link-ownership-b@example.test")
        foreign_id = await _create_memory(mcp_client, "Bob note")

    linked = await _link(mcp_client, own_id, [foreign_id, NONEXISTENT_MEMORY_ID, own_target_id])

    assert linked == [own_target_id]
    assert await _get_linked_ids(mcp_client, own_id) == [own_target_id]
