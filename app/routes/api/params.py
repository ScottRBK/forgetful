"""Integer parsing for REST query and path parameters.

An invalid value raises ValueError with the same message for query and path parameters.
Routes return that message as HTTP 400.
"""
from collections.abc import Mapping
from typing import Any

from starlette.requests import Request


def _parse_int(name: str, raw: Any) -> int:
    try:
        return int(raw)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid value for '{name}': must be an integer") from None


def parse_int_param(
    params: Mapping[str, Any], name: str, default: int | None = None,
) -> int | None:
    """Parse an optional integer query parameter; return default when it is absent.

    Raises:
        ValueError: If value is not a valid integer
    """
    raw = params.get(name)
    return default if raw is None else _parse_int(name, raw)


def parse_path_int(request: Request, name: str) -> int:
    """Parse a required integer path parameter.

    Raises:
        ValueError: If value is not a valid integer
    """
    return _parse_int(name, request.path_params[name])
