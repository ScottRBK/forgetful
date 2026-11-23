"""Shared REST list paging validation, matching the Memories endpoint."""
from typing import Any


def parse_list_pagination(params: Any) -> tuple[int, int]:
    """Return the effective limit and offset or the existing API error text."""
    values = []
    for name, default in (("limit", 20), ("offset", 0)):
        raw = params.get(name)
        try:
            values.append(default if raw is None else int(raw))
        except (ValueError, TypeError):
            raise ValueError(f"Invalid value for '{name}': must be an integer")
    limit, offset = values
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")
    if offset < 0:
        raise ValueError("offset must be non-negative")
    return limit, offset
