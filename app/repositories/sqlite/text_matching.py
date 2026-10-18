"""Case-insensitive literal substring matching for SQLite.

SQLite's built-in ``LIKE`` and ``lower()`` only fold ASCII letters, so ``Émile`` is not
found by ``émile``. Folding both sides with Python's ``str.casefold`` through a SQL
function registered on every connection gives the same Unicode-aware, case-insensitive
behaviour as PostgreSQL's ``ILIKE``.
"""
import sqlite3

from sqlalchemy import ColumnElement, func

from app.utils.like_pattern import LIKE_ESCAPE_CHAR, contains_pattern

CASEFOLD_FUNCTION = "forgetful_casefold"


def _casefold(value: object) -> object:
    """SQL function body: casefold text and pass NULL/non-text values through."""
    return value.casefold() if isinstance(value, str) else value


def register_text_functions(connection: sqlite3.Connection) -> None:
    """Register the SQL helper functions used by ``contains_ignore_case``."""
    connection.create_function(CASEFOLD_FUNCTION, 1, _casefold, deterministic=True)


def contains_ignore_case(column: ColumnElement, text: str) -> ColumnElement[bool]:
    """Match rows whose ``column`` contains ``text``, ignoring case and wildcards."""
    return getattr(func, CASEFOLD_FUNCTION)(column).like(
        contains_pattern(text.casefold()), escape=LIKE_ESCAPE_CHAR,
    )
