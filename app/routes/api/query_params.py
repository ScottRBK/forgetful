"""Strict query-parameter parsing shared by the REST list routes.

Both helpers raise ``ValueError`` (with a message naming the parameter) for a
value that is present but unusable, so routes can answer 400 instead of silently
falling back to a default or dropping a filter.
"""

from datetime import UTC, datetime
from typing import Any, overload

# Range of a signed 64-bit integer: the widest value SQLite and PostgreSQL
# (BIGINT) can bind, used for pagination bounds. Python ints are unbounded, so anything outside this range
# would otherwise surface as an OverflowError / DataError (HTTP 500).
INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1

# Range of a signed 32-bit integer. Row ids (``entity_id``, ``project_id``) are
# INTEGER columns on PostgreSQL, so an id above this range is rejected by
# asyncpg (DataError, HTTP 500) even though SQLite would bind it. ``limit`` and
# ``offset`` are only bound as LIMIT/OFFSET (BIGINT) and keep the int64 range.
INT32_MIN = -(2**31)
INT32_MAX = 2**31 - 1


@overload
def parse_int_param(
    params: Any,
    name: str,
    default: int,
    *,
    min_value: int = ...,
    max_value: int = ...,
) -> int: ...


@overload
def parse_int_param(
    params: Any,
    name: str,
    default: None = None,
    *,
    min_value: int = ...,
    max_value: int = ...,
) -> int | None: ...


def parse_int_param(
    params: Any,
    name: str,
    default: int | None = None,
    *,
    min_value: int = INT64_MIN,
    max_value: int = INT64_MAX,
) -> int | None:
    """Parse an integer query parameter with strict validation.

    Args:
        params: Query params object
        name: Parameter name
        default: Value returned when the parameter is absent
        min_value: Smallest accepted value (defaults to the int64 minimum)
        max_value: Largest accepted value (defaults to the int64 maximum)

    Returns:
        Parsed integer, or ``default`` when the parameter is absent

    Raises:
        ValueError: If the value is not an integer or is outside the bounds
    """
    raw = params.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid value for '{name}': must be an integer") from None
    if not min_value <= value <= max_value:
        raise ValueError(
            f"Invalid value for '{name}': must be between {min_value} and {max_value}",
        )
    return value


def parse_datetime_param(params: Any, name: str) -> datetime | None:
    """Parse an ISO 8601 query parameter into a UTC-aware datetime.

    A value without an offset is taken as UTC (the timezone events are stored
    in); a value with an offset is converted to UTC. Returning an aware UTC
    datetime keeps the comparison independent of the server process timezone.

    Args:
        params: Query params object
        name: Parameter name

    Returns:
        UTC datetime, or None when the parameter is absent

    Raises:
        ValueError: If the value is not a valid ISO 8601 timestamp
    """
    raw = params.get(name)
    if raw is None:
        return None
    try:
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    except (ValueError, OverflowError):
        raise ValueError(
            f"Invalid value for '{name}': must be an ISO 8601 timestamp "
            "(encode '+' in a UTC offset as %2B)",
        ) from None
