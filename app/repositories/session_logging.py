"""Error logging shared by the database adapters' session context managers.

A failure inside ``session()`` / ``system_session()`` is most often an expected outcome:
callers raise ``NotFoundError`` for a missing id and translate ``IntegrityError`` into a
``ConflictError`` or skip it (duplicate links). Those pass through without a log entry.

For anything else only the exception type is logged. ``str(exc)`` and the traceback text of a
database error embed the failing SQL, and the driver may echo the failing row (asyncpg
``DETAIL: Failing row contains (...)``), so they would copy user content into the logs.
"""
import logging

from sqlalchemy.exc import IntegrityError

from app import exceptions as domain_exceptions


def log_session_failure(logger: logging.Logger, exc: Exception, session_name: str) -> None:
    """Log a failure that escaped a database session body (type name only, never the message).

    Args:
        logger: The adapter's logger (so records keep the adapter as their source)
        exc: The exception about to be re-raised to the caller
        session_name: Human-readable session kind, e.g. "session" or "system session"
    """
    if type(exc).__module__ == domain_exceptions.__name__:
        return

    if isinstance(exc, IntegrityError):
        # Callers translate or skip constraint violations; a duplicate is not a server error
        logger.debug(
            "Database %s rolled back on constraint violation",
            session_name,
            extra={"error_type": type(exc).__name__},
        )
        return

    logger.error(
        "Database %s failed",
        session_name,
        extra={"error_type": type(exc).__name__},
    )
