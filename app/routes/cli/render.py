"""Output rendering for the CLI."""
import json
import sys
from typing import Any

from pydantic import BaseModel


def to_jsonable(value: Any) -> Any:
    """Convert tool results (pydantic models, containers, scalars) to JSON-safe data."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def render_result(value: Any, as_json: bool) -> str:
    """Passthrough rendering: compact JSON for --json, indented JSON for humans."""
    payload = to_jsonable(value)
    if as_json:
        return json.dumps(payload)
    return json.dumps(payload, indent=2)


def emit_error(message: str, as_json: bool) -> None:
    """Write an error to stderr; JSON mode emits {"error": ...} for scriptability."""
    if as_json:
        print(json.dumps({"error": message}), file=sys.stderr)
    else:
        print(f"Error: {message}", file=sys.stderr)
