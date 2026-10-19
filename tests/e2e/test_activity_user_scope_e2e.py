"""E2E tests for per-user isolation of the PostgreSQL activity log.

The PostgreSQL schema has no row-level security policy, so the activity
repository must scope every read, count and retention delete to the calling
user itself (as the SQLite repository does). Each event snapshot carries the
full entity content, so a missing predicate leaks other users' data.
"""
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.config.settings import settings
from app.models.activity_models import ActionType, ActivityEvent, EntityType
from app.repositories.postgres.activity_repository import PostgresActivityRepository
from app.services.activity_service import ActivityService

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _create_user(db_adapter, user_id: UUID) -> None:
    """Insert a user row (required by the activity_log foreign key)."""
    now = datetime.now(UTC)
    async with db_adapter.system_session() as session:
        await session.execute(
            text(
                "INSERT INTO users (id, external_id, name, email, created_at, updated_at) "
                "VALUES (:id, :external_id, :name, :email, :created_at, :updated_at)",
            ),
            {
                "id": str(user_id),
                "external_id": f"ext-{user_id}",
                "name": f"user-{user_id}",
                "email": f"{user_id}@example.com",
                "created_at": now,
                "updated_at": now,
            },
        )


def _event(
    entity_id: int,
    secret: str,
    created_at: datetime | None = None,
) -> ActivityEvent:
    kwargs = {"created_at": created_at} if created_at is not None else {}
    return ActivityEvent(
        entity_type=EntityType.MEMORY,
        entity_id=entity_id,
        action=ActionType.CREATED,
        snapshot={"title": secret, "content": secret},
        **kwargs,
    )


@pytest_asyncio.fixture(loop_scope="session")
async def two_users(db_adapter):
    """Two distinct users that each own rows in the shared activity log."""
    user_a, user_b = uuid4(), uuid4()
    await _create_user(db_adapter, user_a)
    await _create_user(db_adapter, user_b)
    return user_a, user_b


@pytest.fixture
def activity_repo(db_adapter):
    return PostgresActivityRepository(db_adapter)


@pytest.mark.e2e
class TestPostgresActivityUserScope:
    """Activity queries and retention cleanup only ever touch the caller's rows."""

    async def test_query_events_returns_only_callers_events(self, activity_repo, two_users):
        user_a, user_b = two_users
        await activity_repo.save_event(user_a, _event(1, "ALICE-SECRET"))
        await activity_repo.save_event(user_b, _event(2, "BOB-SECRET"))
        await activity_repo.save_event(user_b, _event(3, "BOB-SECRET-2"))

        events_a, total_a = await activity_repo.query_events(user_a)
        events_b, total_b = await activity_repo.query_events(user_b)

        assert total_a == 1
        assert [e.user_id for e in events_a] == [str(user_a)]
        assert [e.snapshot["title"] for e in events_a] == ["ALICE-SECRET"]
        assert total_b == 2
        assert {e.user_id for e in events_b} == {str(user_b)}

    async def test_query_events_entity_filter_cannot_reach_other_users_rows(
        self, activity_repo, two_users,
    ):
        user_a, user_b = two_users
        await activity_repo.save_event(user_b, _event(42, "BOB-SECRET"))

        events, total = await activity_repo.query_events(user_a, entity_id=42)

        assert events == []
        assert total == 0

    async def test_count_events_counts_only_callers_events(self, activity_repo, two_users):
        user_a, user_b = two_users
        await activity_repo.save_event(user_a, _event(1, "ALICE-SECRET"))
        await activity_repo.save_event(user_b, _event(2, "BOB-SECRET"))
        await activity_repo.save_event(user_b, _event(3, "BOB-SECRET-2"))

        assert await activity_repo.count_events(user_a) == 1
        assert await activity_repo.count_events(
            user_a, entity_type=EntityType.MEMORY, action=ActionType.CREATED,
        ) == 1
        assert await activity_repo.count_events(user_b) == 2

    async def test_cleanup_expired_only_deletes_callers_events(self, activity_repo, two_users):
        user_a, user_b = two_users
        old = datetime.now(UTC) - timedelta(days=60)
        await activity_repo.save_event(user_a, _event(1, "ALICE-OLD", created_at=old))
        await activity_repo.save_event(user_b, _event(2, "BOB-OLD", created_at=old))
        await activity_repo.save_event(user_b, _event(3, "BOB-OLD-2", created_at=old))

        deleted = await activity_repo.cleanup_expired(user_a, retention_days=30)

        assert deleted == 1
        _, total_a = await activity_repo.query_events(user_a)
        _, total_b = await activity_repo.query_events(user_b)
        assert total_a == 0
        assert total_b == 2

    async def test_cleanup_expired_with_no_own_events_deletes_nothing(
        self, activity_repo, two_users,
    ):
        user_a, user_b = two_users
        old = datetime.now(UTC) - timedelta(days=60)
        await activity_repo.save_event(user_b, _event(10, "BOB-OLD", created_at=old))

        deleted = await activity_repo.cleanup_expired(user_a, retention_days=30)

        assert deleted == 0
        _, total_b = await activity_repo.query_events(user_b, entity_id=10)
        assert total_b == 1

    async def test_service_lazy_retention_cleanup_is_user_scoped(
        self, activity_repo, two_users, monkeypatch,
    ):
        """ActivityService.get_activity runs the lazy cleanup for the caller only."""
        monkeypatch.setattr(settings, "ACTIVITY_RETENTION_DAYS", 30)
        user_a, user_b = two_users
        old = datetime.now(UTC) - timedelta(days=60)
        await activity_repo.save_event(user_a, _event(1, "ALICE-RECENT"))
        await activity_repo.save_event(user_a, _event(2, "ALICE-RECENT-2"))
        await activity_repo.save_event(user_b, _event(3, "BOB-OLD", created_at=old))
        service = ActivityService(activity_repo)

        response = await service.get_activity(user_a)

        assert response.total == 2
        assert {e.user_id for e in response.events} == {str(user_a)}
        assert await service.count_activity(user_a) == 2
        # Bob's expired event must survive Alice's request (and only be his to count).
        bob_events, bob_total = await activity_repo.query_events(user_b, entity_id=3)
        assert bob_total == 1
        assert [e.snapshot["title"] for e in bob_events] == ["BOB-OLD"]
        assert await service.count_activity(user_b) == 1
