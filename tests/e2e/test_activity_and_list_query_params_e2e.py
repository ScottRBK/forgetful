"""E2E (PostgreSQL) tests for since/until handling on GET /api/v1/activity.

asyncpg interprets a naive datetime bound to a timestamptz column in the server
process's local timezone. The route must therefore hand the repository UTC-aware
datetimes so the answer does not depend on the TZ of the server process.
"""
import time
from datetime import UTC, datetime

import pytest

from app.config.settings import settings
from app.models.activity_models import ActionType, ActivityEvent, ActorType, EntityType
from app.models.user_models import UserCreate

pytestmark = pytest.mark.asyncio(loop_scope="session")

EVENT_TIMES = [
    datetime(2026, 10, 18, 12, 0, tzinfo=UTC),
    datetime(2026, 10, 18, 13, 0, tzinfo=UTC),
    datetime(2026, 10, 18, 14, 0, tzinfo=UTC),
]

SERVER_TIMEZONES = ["UTC", "America/New_York", "Asia/Tokyo"]


async def _seed_events(postgres_app):
    user = await postgres_app.user_service.get_or_create_user(
        user=UserCreate(
            external_id=settings.DEFAULT_USER_ID,
            name=settings.DEFAULT_USER_NAME,
            email=settings.DEFAULT_USER_EMAIL,
        ),
    )
    for index, created_at in enumerate(EVENT_TIMES, start=1):
        await postgres_app.activity_service.activity_repo.save_event(
            user.id,
            ActivityEvent(
                entity_type=EntityType.MEMORY,
                entity_id=index,
                action=ActionType.CREATED,
                snapshot={"id": index},
                actor=ActorType.USER,
                created_at=created_at,
            ),
        )


def _hours(body):
    return sorted(event["created_at"][11:16] for event in body["events"])


@pytest.fixture
def server_timezone(monkeypatch):
    """Switch the TZ of the server process for the duration of a test."""
    def switch(zone):
        monkeypatch.setenv("TZ", zone)
        time.tzset()

    yield switch
    monkeypatch.undo()
    time.tzset()


@pytest.mark.e2e
class TestActivityTimestampsPostgres:
    @pytest.mark.parametrize("zone", SERVER_TIMEZONES)
    async def test_naive_since_is_utc_whatever_the_server_timezone(
        self, http_client, postgres_app, server_timezone, zone,
    ):
        await _seed_events(postgres_app)
        server_timezone(zone)

        response = await http_client.get("/api/v1/activity?since=2026-10-18T12:30:00")
        assert response.status_code == 200, response.text
        assert _hours(response.json()) == ["13:00", "14:00"], zone

    @pytest.mark.parametrize("zone", SERVER_TIMEZONES)
    async def test_naive_until_is_utc_whatever_the_server_timezone(
        self, http_client, postgres_app, server_timezone, zone,
    ):
        await _seed_events(postgres_app)
        server_timezone(zone)

        response = await http_client.get("/api/v1/activity?until=2026-10-18T13:30:00")
        assert response.status_code == 200, response.text
        assert _hours(response.json()) == ["12:00", "13:00"], zone

    @pytest.mark.parametrize("zone", SERVER_TIMEZONES)
    async def test_offset_values_are_converted_to_utc(
        self, http_client, postgres_app, server_timezone, zone,
    ):
        await _seed_events(postgres_app)
        server_timezone(zone)

        response = await http_client.get(
            "/api/v1/activity?since=2026-10-18T14:30:00%2B02:00",
        )
        assert response.status_code == 200, response.text
        assert _hours(response.json()) == ["13:00", "14:00"], zone

    async def test_malformed_and_out_of_range_values_are_rejected(self, http_client):
        for query in (
            "since=garbage",
            "until=2099-13-01",
            "offset=abc",
            "entity_id=9223372036854775808",
            "offset=9223372036854775808",
        ):
            response = await http_client.get(f"/api/v1/activity?{query}")
            assert response.status_code == 400, f"{query} -> {response.status_code}"

        response = await http_client.get(
            "/api/v1/activity/memory/1?offset=9223372036854775808",
        )
        assert response.status_code == 400
        response = await http_client.get("/api/v1/activity/memory/1?offset=-1")
        assert response.status_code == 400


@pytest.mark.e2e
class TestIdFiltersFitPostgresInteger:
    """Ids are 32-bit INTEGER columns: a larger filter value must be a 400, not asyncpg's DataError."""

    @pytest.mark.parametrize(
        "url",
        [
            "/api/v1/activity?entity_id=2147483648",
            "/api/v1/activity?entity_id=3000000000",
            "/api/v1/activity?entity_id=-2147483649",
            "/api/v1/memories?project_id=2147483648",
            "/api/v1/memories?project_id=3000000000",
            "/api/v1/memories?project_id=-2147483649",
            "/api/v1/graph?project_id=2147483648",
            "/api/v1/graph?project_id=-2147483649",
        ],
    )
    async def test_id_beyond_int32_is_rejected(self, http_client, url):
        response = await http_client.get(url)
        assert response.status_code == 400, f"{url} -> {response.status_code} {response.text[:200]}"

    @pytest.mark.parametrize(
        "url",
        [
            "/api/v1/activity?entity_id=2147483647",
            "/api/v1/memories?project_id=2147483647",
            "/api/v1/graph?project_id=2147483647",
        ],
    )
    async def test_largest_int32_id_is_accepted(self, http_client, url):
        response = await http_client.get(url)
        assert response.status_code == 200, f"{url} -> {response.status_code} {response.text[:200]}"

    async def test_offset_keeps_the_int64_range(self, http_client):
        response = await http_client.get(f"/api/v1/memories?offset={2**63 - 1}")
        assert response.status_code == 200, response.text
        response = await http_client.get(f"/api/v1/memories?offset={2**63}")
        assert response.status_code == 400
