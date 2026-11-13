"""query_memory response_format handling shared by both MCP surfaces.

Call require_query_memory_response_format before the service call so an invalid
value never runs retrieval, then project_query_memory_result on the result.
"""

from fastmcp.exceptions import ToolError

from app.models.memory_models import (
    MemoryQueryCompactResult,
    MemoryQueryResult,
    QueryMemoryResponseFormat,
    compact_memory_query_result,
    parse_query_memory_response_format,
)


def require_query_memory_response_format(value: str) -> QueryMemoryResponseFormat:
    """Validate response_format, raising ToolError VALIDATION_ERROR on unknown values."""
    try:
        return parse_query_memory_response_format(value)
    except ValueError as exc:
        raise ToolError(f"VALIDATION_ERROR: {exc}") from exc


def project_query_memory_result(
    result: MemoryQueryResult,
    response_format: QueryMemoryResponseFormat,
) -> MemoryQueryResult | MemoryQueryCompactResult:
    """Return the compact projection when requested, else the full result."""
    if response_format == "compact":
        return compact_memory_query_result(result)
    return result
