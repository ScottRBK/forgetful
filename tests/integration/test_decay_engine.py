"""Unit tests for the usage-aware memory decay engine (forgetful-hulkito fork).

Covers the pure decay math in `MemoryService._propose_action` and the
`_usage_weighted_delta` / `_is_protected` / `_effective_access_date` helpers,
plus end-to-end `run_decay_scan` behaviour against the in-memory repository
fixture (no Postgres/SQLite dependency).

Risk class: schema + lifecycle mutation. Verifies:
- protected tags / importance are never decayed
- null confidence is reported as a skip, not silently decayed
- boundary ages (89/90/180+ days) behave correctly
- usage weighting shrinks the delta as access_count grows
- `updated_at` is NOT mutated by `record_memory_access`
- dry-run proposes but does not apply; live mode applies via the validated
  `update_memory` / `mark_memory_obsolete` paths
"""
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.models.memory_models import (
    DecayScanRequest,
    Memory,
    MemoryCreate,
    MemoryUpdate,
)
from app.services.memory_service import MemoryService


def _make_memory(
    *,
    id_: int = 1,
    title: str = "stub",
    importance: int = 5,
    tags: list[str] | None = None,
    confidence: float | None = 0.8,
    age_days: int = 0,
    last_accessed_days_ago: int | None = None,
    access_count: int = 0,
    now: datetime | None = None,
) -> Memory:
    # Shared clock avoids flaky .days truncation when the test captures now
    # a few microseconds before _make_memory's own datetime.now(UTC).
    now = now or datetime.now(UTC)
    created = now - timedelta(days=age_days)
    last_access = (
        now - timedelta(days=last_accessed_days_ago) if last_accessed_days_ago is not None else None
    )
    return Memory(
        id=id_,
        title=title,
        content="stub content",
        context="stub context",
        keywords=["stub"],
        tags=tags or ["stub"],
        importance=importance,
        confidence=confidence,
        access_count=access_count,
        last_accessed_at=last_access,
        created_at=created,
        updated_at=created,  # not touched since creation
        project_ids=[],
        linked_memory_ids=[],
    )


# ---------------------------------------------------------------------------
# Pure-formula unit tests
# ---------------------------------------------------------------------------


def test_protected_by_importance_is_skipped():
    mem = _make_memory(importance=8, confidence=0.9, age_days=400)
    action = MemoryService._propose_action(memory=mem, now=datetime.now(UTC))
    assert action.kind == "skip"
    assert "protected" in (action.reason or "")


def test_protected_by_tag_is_skipped():
    for tag in ("decision", "architecture", "critical"):
        mem = _make_memory(importance=3, tags=[tag], confidence=0.9, age_days=400)
        action = MemoryService._propose_action(memory=mem, now=datetime.now(UTC))
        assert action.kind == "skip", f"tag {tag} should be protected"
        assert "protected" in (action.reason or "")


def test_null_confidence_is_skipped_with_reason():
    mem = _make_memory(confidence=None, age_days=400)
    action = MemoryService._propose_action(memory=mem, now=datetime.now(UTC))
    assert action.kind == "skip"
    assert "confidence is None" in (action.reason or "")


def test_recent_memory_is_skipped():
    mem = _make_memory(confidence=0.8, age_days=30)
    action = MemoryService._propose_action(memory=mem, now=datetime.now(UTC))
    assert action.kind == "skip"
    assert "age" in (action.reason or "")


def test_boundary_age_90_days_decays():
    # 91 days old, confidence above floor -> decay
    mem = _make_memory(confidence=0.8, age_days=91, access_count=0)
    action = MemoryService._propose_action(memory=mem, now=datetime.now(UTC))
    assert action.kind == "decay"
    assert action.delta is not None
    assert action.proposed_confidence is not None
    assert action.proposed_confidence < 0.8


def test_boundary_age_89_days_skipped():
    mem = _make_memory(confidence=0.8, age_days=89, access_count=0)
    action = MemoryService._propose_action(memory=mem, now=datetime.now(UTC))
    assert action.kind == "skip"


def test_decay_clamped_at_floor():
    # confidence exactly at floor: proposed = max(0.3, 0.3 - 0.1) = 0.3,
    # which is NOT lower than current -> skip (clamped).
    mem = _make_memory(confidence=0.3, age_days=120, access_count=0)
    action = MemoryService._propose_action(memory=mem, now=datetime.now(UTC))
    assert action.kind == "skip"
    assert "clamped" in (action.reason or "")


def test_decay_just_above_floor_decays_to_floor():
    # confidence 0.31 -> proposed 0.30 (clamped), still lower than 0.31 -> decay.
    mem = _make_memory(confidence=0.31, age_days=120, access_count=0)
    action = MemoryService._propose_action(memory=mem, now=datetime.now(UTC))
    assert action.kind == "decay"
    assert action.proposed_confidence == pytest.approx(0.3)


def test_obsolete_path_when_very_old_and_low_confidence():
    mem = _make_memory(confidence=0.2, age_days=200, access_count=0)
    action = MemoryService._propose_action(memory=mem, now=datetime.now(UTC))
    assert action.kind == "obsolete"
    assert "aged out" in (action.reason or "")


def test_usage_weighting_shrinks_delta():
    # access_count=0 -> delta 0.1
    assert MemoryService._usage_weighted_delta(0) == pytest.approx(0.1)
    # access_count=5 -> delta 0.1 - 5*0.01 = 0.05
    assert MemoryService._usage_weighted_delta(5) == pytest.approx(0.05)
    # access_count=8 -> delta 0.1 - 8*0.01 = 0.02 (floor)
    assert MemoryService._usage_weighted_delta(8) == pytest.approx(0.02)
    # access_count=20 (above cap) -> still 0.02 (cap at 8)
    assert MemoryService._usage_weighted_delta(20) == pytest.approx(0.02)


def test_effective_access_date_fallback_chain():
    now = datetime.now(UTC)
    # last_accessed_at wins (shared now so timedelta.days is exact, not 9 vs 10)
    mem = _make_memory(age_days=200, last_accessed_days_ago=10, now=now)
    eff = MemoryService._effective_access_date(mem)
    assert (now - eff).days == 10
    # updated_at fallback when last_accessed_at is None
    mem2 = _make_memory(age_days=200, last_accessed_days_ago=None, now=now)
    eff2 = MemoryService._effective_access_date(mem2)
    assert eff2 == MemoryService._as_utc(mem2.updated_at)


def test_propose_action_accepts_naive_sqlite_datetimes():
    """Live SQLite rows often return naive created_at/updated_at; must not TypeError."""
    naive_created = datetime(2025, 1, 1, 12, 0, 0)  # no tzinfo
    mem = Memory.model_construct(
        id=99,
        title="naive-stub",
        content="stub",
        context="stub",
        keywords=["stub"],
        tags=["stub"],
        importance=5,
        confidence=0.8,
        access_count=0,
        last_accessed_at=None,
        created_at=naive_created,
        updated_at=naive_created,
        project_ids=[],
        linked_memory_ids=[],
    )
    action = MemoryService._propose_action(memory=mem, now=datetime.now(UTC))
    assert action.age_days is not None
    assert action.age_days >= 200


# ---------------------------------------------------------------------------
# Integration tests against the in-memory repo fixture
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_memory_access_does_not_mutate_updated_at(test_memory_service):
    """Access tracking must update access_count + last_accessed_at but NOT updated_at."""
    user_id = uuid4()
    mem_data = MemoryCreate(
        title="Decay stub",
        content="Memory used to test access tracking",
        context="Verifying updated_at is preserved",
        keywords=["decay", "test"],
        tags=["stub"],
        importance=5,
    )
    mem, _ = await test_memory_service.create_memory(user_id=user_id, memory_data=mem_data)
    updated_at_before = mem.updated_at

    # Use the repo directly to bypass any service-level touches
    count = await test_memory_service.memory_repo.record_memory_access(
        user_id=user_id,
        memory_ids=[mem.id],
    )
    assert count == 1

    refreshed = await test_memory_service.memory_repo.get_memory_by_id(user_id=user_id, memory_id=mem.id)
    assert refreshed is not None
    assert refreshed.access_count == 1
    assert refreshed.last_accessed_at is not None
    assert refreshed.updated_at == updated_at_before, "updated_at must not move on access"


@pytest.mark.asyncio
async def test_get_memory_records_access(test_memory_service):
    """get_memory should bump access_count via the service path."""
    user_id = uuid4()
    mem_data = MemoryCreate(
        title="Get stub",
        content="Memory used to test get_memory access tracking",
        context="Verifying get_memory bumps access_count",
        keywords=["decay", "get"],
        tags=["stub"],
        importance=5,
    )
    mem, _ = await test_memory_service.create_memory(user_id=user_id, memory_data=mem_data)

    await test_memory_service.get_memory(user_id=user_id, memory_id=mem.id)
    refreshed = await test_memory_service.memory_repo.get_memory_by_id(user_id=user_id, memory_id=mem.id)
    assert refreshed is not None
    assert refreshed.access_count == 1
    assert refreshed.last_accessed_at is not None


@pytest.mark.asyncio
async def test_run_decay_scan_dry_run_does_not_write(test_memory_service):
    """Dry-run must propose without applying."""
    user_id = uuid4()
    now = datetime.now(UTC)
    old_ts = now - timedelta(days=200)
    mem = Memory(
        id=1001,
        title="Old stub",
        content="Memory that should be a decay candidate",
        context="Decay scan dry-run test",
        keywords=["decay"],
        tags=["stub"],
        importance=5,
        confidence=0.8,
        access_count=0,
        last_accessed_at=None,
        created_at=old_ts,
        updated_at=old_ts,
        project_ids=[],
        linked_memory_ids=[],
    )
    repo = test_memory_service.memory_repo
    repo._memories.setdefault(user_id, {})[mem.id] = mem

    response = await test_memory_service.run_decay_scan(
        user_id=user_id,
        request=DecayScanRequest(memory_ids=[mem.id], dry_run=True),
    )
    assert response.dry_run is True
    assert response.scanned == 1
    assert response.applied == 0
    assert any(a.kind == "decay" for a in response.actions)

    # Memory confidence unchanged
    refreshed = await repo.get_memory_by_id(user_id=user_id, memory_id=mem.id)
    assert refreshed is not None
    assert refreshed.confidence == 0.8


@pytest.mark.asyncio
async def test_run_decay_scan_live_applies_confidence_decay(test_memory_service):
    """Live mode applies confidence decay through the validated update path."""
    user_id = uuid4()
    old_ts = datetime.now(UTC) - timedelta(days=200)
    mem = Memory(
        id=1002,
        title="Old stub live",
        content="Memory that should be decayed in live mode",
        context="Decay scan live test",
        keywords=["decay"],
        tags=["stub"],
        importance=5,
        confidence=0.8,
        access_count=0,
        last_accessed_at=None,
        created_at=old_ts,
        updated_at=old_ts,
        project_ids=[],
        linked_memory_ids=[],
    )
    repo = test_memory_service.memory_repo
    repo._memories.setdefault(user_id, {})[mem.id] = mem

    response = await test_memory_service.run_decay_scan(
        user_id=user_id,
        request=DecayScanRequest(memory_ids=[mem.id], dry_run=False),
    )
    assert response.dry_run is False
    assert response.applied == 1
    assert any(a.kind == "decay" for a in response.actions)

    refreshed = await repo.get_memory_by_id(user_id=user_id, memory_id=mem.id)
    assert refreshed is not None
    assert refreshed.confidence is not None
    assert refreshed.confidence < 0.8


@pytest.mark.asyncio
async def test_run_decay_scan_live_obsolete_path(test_memory_service):
    """Live mode applies obsolescence when the obsolete path is selected."""
    user_id = uuid4()
    old_ts = datetime.now(UTC) - timedelta(days=400)
    mem = Memory(
        id=1003,
        title="Very old low-confidence stub",
        content="Memory that should be marked obsolete",
        context="Decay scan obsolete test",
        keywords=["decay"],
        tags=["stub"],
        importance=5,
        confidence=0.2,
        access_count=0,
        last_accessed_at=None,
        created_at=old_ts,
        updated_at=old_ts,
        project_ids=[],
        linked_memory_ids=[],
    )
    repo = test_memory_service.memory_repo
    repo._memories.setdefault(user_id, {})[mem.id] = mem

    response = await test_memory_service.run_decay_scan(
        user_id=user_id,
        request=DecayScanRequest(memory_ids=[mem.id], dry_run=False),
    )
    assert response.dry_run is False
    assert response.applied == 1
    assert any(a.kind == "obsolete" for a in response.actions)

    refreshed = await repo.get_memory_by_id(user_id=user_id, memory_id=mem.id)
    assert refreshed is not None
    assert refreshed.is_obsolete is True
    assert refreshed.obsolete_reason is not None
