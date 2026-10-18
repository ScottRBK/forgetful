"""Output rendering for the CLI."""
import json
import re
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


# C0 and C1 control characters (ESC, BEL, newlines, CSI/OSC introducers) plus the Unicode
# line and paragraph separators. Tab and newline stay legal in multi-line content.
_LINE_UNSAFE = re.compile(r"[\x00-\x1f\x7f-\x9f\u2028\u2029]")
_TEXT_UNSAFE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f\u2028\u2029]")


def _escape(match: re.Match) -> str:
    return match.group().encode("unicode_escape").decode("ascii")


def sanitize_line(value: Any) -> str:
    """Make stored text safe for one terminal line.

    Memories are written by agents and external sources, so titles, tags and names can
    carry escape sequences or newlines that would repaint the terminal or forge extra
    result rows. Control characters become visible escapes such as '\\x1b' and '\\n'.
    """
    return _LINE_UNSAFE.sub(_escape, str(value))


def sanitize_text(value: Any) -> str:
    """Like sanitize_line for multi-line content: keeps newlines and tabs, folds CRLF."""
    return _TEXT_UNSAFE.sub(_escape, str(value).replace("\r\n", "\n"))


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
        f"#{index}  [{memory.get('importance', '?')}]  {sanitize_line(memory['title'])}"
        f"  (memory {memory['id']})"
        for index, memory in enumerate(memories, 1)
    )


def render_memory_detail(memory: dict) -> str:
    """Multi-line detail view for a single memory; obsolete memories are flagged."""
    tags = ", ".join(sanitize_line(tag) for tag in memory.get("tags") or []) or "-"
    lines = [f"Memory {memory['id']}: {sanitize_line(memory['title'])}"]
    lines.extend([
        f"Importance: {memory.get('importance', '?')}    Tags: {tags}",
        f"Context: {sanitize_line(memory.get('context') or '-')}",
        "",
        sanitize_text(memory.get("content") or ""),
    ])
    return "\n".join(lines)


def render_project_lines(projects: list[dict]) -> str:
    """Compact one-line-per-project listing."""
    if not projects:
        return "No projects found."
    return "\n".join(
        f"#{project['id']}  {sanitize_line(project['name'])}  "
        f"({sanitize_line(project.get('project_type', '?'))}, "
        f"{sanitize_line(project.get('status', '?'))})"
        for project in projects
    )
