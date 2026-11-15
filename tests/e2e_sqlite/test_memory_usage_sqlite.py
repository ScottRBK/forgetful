"""SQLite read/search tracking regressions with a real EventBus."""

import pytest
from fastmcp import Client
from httpx import ASGITransport, AsyncClient

from app.config.settings import settings
from app.events import EventBus
from tests.memory_list_cases import create_memory, list_memory
from tests.memory_usage_cases import TestMemoryUsageTracking as TestMemoryUsageTracking

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def http_client(sqlite_app, monkeypatch):
    monkeypatch.setattr(settings, "ACTIVITY_TRACK_READS", True)
    monkeypatch.setattr(settings, "MEMORY_NUM_AUTO_LINK", 0)
    async with Client(sqlite_app) as _:
        bus = EventBus()
        bus.subscribe("*.*", sqlite_app.activity_service.handle_event)
        sqlite_app.memory_service._event_bus = bus
        sqlite_app.memory_service.register_access_tracking_handlers(bus)
        sqlite_app.event_bus = bus
        transport = ASGITransport(app=sqlite_app.http_app())
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                yield client
        finally:
            await bus.wait_for_pending(timeout=5)


@pytest.fixture
def wait_for_events(http_client, sqlite_app):
    async def wait():
        await sqlite_app.event_bus.wait_for_pending(timeout=5)

    return wait


async def test_get_does_not_track_when_disabled(http_client, wait_for_events, monkeypatch):
    # Keep the real event bus connected: only the read-tracking flag disables the write.
    monkeypatch.setattr(settings, "ACTIVITY_TRACK_READS", False)
    created = await create_memory(http_client, "Tracking disabled SQLite")
    baseline = await list_memory(http_client, created["id"])

    read_response = await http_client.get(f"/api/v1/memories/{created['id']}")
    assert read_response.status_code == 200, read_response.text
    await wait_for_events()

    after = await list_memory(http_client, created["id"])
    assert after["access_count"] == 0
    assert after["last_accessed_at"] is None
    assert after["updated_at"] == baseline["updated_at"]
