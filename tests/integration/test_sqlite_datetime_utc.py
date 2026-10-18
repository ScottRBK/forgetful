"""SQLite timestamp columns bind and return timezone-aware UTC datetimes.

SQLite has no timezone-aware type: SQLAlchemy stores `DateTime(timezone=True)` as
naive wall-clock text and returns naive datetimes. `UTCDateTime` normalises values
to UTC on the way in and re-attaches UTC on the way out, so SQLite behaves like
PostgreSQL `timestamptz`.
"""
from datetime import UTC, datetime, timedelta, timezone

import pytest
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    Table,
    create_engine,
    select,
    text,
)

from app.repositories.sqlite.sqlite_tables import Base, UTCDateTime

PLUS_TWO = timezone(timedelta(hours=2))
MINUS_FIVE = timezone(timedelta(hours=-5))

_metadata = MetaData()
_events = Table(
    "datetime_utc_probe",
    _metadata,
    Column("id", Integer, primary_key=True),
    Column("at", UTCDateTime(), nullable=True),
)


@pytest.fixture
def engine():
    engine = create_engine("sqlite://")
    _metadata.create_all(engine)
    yield engine
    engine.dispose()


def _store(engine, value):
    with engine.begin() as conn:
        conn.execute(_events.insert().values(id=1, at=value))


def _stored_text(engine):
    with engine.connect() as conn:
        return conn.execute(text("SELECT at FROM datetime_utc_probe")).scalar()


def _read(engine):
    with engine.connect() as conn:
        return conn.execute(select(_events.c.at)).scalar()


@pytest.mark.parametrize(
    ("value", "expected_utc"),
    [
        (datetime(2026, 1, 1, 8, 30, tzinfo=UTC), datetime(2026, 1, 1, 8, 30, tzinfo=UTC)),
        (datetime(2026, 1, 1, 10, 30, tzinfo=PLUS_TWO), datetime(2026, 1, 1, 8, 30, tzinfo=UTC)),
        (datetime(2026, 1, 1, 3, 30, tzinfo=MINUS_FIVE), datetime(2026, 1, 1, 8, 30, tzinfo=UTC)),
        # Naive input was always compared as UTC wall-clock text; that is preserved.
        (datetime(2026, 1, 1, 8, 30), datetime(2026, 1, 1, 8, 30, tzinfo=UTC)),
    ],
)
def test_round_trip_returns_aware_utc(engine, value, expected_utc):
    """Any accepted input comes back as the same instant, tz-aware, in UTC."""
    _store(engine, value)

    result = _read(engine)

    assert result == expected_utc
    assert result.tzinfo is not None
    assert result.utcoffset() == timedelta(0)


def test_non_utc_offset_is_converted_before_storing(engine):
    """The stored text is the UTC wall clock, not the caller's local wall clock."""
    _store(engine, datetime(2026, 1, 1, 10, 30, tzinfo=PLUS_TWO))

    assert _stored_text(engine).startswith("2026-01-01 08:30:00")


def test_null_round_trips_as_none(engine):
    _store(engine, None)

    assert _read(engine) is None


def test_comparison_values_are_normalised_to_utc(engine):
    """Bind values in WHERE clauses are converted too (offset must not be dropped)."""
    _store(engine, datetime(2026, 1, 1, 8, 30, tzinfo=UTC))
    # 10:00+02:00 == 08:00Z, which is before the stored 08:30Z.
    since = datetime(2026, 1, 1, 10, 0, tzinfo=PLUS_TWO)

    with engine.connect() as conn:
        after = conn.execute(select(_events.c.id).where(_events.c.at >= since)).all()
        before = conn.execute(select(_events.c.id).where(_events.c.at <= since)).all()

    assert after == [(1,)]
    assert before == []


def test_every_sqlite_timestamp_column_is_utc_aware():
    """A plain DateTime column would silently reintroduce naive reads."""
    columns = [column for table in Base.metadata.tables.values() for column in table.columns]
    plain = [column for column in columns if isinstance(column.type, DateTime)]
    aware = [column for column in columns if isinstance(column.type, UTCDateTime)]

    assert [f"{column.table.name}.{column.name}" for column in plain] == []
    assert len(aware) > 0
