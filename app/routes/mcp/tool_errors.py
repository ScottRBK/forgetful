"""Client-safe error text for MCP tool failures.

``str(exc)`` of an unexpected exception can carry SQL statements, bound parameters, internal
ids and driver internals. Only the exception types listed here have messages that are written
for the caller; everything else is reduced to a short generic sentence and its full detail
stays in the server logs.
"""

import yaml
from fastmcp.exceptions import ToolError
from sqlalchemy.exc import IntegrityError

from app.exceptions import (
    ConflictError,
    CyclicDependencyError,
    DependencyNotMetError,
    InvalidStateTransitionError,
    NotFoundError,
)

GENERIC_FAILURE = "an internal error occurred; see the server logs for details"
CONSTRAINT_FAILURE = (
    "the request violates a data constraint "
    "(for example a duplicate entry or a reference to a resource that does not exist)"
)
INVALID_YAML_FAILURE = "invalid YAML in the supplied content"

# Messages of these types are authored for the caller (domain errors, argument validation;
# pydantic's ValidationError is a ValueError) and never contain query or driver details.
_CLIENT_SAFE_ERRORS = (
    ToolError,
    NotFoundError,
    ConflictError,
    InvalidStateTransitionError,
    DependencyNotMetError,
    CyclicDependencyError,
    ValueError,
    TypeError,
)


def client_error_detail(exc: BaseException) -> str:
    """Return the text of ``exc`` that may be shown to an MCP client."""
    if isinstance(exc, IntegrityError):
        return CONSTRAINT_FAILURE
    if isinstance(exc, yaml.YAMLError):
        return INVALID_YAML_FAILURE
    if isinstance(exc, _CLIENT_SAFE_ERRORS):
        return str(exc)
    return GENERIC_FAILURE
