"""Shared request parsing for REST handlers.

Malformed client input (non-numeric or out-of-range ids, invalid or non-object
JSON bodies, ints that cannot be stored) must produce a 4xx JSON error rather
than an unhandled exception, which Starlette reports as a 500.

Handlers raise ``RequestError`` through these helpers and are wrapped with
``handle_request_errors`` below the ``custom_route`` decorator.
"""
import functools
import re
from collections.abc import Awaitable, Callable
from enum import Enum
from typing import Any

from starlette.datastructures import QueryParams
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# Primary keys are 32-bit on PostgreSQL (SQLite integers are wider), so no stored
# row can have a larger id; values beyond this overflow the database driver.
MAX_ID = 2**31 - 1
MIN_INT = -(2**31)

_ID_PATTERN = re.compile(r"[0-9]+")
_MAX_ID_DIGITS = len(str(MAX_ID))


class RequestError(Exception):
    """A client error that is reported as a JSON ``{"error": message}`` response."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def handle_request_errors(
    handler: Callable[[Request], Awaitable[Response]],
) -> Callable[[Request], Awaitable[Response]]:
    """Turn a ``RequestError`` raised inside a handler into its JSON error response."""

    @functools.wraps(handler)
    async def wrapper(request: Request) -> Response:
        try:
            return await handler(request)
        except RequestError as e:
            return JSONResponse({"error": e.message}, status_code=e.status_code)

    return wrapper


def path_id(request: Request, name: str) -> int:
    """Return a path parameter as an id, or raise a 404 if it can never name a resource."""
    raw = request.path_params[name]
    # The length check keeps int() away from absurdly long digit strings.
    if not _ID_PATTERN.fullmatch(raw) or len(raw) > _MAX_ID_DIGITS or int(raw) > MAX_ID:
        raise RequestError(f"Invalid {name}: {raw[:50]}. Must be an integer id.", status_code=404)
    return int(raw)


async def read_json_object(request: Request) -> dict[str, Any]:
    """Return the request body as a JSON object, or raise a 400."""
    try:
        body = await request.json()
    except (ValueError, RecursionError):
        raise RequestError("Invalid JSON body") from None
    if not isinstance(body, dict):
        raise RequestError("Request body must be a JSON object")
    return body


def body_int(value: Any, name: str) -> int:
    """Coerce a body value to a database-safe int, or raise a 400."""
    try:
        number = int(value)
    except (TypeError, ValueError, OverflowError):
        raise RequestError(f"Invalid {name}: must be an integer") from None
    if not MIN_INT <= number <= MAX_ID:
        raise RequestError(f"Invalid {name}: out of range")
    return number


def query_int(params: QueryParams, name: str) -> int | None:
    """Return an optional integer query parameter, or raise a 400."""
    raw = params.get(name)
    if not raw:
        return None
    try:
        number = int(raw)
    except ValueError:
        raise RequestError(f"Invalid {name}: {raw[:50]}. Must be an integer.") from None
    if not MIN_INT <= number <= MAX_ID:
        raise RequestError(f"Invalid {name}: {raw[:50]}. Out of range.")
    return number


def query_enum[E: Enum](params: QueryParams, name: str, enum_type: type[E]) -> E | None:
    """Return an optional enum query parameter, or raise a 400 listing the valid values."""
    raw = params.get(name)
    if not raw:
        return None
    try:
        return enum_type(raw)
    except ValueError:
        valid = ", ".join(str(member.value) for member in enum_type)
        raise RequestError(f"Invalid {name}: {raw[:50]}. Valid values: {valid}") from None
