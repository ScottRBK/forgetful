"""ASCII-only case folding for literal text filters."""

_ASCII_FOLD = str.maketrans(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "abcdefghijklmnopqrstuvwxyz",
)


def fold_ascii(text: str) -> str:
    """Lowercase ASCII A-Z only; every other character is unchanged."""
    return text.translate(_ASCII_FOLD)
