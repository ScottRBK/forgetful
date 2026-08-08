"""E2E tests for memory access_count / last_accessed_at via EventBus subscribers.

Uses PostgreSQL + REST API with ACTIVITY_ENABLED and ACTIVITY_TRACK_READS enabled.
"""
import asyncio

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")

SETTINGS_OVERRIDE = {
    "ACTIVITY_ENABLED": True,
    "ACTIVITY_TRACK_READS": True,
    "MEMORY_NUM_AUTO_LINK": 0,
}


async def _wait_for_access_handler() -> None:
    """Allow async EventBus access-tracking handler to complete."""
    await asyncio.sleep(0.5)


@pytest.mark.e2e
class TestMemoryUsageTrackingE2E:
    """access_count updates on read paths when activity read tracking is enabled."""

    async def test_get_memory_increments_access_count(self, http_client):
        """GET /api/v1/memories/{id} bumps access_count when read tracking is on."""
        create_response = await http_client.post("/api/v1/memories", json={
            "title": "Access Count GET E2E",
            "content": "Unique e2e access tracking get path content",
            "context": "E2E access_count via GET",
            "keywords": ["access-count-e2e-get"],
            "tags": ["e2e", "usage"],
            "importance": 7,
        })
        assert create_response.status_code == 201
        memory_id = create_response.json()["id"]

        read_response = await http_client.get(f"/api/v1/memories/{memory_id}")
        assert read_response.status_code == 200

        await _wait_for_access_handler()

        refreshed_response = await http_client.get(f"/api/v1/memories/{memory_id}")
        assert refreshed_response.status_code == 200
        refreshed = refreshed_response.json()
        assert refreshed["access_count"] >= 1
        assert refreshed["last_accessed_at"] is not None

    async def test_query_memory_increments_access_count(self, http_client):
        """POST /api/v1/memories/search records access for returned memory IDs."""
        primary_response = await http_client.post("/api/v1/memories", json={
            "title": "Access Count Query Primary E2E",
            "content": "Unique e2e primary memory for query access tracking",
            "context": "E2E query access primary",
            "keywords": ["access-count-e2e-query-primary"],
            "tags": ["e2e", "usage"],
            "importance": 9,
        })
        assert primary_response.status_code == 201
        primary_id = primary_response.json()["id"]

        linked_response = await http_client.post("/api/v1/memories", json={
            "title": "Access Count Query Linked E2E",
            "content": "Unique e2e linked memory for query access tracking",
            "context": "E2E query access linked",
            "keywords": ["access-count-e2e-query-linked"],
            "tags": ["e2e", "usage"],
            "importance": 8,
        })
        assert linked_response.status_code == 201
        linked_id = linked_response.json()["id"]

        link_response = await http_client.post(
            f"/api/v1/memories/{primary_id}/links",
            json={"related_ids": [linked_id]},
        )
        assert link_response.status_code == 200
        await _wait_for_access_handler()

        primary_before = (await http_client.get(f"/api/v1/memories/{primary_id}")).json()
        linked_before = (await http_client.get(f"/api/v1/memories/{linked_id}")).json()
        primary_count_before = primary_before["access_count"]
        linked_count_before = linked_before["access_count"]

        search_response = await http_client.post("/api/v1/memories/search", json={
            "query": "access-count-e2e-query-primary",
            "query_context": "E2E query access tracking",
            "k": 5,
            "include_links": True,
            "max_links_per_primary": 5,
        })
        assert search_response.status_code == 200
        result = search_response.json()
        assert any(m["id"] == primary_id for m in result["primary_memories"])

        tracked_ids = {m["id"] for m in result["primary_memories"]}
        tracked_ids.update(lm["memory"]["id"] for lm in result["linked_memories"])
        assert primary_id in tracked_ids
        assert linked_id in tracked_ids

        await _wait_for_access_handler()

        primary_after = (await http_client.get(f"/api/v1/memories/{primary_id}")).json()
        linked_after = (await http_client.get(f"/api/v1/memories/{linked_id}")).json()

        assert primary_after["access_count"] > primary_count_before
        assert primary_after["last_accessed_at"] is not None

        assert linked_after["access_count"] > linked_count_before
        assert linked_after["last_accessed_at"] is not None
