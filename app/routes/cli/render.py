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


def render_memory_lines(memories: list[dict]) -> str:
    """Compact one-line-per-memory listing, e.g. '#1  [8]  Title  (memory 812)'."""
    if not memories:
        return "No memories found."
    return "\n".join(
        f"#{index}  [{memory.get('importance', '?')}]  {memory['title']}  (memory {memory['id']})"
        for index, memory in enumerate(memories, 1)
    )


def render_memory_detail(memory: dict) -> str:
    """Multi-line detail view for a single memory."""
    tags = ", ".join(memory.get("tags") or []) or "-"
    return "\n".join([
        f"Memory {memory['id']}: {memory['title']}",
        f"Importance: {memory.get('importance', '?')}    Tags: {tags}",
        f"Context: {memory.get('context') or '-'}",
        "",
        memory.get("content") or "",
    ])


def render_project_lines(projects: list[dict]) -> str:
    """Compact one-line-per-project listing."""
    if not projects:
        return "No projects found."
    return "\n".join(
        f"#{project['id']}  {project['name']}  "
        f"({project.get('project_type', '?')}, {project.get('status', '?')})"
        for project in projects
    )
