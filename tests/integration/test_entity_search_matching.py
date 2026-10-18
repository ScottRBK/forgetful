"""Integration tests for the literal, case-insensitive text matching helpers.

These run the helpers against a real in-memory SQLite connection, with no application
stack, to pin down how wildcards, escapes and Unicode case folding behave.
"""
import pytest
from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    event,
    select,
)

from app.repositories.sqlite.text_matching import (
    contains_ignore_case,
    register_text_functions,
)
from app.utils.like_pattern import LIKE_ESCAPE_CHAR, contains_pattern, escape_like

NAMES = [
    "auth_service",
    "auth-service",
    "100% done",
    "plain",
    "back\\slash",
    "backslash",
    "Émile Zola",
    "Zoë",
    "Straße",
]


@pytest.fixture
def names_table():
    engine = create_engine("sqlite://")
    event.listen(
        engine, "connect", lambda dbapi_conn, _record: register_text_functions(dbapi_conn),
    )
    table = Table(
        "names",
        MetaData(),
        Column("id", Integer, primary_key=True),
        Column("name", String),
    )
    table.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(table.insert(), [{"name": name} for name in NAMES])
        conn.execute(table.insert(), [{"name": None}])
    yield engine, table
    engine.dispose()


def _matches(names_table, text):
    engine, table = names_table
    stmt = select(table.c.name).where(contains_ignore_case(table.c.name, text))
    with engine.connect() as conn:
        return sorted(conn.execute(stmt).scalars())


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("auth_service", ["auth_service"]),
        ("%", ["100% done"]),
        ("_", ["auth_service"]),
        ("back\\slash", ["back\\slash"]),
        ("\\", ["back\\slash"]),
        ("PLAIN", ["plain"]),
        ("émile", ["Émile Zola"]),
        ("ÉMILE ZOLA", ["Émile Zola"]),
        ("ZOË", ["Zoë"]),
        ("strasse", ["Straße"]),
        ("STRASSE", ["Straße"]),
        ("missing", []),
    ],
)
def test_contains_ignore_case_matches_literal_text(names_table, text, expected):
    assert _matches(names_table, text) == expected


def test_contains_ignore_case_never_matches_null(names_table):
    engine, table = names_table
    stmt = select(table.c.id).where(~contains_ignore_case(table.c.name, "plain"))
    with engine.connect() as conn:
        # NULL names are neither matched nor negated-matched by the LIKE predicate.
        assert len(list(conn.execute(stmt))) == len(NAMES) - 1


@pytest.mark.parametrize(
    ("text", "escaped"),
    [
        ("plain", "plain"),
        ("a_b", "a\\_b"),
        ("50%", "50\\%"),
        ("a\\b", "a\\\\b"),
        ("\\%_", "\\\\\\%\\_"),
    ],
)
def test_escape_like(text, escaped):
    assert LIKE_ESCAPE_CHAR == "\\"
    assert escape_like(text) == escaped
    assert contains_pattern(text) == f"%{escaped}%"
