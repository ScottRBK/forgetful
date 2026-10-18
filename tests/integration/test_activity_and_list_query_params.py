"""Integration tests for query-parameter handling on the activity routes.

Covers, without any database:
- the shared strict query parameter helpers (int64 bounds, UTC normalisation),
- the activity routes rejecting malformed values instead of ignoring them and
  handing the services timezone-aware UTC datetimes.
"""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from fastmcp import FastMCP
from starlette.datastructures import QueryParams

from app.models.activity_models import ActivityListResponse
from app.routes.api import activity as activity_routes
from app.routes.api.query_params import (
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
    parse_datetime_param,
    parse_int_param,
)


class TestParseIntParam:
    """parse_int_param is strict and bounded to what the database can store."""

    def test_absent_returns_default(self):
        assert parse_int_param(QueryParams(""), "limit", 20) == 20
        assert parse_int_param(QueryParams(""), "project_id") is None

    def test_parses_integer(self):
        assert parse_int_param(QueryParams("limit=7"), "limit", 20) == 7

    @pytest.mark.parametrize("raw", ["abc", "", "1.5", "0x10"])
    def test_non_integer_raises_naming_parameter(self, raw):
        with pytest.raises(ValueError, match="'offset'"):
            parse_int_param(QueryParams(f"offset={raw}"), "offset", 0)

    @pytest.mark.parametrize("value", [INT64_MAX + 1, INT64_MIN - 1, 10**40])
    def test_outside_int64_raises_naming_parameter(self, value):
        with pytest.raises(ValueError, match="'project_id'"):
            parse_int_param(QueryParams(f"project_id={value}"), "project_id")

    @pytest.mark.parametrize("value", [INT64_MAX, INT64_MIN, 0, -1])
    def test_int64_edges_are_accepted(self, value):
        params = QueryParams(f"project_id={value}")
        assert parse_int_param(params, "project_id") == value

    def test_id_bounds_are_the_postgres_integer_range(self):
        assert INT32_MIN == -2147483648
        assert INT32_MAX == 2147483647
        for value in (INT32_MAX + 1, INT32_MIN - 1):
            with pytest.raises(ValueError, match="'entity_id'"):
                parse_int_param(
                    QueryParams(f"entity_id={value}"),
                    "entity_id",
                    min_value=INT32_MIN,
                    max_value=INT32_MAX,
                )
        for value in (INT32_MAX, INT32_MIN):
            params = QueryParams(f"entity_id={value}")
            assert parse_int_param(
                params, "entity_id", min_value=INT32_MIN, max_value=INT32_MAX,
            ) == value

    def test_custom_bounds(self):
        with pytest.raises(ValueError, match="'limit'"):
            parse_int_param(QueryParams("limit=0"), "limit", 20, min_value=1)
        with pytest.raises(ValueError, match="'limit'"):
            parse_int_param(QueryParams("limit=101"), "limit", 20, max_value=100)


class TestParseDatetimeParam:
    """parse_datetime_param returns UTC-aware datetimes or raises."""

    def test_absent_returns_none(self):
        assert parse_datetime_param(QueryParams(""), "since") is None

    def test_naive_value_is_treated_as_utc(self):
        parsed = parse_datetime_param(QueryParams("since=2026-10-18T12:30:00"), "since")
        assert parsed == datetime(2026, 10, 18, 12, 30, tzinfo=UTC)
        assert parsed.utcoffset() == timedelta(0)

    def test_zulu_suffix_is_utc(self):
        parsed = parse_datetime_param(QueryParams("since=2026-10-18T12:30:00Z"), "since")
        assert parsed == datetime(2026, 10, 18, 12, 30, tzinfo=UTC)

    def test_offset_is_converted_to_utc(self):
        parsed = parse_datetime_param(
            QueryParams("until=2026-10-18T14:30:00%2B02:00"), "until",
        )
        assert parsed == datetime(2026, 10, 18, 12, 30, tzinfo=UTC)
        assert parsed.utcoffset() == timedelta(0)
        assert parsed.tzinfo == UTC

    @pytest.mark.parametrize(
        "raw",
        [
            "garbage",
            "2099-13-01",
            "1999-99-99",
            "",
            # an unencoded '+' reaches the server as a space
            "2099-01-01T00:00:00 00:00",
            # UTC conversion would overflow the datetime range
            "0001-01-01T00:00:00%2B05:00",
        ],
    )
    def test_invalid_value_raises_naming_parameter(self, raw):
        with pytest.raises(ValueError, match="'since'"):
            parse_datetime_param(QueryParams(f"since={raw}"), "since")


class StubActivityService:
    """Records what the routes pass down to the activity service."""

    def __init__(self):
        self.calls = []

    async def get_activity(self, **kwargs):
        self.calls.append(("get_activity", kwargs))
        return ActivityListResponse(
            events=[], total=0, limit=kwargs["limit"], offset=kwargs["offset"],
        )

    async def get_entity_history(self, **kwargs):
        self.calls.append(("get_entity_history", kwargs))
        return ActivityListResponse(
            events=[], total=0, limit=kwargs["limit"], offset=kwargs["offset"],
        )


class StubUserService:
    async def get_or_create_user(self, user):
        return SimpleNamespace(id=uuid4())


@pytest.fixture
def activity_service():
    return StubActivityService()


@pytest.fixture
async def client(activity_service):
    mcp = FastMCP("activity-query-params")
    mcp.user_service = StubUserService()
    mcp.activity_service = activity_service
    activity_routes.register(mcp)
    transport = httpx.ASGITransport(app=mcp.http_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestActivityRoutesValidation:
    """Malformed values are rejected with 400 instead of being ignored."""

    @pytest.mark.parametrize(
        "query,param",
        [
            ("since=2099-13-01", "since"),
            ("since=garbage", "since"),
            ("until=garbage", "until"),
            ("until=1999-99-99", "until"),
            # raw '+' in the offset is decoded to a space by the query parser
            ("since=2099-01-01T00:00:00+00:00", "since"),
            ("limit=abc", "limit"),
            ("offset=abc", "offset"),
            ("entity_id=abc", "entity_id"),
        ],
    )
    async def test_list_rejects_malformed_value(self, client, activity_service, query, param):
        response = await client.get(f"/api/v1/activity?{query}")
        assert response.status_code == 400, response.text
        assert param in response.json()["error"]
        assert activity_service.calls == []

    @pytest.mark.parametrize(
        "query,param",
        [
            ("offset=-1", "offset"),
            ("offset=9223372036854775808", "offset"),
            ("entity_id=2147483648", "entity_id"),
            ("entity_id=-2147483649", "entity_id"),
            ("entity_id=9223372036854775808", "entity_id"),
            ("limit=0", "limit"),
            ("limit=101", "limit"),
        ],
    )
    async def test_list_rejects_out_of_range_value(self, client, activity_service, query, param):
        response = await client.get(f"/api/v1/activity?{query}")
        assert response.status_code == 400, response.text
        assert param in response.json()["error"]
        assert activity_service.calls == []

    @pytest.mark.parametrize(
        "query,param",
        [
            ("offset=-3", "offset"),
            ("offset=abc", "offset"),
            ("offset=9223372036854775808", "offset"),
            ("limit=abc", "limit"),
            ("limit=0", "limit"),
            ("limit=101", "limit"),
        ],
    )
    async def test_entity_history_rejects_bad_pagination(
        self, client, activity_service, query, param,
    ):
        response = await client.get(f"/api/v1/activity/memory/7?{query}")
        assert response.status_code == 400, response.text
        assert param in response.json()["error"]
        assert activity_service.calls == []

    async def test_valid_values_reach_the_service(self, client, activity_service):
        response = await client.get(
            "/api/v1/activity?limit=100&offset=5&entity_id=2147483647",
        )
        assert response.status_code == 200, response.text
        assert activity_service.calls[0][1]["limit"] == 100
        assert activity_service.calls[0][1]["offset"] == 5
        assert activity_service.calls[0][1]["entity_id"] == INT32_MAX

        response = await client.get("/api/v1/activity/memory/7?limit=1&offset=2")
        assert response.status_code == 200, response.text
        assert activity_service.calls[1][1]["offset"] == 2

    async def test_empty_entity_id_still_means_no_filter(self, client, activity_service):
        response = await client.get("/api/v1/activity?entity_id=")
        assert response.status_code == 200, response.text
        assert activity_service.calls[0][1]["entity_id"] is None


class TestActivityRoutesUtcNormalisation:
    """since/until reach the service as UTC, whatever the client or process zone."""

    async def test_naive_values_are_passed_as_utc(self, client, activity_service):
        response = await client.get(
            "/api/v1/activity?since=2026-10-18T12:30:00&until=2026-10-18T13:30:00",
        )
        assert response.status_code == 200, response.text
        kwargs = activity_service.calls[0][1]
        assert kwargs["since"] == datetime(2026, 10, 18, 12, 30, tzinfo=UTC)
        assert kwargs["until"] == datetime(2026, 10, 18, 13, 30, tzinfo=UTC)
        assert kwargs["since"].tzinfo is not None
        assert kwargs["until"].tzinfo is not None

    async def test_offsets_are_converted_to_utc(self, client, activity_service):
        response = await client.get(
            "/api/v1/activity"
            "?since=2026-10-18T14:30:00%2B02:00&until=2026-10-18T07:30:00-05:00",
        )
        assert response.status_code == 200, response.text
        kwargs = activity_service.calls[0][1]
        assert kwargs["since"] == datetime(2026, 10, 18, 12, 30, tzinfo=UTC)
        assert kwargs["until"] == datetime(2026, 10, 18, 12, 30, tzinfo=UTC)
        assert kwargs["since"].utcoffset() == timedelta(0)
        assert kwargs["until"].utcoffset() == timedelta(0)
