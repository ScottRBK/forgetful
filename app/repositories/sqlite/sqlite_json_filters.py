"""SQLite helpers for filtering on JSON array columns

JSON columns are serialized by SQLAlchemy with ``ensure_ascii=True`` so the
stored text is not what the caller typed (``"café"`` is stored as
``"caf\\u00e9"``). Matching a ``LIKE`` pattern against that text therefore misses
non-ASCII values, treats ``%`` / ``_`` as wildcards and is case-insensitive.
Expanding the array with ``json_each`` compares the decoded element values
instead, which is the same exact-membership contract as the PostgreSQL ``&&``
array overlap.
"""
from collections.abc import Sequence

from sqlalchemy import ColumnElement, exists, func, select


def json_array_overlaps(
    column: ColumnElement,
    values: Sequence[str],
) -> ColumnElement[bool]:
    """Build a condition matching rows whose JSON array shares an element with values

    Args:
        column: JSON array column holding a list of strings (e.g. ``tags``)
        values: Values to look for (ANY match, exact and case-sensitive)

    Returns:
        Correlated EXISTS condition usable in ``where()``
    """
    elements = func.json_each(column).table_valued("value")
    return exists(
        select(1).select_from(elements).where(elements.c.value.in_(list(values))),
    )
