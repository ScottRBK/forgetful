"""E2E (SQLite) tests for query-parameter handling on the activity, memories and graph routes.

Malformed or out-of-range values must produce a 400 naming the parameter instead of
being silently ignored (activity) or reaching the database (500), since/until must be
normalised to UTC, and zero is a real value for ``project_id``.
"""
import time
from datetime import UTC, datetime

import pytest
from fastmcp import Client
from httpx import ASGITransport, AsyncClient

from app.config.settings import settings
from app.models.activity_models import ActionType, ActivityEvent, ActorType, EntityType
from app.models.user_models import UserCreate

BEYOND_INT64 = 2**63  # 9223372036854775808, one past the largest SQL integer

EVENT_TIMES = [
    datetime(2026, 10, 18, 12, 0, tzinfo=UTC),
    datetime(2026, 10, 18, 13, 0, tzinfo=UTC),
    datetime(2026, 10, 18, 14, 0, tzinfo=UTC),
]


@pytest.fixture
async def client(sqlite_app):
    """HTTP client that reports unhandled server errors as real 500 responses."""
    async with Client(sqlite_app):
        transport = ASGITransport(app=sqlite_app.http_app(), raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


async def _seed_events(sqlite_app, times=EVENT_TIMES):
    """Persist one memory.created event per timestamp for the default (no-auth) user."""
    user = await sqlite_app.user_service.get_or_create_user(
        user=UserCreate(
            external_id=settings.DEFAULT_USER_ID,
            name=settings.DEFAULT_USER_NAME,
            email=settings.DEFAULT_USER_EMAIL,
        ),
    )
    for index, created_at in enumerate(times, start=1):
        await sqlite_app.activity_service.activity_repo.save_event(
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


async def _create_memories(client, count, project_ids=None):
    for index in range(count):
        payload = {
            "title": f"Query params memory {index}",
            "content": f"content {index}",
            "context": "query params",
            "keywords": ["query-params"],
            "tags": ["query-params"],
            "importance": 5,
        }
        if project_ids:
            payload["project_ids"] = project_ids
        response = await client.post("/api/v1/memories", json=payload)
        assert response.status_code == 201, response.text


def _hours(body):
    return sorted(event["created_at"][11:16] for event in body["events"])


class TestActivityListMalformedValues:
    @pytest.mark.parametrize(
        "query,param",
        [
            ("since=2099-13-01", "since"),
            ("since=garbage", "since"),
            ("until=garbage", "until"),
            ("until=1999-99-99", "until"),
            ("limit=abc", "limit"),
            ("offset=abc", "offset"),
            ("entity_id=abc", "entity_id"),
        ],
    )
    async def test_malformed_value_is_rejected(self, sqlite_app, client, query, param):
        await _seed_events(sqlite_app)
        response = await client.get(f"/api/v1/activity?{query}")
        assert response.status_code == 400, response.text
        assert param in response.json()["error"]

    async def test_unencoded_plus_in_offset_does_not_return_whole_history(
        self, sqlite_app, client,
    ):
        """A raw '+' arrives as a space; the filter must not be dropped silently."""
        await _seed_events(sqlite_app)
        response = await client.get("/api/v1/activity?since=2099-01-01T00:00:00+00:00")
        assert response.status_code == 400, response.text
        assert "since" in response.json()["error"]

    async def test_properly_encoded_future_since_still_filters(self, sqlite_app, client):
        await _seed_events(sqlite_app)
        for since in ("2099-01-01T00:00:00%2B00:00", "2099-01-01T00:00:00Z"):
            response = await client.get(f"/api/v1/activity?since={since}")
            assert response.status_code == 200, response.text
            assert response.json()["total"] == 0


class TestActivityIntegerBounds:
    async def test_entity_history_rejects_negative_offset(self, client):
        response = await client.get("/api/v1/activity/memory/7?offset=-3")
        assert response.status_code == 400, response.text
        assert "offset" in response.json()["error"]

    @pytest.mark.parametrize("query", ["limit=abc", "offset=abc"])
    async def test_entity_history_rejects_non_integer_pagination(self, client, query):
        response = await client.get(f"/api/v1/activity/memory/7?{query}")
        assert response.status_code == 400, response.text
        assert query.split("=")[0] in response.json()["error"]

    @pytest.mark.parametrize(
        "url,param",
        [
            (f"/api/v1/activity?entity_id={BEYOND_INT64}", "entity_id"),
            (f"/api/v1/activity?offset={BEYOND_INT64}", "offset"),
            (f"/api/v1/activity/memory/1?offset={BEYOND_INT64}", "offset"),
        ],
    )
    async def test_value_beyond_int64_is_rejected_not_a_server_error(
        self, client, url, param,
    ):
        response = await client.get(url)
        assert response.status_code == 400, f"{url} -> {response.status_code} {response.text[:200]}"
        assert param in response.json()["error"]

    async def test_largest_int64_is_accepted(self, client):
        response = await client.get(f"/api/v1/activity?entity_id={BEYOND_INT64 - 1}")
        assert response.status_code == 200, response.text
        assert response.json()["total"] == 0


class TestActivityTimestampsAreUtc:
    async def test_offsets_are_converted_to_utc(self, sqlite_app, client):
        """14:30+02:00 is 12:30Z, so only the 13:00Z and 14:00Z events are 'since' it."""
        await _seed_events(sqlite_app)

        response = await client.get("/api/v1/activity?since=2026-10-18T14:30:00%2B02:00")
        assert response.status_code == 200, response.text
        assert _hours(response.json()) == ["13:00", "14:00"]

        response = await client.get("/api/v1/activity?until=2026-10-18T14:30:00%2B02:00")
        assert response.status_code == 200, response.text
        assert _hours(response.json()) == ["12:00"]

    async def test_naive_values_are_utc_whatever_the_process_timezone(
        self, sqlite_app, client, monkeypatch,
    ):
        await _seed_events(sqlite_app)
        try:
            for zone in ("UTC", "America/New_York", "Asia/Tokyo"):
                monkeypatch.setenv("TZ", zone)
                time.tzset()

                response = await client.get("/api/v1/activity?since=2026-10-18T12:30:00")
                assert response.status_code == 200, response.text
                assert _hours(response.json()) == ["13:00", "14:00"], zone

                response = await client.get("/api/v1/activity?until=2026-10-18T13:30:00")
                assert response.status_code == 200, response.text
                assert _hours(response.json()) == ["12:00", "13:00"], zone
        finally:
            monkeypatch.undo()
            time.tzset()


class TestMemoriesListQueryParams:
    async def test_project_id_zero_filters_instead_of_being_ignored(self, client):
        await _create_memories(client, 3)
        assert (await client.get("/api/v1/memories")).json()["total"] == 3
        assert (await client.get("/api/v1/memories?project_id=99")).json()["total"] == 0

        response = await client.get("/api/v1/memories?project_id=0")
        assert response.status_code == 200, response.text
        assert response.json()["total"] == 0

    async def test_project_id_filter_still_selects_project_memories(self, client):
        project = await client.post(
            "/api/v1/projects",
            json={
                "name": "Query params project",
                "description": "project used to check the project_id filter",
                "project_type": "development",
            },
        )
        assert project.status_code == 201, project.text
        project_id = project.json()["id"]
        await _create_memories(client, 2, project_ids=[project_id])
        await _create_memories(client, 1)

        response = await client.get(f"/api/v1/memories?project_id={project_id}")
        assert response.status_code == 200, response.text
        assert response.json()["total"] == 2

    @pytest.mark.parametrize("name", ["project_id", "offset"])
    @pytest.mark.parametrize("value", [BEYOND_INT64, -BEYOND_INT64 - 1])
    async def test_value_beyond_int64_is_rejected(self, client, name, value):
        response = await client.get(f"/api/v1/memories?{name}={value}")
        assert response.status_code == 400, f"{name}={value} -> {response.status_code}"
        assert name in response.json()["error"]


class TestGraphQueryParams:
    @pytest.mark.parametrize("limit", [0, -1, -2])
    async def test_non_positive_limit_is_rejected(self, client, limit):
        await _create_memories(client, 3)
        response = await client.get(f"/api/v1/graph?limit={limit}")
        assert response.status_code == 400, (
            f"limit={limit} -> {response.status_code} {response.text[:200]}"
        )
        assert "limit" in response.json()["error"]

    async def test_limit_one_pages_to_the_end(self, client):
        await _create_memories(client, 3)
        seen = 0
        for offset in range(3):
            response = await client.get(
                f"/api/v1/graph?node_types=memory&limit=1&offset={offset}",
            )
            assert response.status_code == 200, response.text
            meta = response.json()["meta"]
            seen += meta["memory_count"]
            assert meta["has_more"] is (offset < 2)
        assert seen == 3

    @pytest.mark.parametrize("name", ["project_id", "offset"])
    async def test_value_beyond_int64_is_rejected(self, client, name):
        response = await client.get(f"/api/v1/graph?{name}={BEYOND_INT64}")
        assert response.status_code == 400, f"{name} -> {response.status_code}"
        assert name in response.json()["error"]

    async def test_project_id_zero_still_filters(self, client):
        await _create_memories(client, 2)
        response = await client.get("/api/v1/graph?project_id=0&node_types=memory")
        assert response.status_code == 200, response.text
        assert response.json()["meta"]["memory_count"] == 0

    @pytest.mark.parametrize("depth", [0, -3])
    async def test_memory_subgraph_rejects_depth_below_one(self, client, depth):
        await _create_memories(client, 1)
        memory_id = (await client.get("/api/v1/memories?limit=1")).json()["memories"][0]["id"]
        response = await client.get(f"/api/v1/graph/memory/{memory_id}?depth={depth}")
        assert response.status_code == 400, response.text
        assert "depth" in response.json()["error"]

    async def test_memory_subgraph_accepts_valid_depth(self, client):
        await _create_memories(client, 1)
        memory_id = (await client.get("/api/v1/memories?limit=1")).json()["memories"][0]["id"]
        for depth in (1, 3, 50):
            response = await client.get(f"/api/v1/graph/memory/{memory_id}?depth={depth}")
            assert response.status_code == 200, response.text
