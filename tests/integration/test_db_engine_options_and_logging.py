"""Regression tests for database engine options and SQL logging.

Covers:
- the adapters' ``session()`` / ``system_session()`` error logging: domain outcomes are
  not database failures, and SQL parameters (user content) never reach the log
- ``create_async_engine`` options: no SQLAlchemy ``echo`` (it installs a stdout handler),
  parameters hidden
- ``configure_logging(db_logging=...)``: SQL logging is driven through the logging pipeline

Everything runs offline: the Postgres adapter is built without connecting and driven
through a fake session factory.
"""
import io
import json
import logging
import sys
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.config import logging_config
from app.config.settings import settings
from app.exceptions import (
    ConflictError,
    CyclicDependencyError,
    DependencyNotMetError,
    InvalidStateTransitionError,
    NotFoundError,
)
from app.repositories.postgres.postgres_adapter import PostgresDatabaseAdapter
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter

SECRET = "PRIVATE-NOTE-SECRET-XYZ-9876"

DOMAIN_ERRORS = [
    NotFoundError,
    ConflictError,
    InvalidStateTransitionError,
    DependencyNotMetError,
    CyclicDependencyError,
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
class _Capture(logging.Handler):
    """Collect everything a logger emits, rendered the way a handler would print it."""

    def __init__(self):
        super().__init__(level=logging.DEBUG)
        self.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
        self.records: list[logging.LogRecord] = []
        self.rendered: list[str] = []

    def emit(self, record):
        self.records.append(record)
        # Include extras: structured handlers (JSON) emit every record attribute
        extras = json.dumps(vars(record), default=str)
        self.rendered.append(self.format(record) + "\n" + extras)

    @property
    def text(self) -> str:
        return "\n".join(self.rendered)

    def at_least(self, level: int) -> list[logging.LogRecord]:
        return [r for r in self.records if r.levelno >= level]


class _FakeSession:
    """Stands in for an AsyncSession so the session() context managers run offline."""

    def __init__(self):
        self.committed = False
        self.rolled_back = False
        self.closed = False

    async def execute(self, *args, **kwargs):
        return None

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True

    async def close(self):
        self.closed = True


def _attach(logger_name: str):
    """Capture a logger even if a previous test left it disabled (alembic fileConfig)."""
    lg = logging.getLogger(logger_name)
    saved = (lg.disabled, lg.level)
    lg.disabled = False
    lg.setLevel(logging.DEBUG)
    cap = _Capture()
    lg.addHandler(cap)
    return lg, cap, saved


@pytest.fixture(params=["sqlite", "postgres"])
def fake_backend(request, monkeypatch):
    """Adapter whose sessions are fakes, plus a capture handler on its logger."""
    monkeypatch.setattr(settings, "SQLITE_MEMORY", True)
    adapter = SqliteDatabaseAdapter() if request.param == "sqlite" else PostgresDatabaseAdapter()
    sessions: list[_FakeSession] = []

    def factory():
        sessions.append(_FakeSession())
        return sessions[-1]

    adapter._session_factory = factory
    logger_name = (
        "app.repositories.sqlite.sqlite_adapter"
        if request.param == "sqlite"
        else "app.repositories.postgres.postgres_adapter"
    )
    lg, cap, saved = _attach(logger_name)
    try:
        yield adapter, sessions, cap
    finally:
        lg.removeHandler(cap)
        lg.disabled, level = saved
        lg.setLevel(level)


def _open(adapter, kind):
    return adapter.session(uuid4()) if kind == "session" else adapter.system_session()


# ---------------------------------------------------------------------------
# session() / system_session() error logging
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("kind", ["session", "system_session"])
@pytest.mark.parametrize("error_cls", DOMAIN_ERRORS)
async def test_domain_errors_are_rolled_back_but_not_logged(fake_backend, kind, error_cls):
    """A 404 / conflict is a normal outcome, not a database failure to log at ERROR."""
    adapter, sessions, cap = fake_backend

    with pytest.raises(error_cls):
        async with _open(adapter, kind):
            raise error_cls("Memory with id 99999 not found")

    assert sessions[-1].rolled_back and sessions[-1].closed
    assert not sessions[-1].committed
    assert not cap.at_least(logging.WARNING), cap.text


@pytest.mark.parametrize("kind", ["session", "system_session"])
async def test_integrity_error_is_not_logged_as_error_or_with_parameters(fake_backend, kind):
    """Callers translate IntegrityError (duplicate link, unique external id); no ERROR flood."""
    adapter, _sessions, cap = fake_backend
    error = IntegrityError("INSERT INTO t (title, content) VALUES (?, ?)", (None, SECRET), Exception("dup"))
    assert SECRET in str(error)  # the exception text itself is what must never be logged

    with pytest.raises(IntegrityError):
        async with _open(adapter, kind):
            raise error

    assert not cap.at_least(logging.WARNING), cap.text
    assert SECRET not in cap.text


@pytest.mark.parametrize("kind", ["session", "system_session"])
async def test_unexpected_error_is_logged_once_with_type_name_only(fake_backend, kind):
    adapter, sessions, cap = fake_backend

    with pytest.raises(RuntimeError):
        async with _open(adapter, kind):
            raise RuntimeError(f"driver exploded near {SECRET}")

    assert sessions[-1].rolled_back and sessions[-1].closed
    errors = cap.at_least(logging.ERROR)
    assert len(errors) == 1, cap.text
    record = errors[0]
    assert record.levelno == logging.ERROR
    assert "RuntimeError" in cap.text
    assert "initialis" not in record.getMessage().lower()  # message used to claim "initialisation failed"
    assert not record.exc_info, "traceback text carries str(exc), which may hold SQL parameters"
    assert SECRET not in cap.text


@pytest.mark.parametrize("kind", ["session", "system_session"])
async def test_successful_session_commits_and_logs_nothing(fake_backend, kind):
    adapter, sessions, cap = fake_backend

    async with _open(adapter, kind):
        pass

    assert sessions[-1].committed and sessions[-1].closed and not sessions[-1].rolled_back
    assert not cap.records


# ---------------------------------------------------------------------------
# Engine options
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("adapter_cls", [SqliteDatabaseAdapter, PostgresDatabaseAdapter])
def test_engine_hides_parameters(monkeypatch, adapter_cls):
    """str(exc) of a failed statement would otherwise carry the bound values (user content)."""
    monkeypatch.setattr(settings, "SQLITE_MEMORY", True)

    assert adapter_cls()._engine.sync_engine.hide_parameters is True


@pytest.mark.parametrize("adapter_cls", [SqliteDatabaseAdapter, PostgresDatabaseAdapter])
def test_engine_never_echoes(monkeypatch, adapter_cls):
    """echo=True makes SQLAlchemy attach its own StreamHandler(sys.stdout) to the engine logger."""
    monkeypatch.setattr(settings, "SQLITE_MEMORY", True)
    monkeypatch.setattr(settings, "DB_LOGGING", True)

    assert not adapter_cls()._engine.echo  # None / False: no SQLAlchemy-managed stdout handler


async def test_sqlite_failed_write_exception_text_has_no_parameters(monkeypatch):
    """A failing INSERT/UPDATE must not copy the user's content into str(exception)."""
    monkeypatch.setattr(settings, "SQLITE_MEMORY", True)
    adapter = SqliteDatabaseAdapter()
    lg, cap, saved = _attach("app.repositories.sqlite.sqlite_adapter")
    table = f"engine_options_{uuid4().hex[:8]}"
    try:
        async with adapter.system_session() as session:
            await session.execute(text(f"CREATE TABLE {table} (title TEXT NOT NULL, content TEXT)"))

        with pytest.raises(IntegrityError) as excinfo:
            async with adapter.session(uuid4()) as session:
                await session.execute(
                    text(f"INSERT INTO {table} (title, content) VALUES (:t, :c)"),  # noqa: S608
                    {"t": None, "c": SECRET},
                )

        assert SECRET not in str(excinfo.value)
        assert SECRET not in cap.text
        assert not cap.at_least(logging.WARNING), cap.text
    finally:
        lg.removeHandler(cap)
        lg.disabled, level = saved
        lg.setLevel(level)
        await adapter.dispose()


# ---------------------------------------------------------------------------
# configure_logging
# ---------------------------------------------------------------------------
@pytest.fixture
def configure(monkeypatch):
    """Run configure_logging with stderr captured; yields (configure, read_stderr)."""
    root = logging.getLogger()
    engine_logger = logging.getLogger("sqlalchemy.engine")
    saved = (list(root.handlers), root.level, engine_logger.level)
    buf = io.StringIO()

    def _configure(log_format="console", level="DEBUG", **kwargs):
        # StreamHandler(sys.stderr) binds at configure time; patch here, not in the fixture,
        # because pytest's capture re-installs its own sys.stderr when the test body starts.
        monkeypatch.setattr(sys, "stderr", buf)
        return logging_config.configure_logging(level, log_format, **kwargs)

    def read() -> str:
        logging_config.shutdown_logging()  # stops the listener: queued records are flushed
        return buf.getvalue()

    try:
        yield _configure, read
    finally:
        logging_config.shutdown_logging()
        root.handlers[:] = saved[0]
        root.setLevel(saved[1])
        engine_logger.setLevel(saved[2])


@pytest.mark.parametrize(
    "kwargs,expected",
    [
        ({}, logging.WARNING),
        ({"db_logging": False}, logging.WARNING),
        ({"db_logging": True}, logging.INFO),
    ],
)
def test_sql_logging_level_follows_db_logging(configure, kwargs, expected):
    setup, _read = configure
    setup("console", level="WARNING", **kwargs)

    assert logging.getLogger("sqlalchemy.engine").level == expected
