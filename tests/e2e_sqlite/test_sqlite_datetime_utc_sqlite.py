"""E2E tests: SQLite returns timezone-aware UTC timestamps and honours UTC offsets.

Uses in-memory SQLite for test isolation.

- Timestamps read back from SQLite must carry a UTC offset, exactly like the value
  returned by the create call and like PostgreSQL `timestamptz`.
- `since` / `until` on /api/v1/activity must compare instants, not wall-clock digits,
  when the caller passes a non-UTC offset.
"""
from datetime import UTC, datetime, timedelta, timezone

import pytest

from app.config.settings import settings
from app.models.activity_models import ActionType, ActivityEvent, EntityType
from app.models.project_models import ProjectCreate, ProjectType, ProjectUpdate
from app.models.user_models import UserCreate

EVENT_TIME = datetime(2026, 1, 1, 8, 30, 0, tzinfo=UTC)

RESOURCES = {
    "projects": {
        "name": "UTC project",
        "description": "Timestamp check",
        "project_type": "development",
    },
    "documents": {
        "title": "UTC document",
        "description": "Timestamp check",
        "content": "Document content with enough text.",
        "document_type": "analysis",
    },
    "entities": {
        "name": "UTC entity",
        "entity_type": "Organization",
        "notes": "Timestamp check",
    },
    "code-artifacts": {
        "title": "UTC artifact",
        "description": "Timestamp check",
        "code": "print('utc')",
        "language": "python",
    },
    "memories": {
        "title": "UTC memory",
        "content": "Timestamp check content.",
        "context": "Timestamp check",
        "keywords": ["utc"],
        "tags": ["utc"],
        "importance": 7,
    },
    "skills": {
        "name": "utc-skill",
        "description": "Timestamp check",
        "content": "# UTC\n\nSteps here.",
        "tags": ["utc"],
        "importance": 7,
    },
}


@pytest.fixture
async def app(http_client, sqlite_app):
    """The FastMCP app with its lifespan running, so the services are attached."""
    return sqlite_app


def _parse_aware(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None, f"timestamp has no UTC offset: {value}"
    assert parsed.utcoffset() == timedelta(0), value
    return parsed


class TestTimestampsAreAwareUtc:
    """Every read path returns the same aware UTC value that create returned."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("resource", sorted(RESOURCES))
    async def test_get_matches_create(self, http_client, resource):
        created = await http_client.post(f"/api/v1/{resource}", json=RESOURCES[resource])
        assert created.status_code == 201
        body = created.json()

        fetched = await http_client.get(f"/api/v1/{resource}/{body['id']}")
        assert fetched.status_code == 200
        data = fetched.json()

        for field in ("created_at", "updated_at"):
            read_back = _parse_aware(data[field])
            # Memory creation returns a result summary without timestamps.
            if field in body:
                assert read_back == _parse_aware(body[field])

    @pytest.mark.asyncio
    async def test_project_list_and_update_are_aware(self, http_client):
        created = await http_client.post("/api/v1/projects", json=RESOURCES["projects"])
        project_id = created.json()["id"]

        updated = await http_client.put(f"/api/v1/projects/{project_id}", json={"name": "Renamed"})
        assert updated.status_code == 200
        listed = await http_client.get("/api/v1/projects")
        assert listed.status_code == 200

        _parse_aware(updated.json()["updated_at"])
        for project in listed.json()["projects"]:
            _parse_aware(project["created_at"])
            _parse_aware(project["updated_at"])

    @pytest.mark.asyncio
    async def test_service_results_are_aware(self, app):
        """Same check one layer down, on the model objects the services return."""
        user = await app.user_service.get_or_create_user(
            user=UserCreate(
                external_id=settings.DEFAULT_USER_ID,
                name=settings.DEFAULT_USER_NAME,
                email=settings.DEFAULT_USER_EMAIL,
            ),
        )
        service = app.project_service
        created = await service.create_project(
            user.id,
            ProjectCreate(name="p", description="d", project_type=ProjectType.DEVELOPMENT),
        )
        fetched = await service.get_project(user.id, created.id)
        updated = await service.update_project(user.id, created.id, ProjectUpdate(name="p2"))
        listed = (await service.list_projects(user.id))[0]

        for value in (
            created.created_at,
            fetched.created_at,
            fetched.updated_at,
            updated.updated_at,
            listed.updated_at,
        ):
            assert value.utcoffset() == timedelta(0)
        assert fetched.created_at == created.created_at
        assert updated.model_dump(mode="json")["updated_at"].endswith(("Z", "+00:00"))


class TestActivityWindowHonoursOffsets:
    """GET /api/v1/activity since/until compare instants, whatever the offset."""

    @staticmethod
    async def _seed(app):
        user = await app.user_service.get_or_create_user(
            user=UserCreate(
                external_id=settings.DEFAULT_USER_ID,
                name=settings.DEFAULT_USER_NAME,
                email=settings.DEFAULT_USER_EMAIL,
            ),
        )
        event = ActivityEvent(
            entity_type=EntityType.MEMORY,
            entity_id=1,
            action=ActionType.CREATED,
            snapshot={"title": "x"},
            created_at=EVENT_TIME,
        )
        await app.activity_service.activity_repo.save_event(user.id, event)
        return user

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("param", "value", "expected_total"),
        [
            # 08:00Z: the 08:30Z event is after it
            ("since", "2026-01-01T08:00:00Z", 1),
            ("until", "2026-01-01T08:00:00Z", 0),
            ("since", "2026-01-01T10:00:00+02:00", 1),
            ("until", "2026-01-01T10:00:00+02:00", 0),
            # 09:00Z: the 08:30Z event is before it
            ("until", "2026-01-01T04:00:00-05:00", 1),
            ("since", "2026-01-01T04:00:00-05:00", 0),
        ],
    )
    async def test_http_offsets(self, http_client, app, param, value, expected_total):
        await self._seed(app)

        response = await http_client.get("/api/v1/activity", params={param: value})

        assert response.status_code == 200
        assert response.json()["total"] == expected_total

    @pytest.mark.asyncio
    async def test_repository_aware_non_utc_and_naive_bounds(self, app):
        user = await self._seed(app)
        repo = app.activity_service.activity_repo
        plus_two = timezone(timedelta(hours=2))

        _, since_total = await repo.query_events(
            user_id=user.id, since=datetime(2026, 1, 1, 10, 0, tzinfo=plus_two),
        )
        _, until_total = await repo.query_events(
            user_id=user.id, until=datetime(2026, 1, 1, 10, 0, tzinfo=plus_two),
        )
        # Naive bounds keep meaning "UTC wall clock".
        _, naive_since_total = await repo.query_events(
            user_id=user.id, since=datetime(2026, 1, 1, 8, 0),
        )
        _, naive_until_total = await repo.query_events(
            user_id=user.id, until=datetime(2026, 1, 1, 8, 0),
        )

        assert (since_total, until_total) == (1, 0)
        assert (naive_since_total, naive_until_total) == (1, 0)

    @pytest.mark.asyncio
    async def test_stored_events_come_back_aware(self, app):
        user = await self._seed(app)

        events, _ = await app.activity_service.activity_repo.query_events(user_id=user.id)

        assert events[0].created_at == EVENT_TIME
        assert events[0].created_at.utcoffset() == timedelta(0)
