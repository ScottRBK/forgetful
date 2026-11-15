"""E2E test: access_count stays at zero when ACTIVITY_TRACK_READS is disabled."""
import pytest

from tests.memory_list_cases import list_memory

pytestmark = pytest.mark.asyncio(loop_scope="session")

SETTINGS_OVERRIDE = {
    "ACTIVITY_ENABLED": True,
    "ACTIVITY_TRACK_READS": False,
}


@pytest.mark.e2e
async def test_get_memory_does_not_increment_access_count_when_tracking_disabled(
    http_client, wait_for_events,
):
    """GET must not bump access_count when read tracking is off."""
    create_response = await http_client.post("/api/v1/memories", json={
        "title": "Access Count Disabled E2E",
        "content": "Unique e2e content when read tracking disabled",
        "context": "E2E negative access tracking gate",
        "keywords": ["access-count-e2e-disabled"],
        "tags": ["e2e", "usage"],
        "importance": 7,
    })
    assert create_response.status_code == 201
    memory_id = create_response.json()["id"]
    baseline = await list_memory(http_client, memory_id)

    read_response = await http_client.get(f"/api/v1/memories/{memory_id}")
    assert read_response.status_code == 200

    await wait_for_events()

    refreshed = await list_memory(http_client, memory_id)
    assert refreshed["access_count"] == 0
    assert refreshed["last_accessed_at"] is None
    assert refreshed["updated_at"] == baseline["updated_at"]
