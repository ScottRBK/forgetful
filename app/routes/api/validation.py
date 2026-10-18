"""Shared request validation helpers for the REST API routes.

Keeps the way routes report invalid input (400 responses) and the bounds they
enforce on client supplied integers in one place.
"""
from typing import Any

from pydantic import ValidationError
from starlette.responses import JSONResponse

# Database integer columns are signed 64-bit; larger values are rejected by the
# driver (OverflowError on SQLite, DataError on PostgreSQL) and would surface as 500s.
INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1


def validation_error_response(error: ValidationError) -> JSONResponse:
    """Build the 400 response for a pydantic ``ValidationError``.

    ``ValidationError.errors()`` is not safe to hand to ``JSONResponse`` as is:
    errors raised by custom validators carry the exception object in ``ctx`` and
    non-finite floats (``NaN``/``Infinity``, accepted by ``json.loads``) are echoed in
    ``input``; both make JSON rendering raise and the client get a 500 instead.
    Only the documented ``type``, ``loc`` and ``msg`` keys are returned.
    """
    return JSONResponse(
        {
            "error": error.errors(
                include_url=False,
                include_context=False,
                include_input=False,
            ),
        },
        status_code=400,
    )


def parse_int_param(params: Any, name: str, default: int | None = None) -> int | None:
    """Parse integer query parameter with strict validation.

    Args:
        params: Query parameters object
        name: Parameter name to extract
        default: Default value if parameter not provided

    Returns:
        Parsed integer value or default

    Raises:
        ValueError: If value is not a valid integer or does not fit in 64 bits
    """
    raw = params.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid value for '{name}': must be an integer") from None
    if not INT64_MIN <= value <= INT64_MAX:
        raise ValueError(f"Invalid value for '{name}': out of range")
    return value


def parse_int_query(raw: str, name: str) -> int:
    """Parse the text of an integer query parameter.

    Raises:
        ValueError: With a client-facing message if the text is not an integer
            or the integer does not fit in 64 bits
    """
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"Invalid {name}: {raw}. Must be an integer.") from None
    if not INT64_MIN <= value <= INT64_MAX:
        raise ValueError(f"Invalid {name}: {raw}. Value is out of range.")
    return value


def parse_optional_int_query(params: Any, name: str) -> int | None:
    """Parse an optional integer query parameter; missing or empty means ``None``.

    Raises:
        ValueError: As for ``parse_int_query``
    """
    raw = params.get(name)
    if not raw:
        return None
    return parse_int_query(raw, name)


def validate_body_id(value: Any, name: str) -> int:
    """Validate an identifier taken from a JSON request body.

    JSON permits any value type and arbitrarily large integers; anything that is not
    an integer fitting in 64 bits would otherwise reach the database driver and fail
    there with a 500.

    Raises:
        ValueError: With a client-facing message if the value is not a valid id
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if not INT64_MIN <= value <= INT64_MAX:
        raise ValueError(f"{name} is out of range")
    return value
