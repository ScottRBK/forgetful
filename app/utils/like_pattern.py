"""Build LIKE/ILIKE patterns that match user text literally."""

LIKE_ESCAPE_CHAR = "\\"


def escape_like(text: str) -> str:
    """Escape LIKE wildcards so ``%``, ``_`` and the escape character match themselves.

    Pass ``LIKE_ESCAPE_CHAR`` as the ``escape`` argument of ``like``/``ilike``.
    """
    return (
        text.replace(LIKE_ESCAPE_CHAR, LIKE_ESCAPE_CHAR * 2)
        .replace("%", f"{LIKE_ESCAPE_CHAR}%")
        .replace("_", f"{LIKE_ESCAPE_CHAR}_")
    )


def contains_pattern(text: str) -> str:
    """Return a LIKE pattern matching any value that contains ``text`` literally."""
    return f"%{escape_like(text)}%"
