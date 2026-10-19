"""Snapshots of surfaces that must not change by accident: CLI help, settings, DB schema.

A changed snapshot is a contract change: review the diff, then refresh deliberately with
``uv run pytest -m snapshot --snapshot-update``.
"""

import argparse
import re
from pathlib import Path, PurePath

import pytest
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.schema import CreateIndex, CreateTable
from syrupy.extensions.json import JSONSnapshotExtension

import app.config.settings as settings_module
from app.config.settings import Settings
from app.repositories.postgres.postgres_tables import Base as PostgresBase
from app.repositories.sqlite.sqlite_tables import Base as SqliteBase
from app.routes.cli.parser import build_parser

pytestmark = pytest.mark.snapshot

SECRET_FIELD = re.compile(r"(_KEY|_SECRET|_PASSWORD|_CLIENT_ID|_TOKEN)$")
VOLATILE_FIELDS = {"SERVICE_VERSION"}  # derived from the git revision, changes with every commit
ALEMBIC_VERSIONS = Path(__file__).resolve().parents[2] / "alembic" / "versions"


@pytest.fixture
def json_snapshot(snapshot):
    return snapshot.use_extension(JSONSnapshotExtension)


@pytest.fixture
def pristine_settings(monkeypatch, tmp_path):
    """Settings built from code defaults only, immune to the developer's env and dotenv files."""
    for name in Settings.model_fields:
        monkeypatch.delenv(name, raising=False)
        monkeypatch.delenv(name.upper(), raising=False)
    monkeypatch.setenv("COLUMNS", "100")  # argparse wraps help at the terminal width
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.chdir(tmp_path)
    fresh = Settings(_env_file=None)
    monkeypatch.setattr(settings_module, "settings", fresh)
    return fresh


def _describe(parser: argparse.ArgumentParser, name: str, out: dict[str, list[dict]]) -> None:
    """Structural description of a parser tree.

    Formatted help text is not used: argparse wraps and words usage differently between
    Python releases, while arguments, defaults and help strings are the actual contract.
    """
    arguments = []
    for action in parser._actions:  # noqa: SLF001 - argparse exposes its actions only here
        if isinstance(action, argparse._SubParsersAction):  # noqa: SLF001
            for child_name, child in sorted(action.choices.items()):
                _describe(child, f"{name} {child_name}", out)
            continue
        arguments.append({
            "flags": action.option_strings or [action.dest],
            "required": action.required,
            "nargs": action.nargs,
            "choices": sorted(action.choices) if action.choices else None,
            "default": None if action.default is argparse.SUPPRESS else action.default,
            "type": getattr(action.type, "__name__", None),
            "help": action.help,
        })
    out[name] = arguments


def test_cli_argument_tree(pristine_settings, json_snapshot):
    tree: dict[str, list[dict]] = {}
    _describe(build_parser(), "forgetful", tree)
    assert tree == json_snapshot


def test_settings_defaults(pristine_settings, json_snapshot):
    dumped = {}
    for name, value in sorted(pristine_settings.model_dump().items()):
        if name in VOLATILE_FIELDS:
            dumped[name] = "<varies per build>"
        elif SECRET_FIELD.search(name):
            dumped[name] = "<set>" if value else "<unset>"
        elif isinstance(value, str) and PurePath(value).is_absolute():
            dumped[name] = "<absolute path>"  # platform- and user-specific default
        elif isinstance(value, str | int | float | bool | type(None)):
            dumped[name] = value
        else:
            dumped[name] = str(value)
    assert dumped == json_snapshot


def _ddl(base, dialect) -> dict[str, list[str]]:
    schema = {}
    for table in sorted(base.metadata.sorted_tables, key=lambda t: t.name):
        statements = [str(CreateTable(table).compile(dialect=dialect)).strip()]
        statements += [
            str(CreateIndex(index).compile(dialect=dialect)).strip()
            for index in sorted(table.indexes, key=lambda i: i.name or "")
        ]
        schema[table.name] = statements
    return schema


def test_sqlite_schema(json_snapshot):
    assert _ddl(SqliteBase, sqlite.dialect()) == json_snapshot


def test_postgres_schema(json_snapshot):
    assert _ddl(PostgresBase, postgresql.dialect()) == json_snapshot


def test_migration_chain(json_snapshot):
    revisions = {}
    for path in sorted(ALEMBIC_VERSIONS.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        revision = re.search(r'^revision(?:: str)? = ["\'](\w+)["\']', text, re.MULTILINE)
        parent = re.search(r"^down_revision(?:: [^=]+)? = (.+)$", text, re.MULTILINE)
        revisions[path.name] = {
            "revision": revision.group(1) if revision else None,
            "down_revision": parent.group(1).strip().strip("\"'") if parent else None,
        }
    assert revisions == json_snapshot
