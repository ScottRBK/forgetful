"""Regression tests for database engine options and the logging pipeline.

Covers:
- the adapters' ``session()`` / ``system_session()`` error logging: domain outcomes are
  not database failures, and SQL parameters (user content) never reach the log
- ``create_async_engine`` options: no SQLAlchemy ``echo`` (it installs a stdout handler),
  parameters hidden
- ``SensitiveDataFilter`` masks secret-shaped values only, not ordinary words
- ``configure_logging``: JSON output keeps ``exception`` / request context, no ``taskName``,
  and SQL logging is driven through the logging pipeline (``db_logging``)

Everything runs offline: the Postgres adapter is built without connecting and driven
through a fake session factory.
"""
import io
import json
import logging
import sys
from queue import Queue
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.config import logging_config
from app.config.logging_config import SensitiveDataFilter
from app.config.settings import settings
from app.exceptions import (
    ConflictError,
    CyclicDependencyError,
    DependencyNotMetError,
    InvalidStateTransitionError,
    NotFoundError,
)
from app.middleware.logging_middleware import request_id_var, user_id_var
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
# SensitiveDataFilter
# ---------------------------------------------------------------------------
def _filtered(message: str, *args) -> str:
    record = logging.LogRecord("t", logging.INFO, __file__, 1, message, args or None, None)
    assert SensitiveDataFilter().filter(record) is True
    return record.getMessage()


@pytest.mark.parametrize(
    "message",
    [
        "Token cache initialized (TTL: 300s, max: 1000)",
        "Token cache disabled",
        "Validating Bearer token via GitHubProvider",
        "applying token budget",
        "Invalid password for user alice",
        "Password policy enforced",
        "Bearer authentication is required",
        "Token claims received: {}",
    ],
)
def test_ordinary_text_is_not_masked(message):
    assert _filtered(message) == message


@pytest.mark.parametrize(
    "message,secret",
    [
        ("login password=hunter2 ok", "hunter2"),
        ("login password: hunter2 ok", "hunter2"),
        ('payload {"password": "hunter2", "a": 1}', "hunter2"),
        ("PASSWORD = hunter2", "hunter2"),
        ("auth token=abc123def ok", "abc123def"),
        ('payload {"token": "abc123def"}', "abc123def"),
        ("access_token=abc123def", "abc123def"),
        ("Authorization: Bearer abc123def", "abc123def"),
        ("Authorization: Bearer secretword", "secretword"),
        ("got Bearer eyJhbGciOiJIUzI1NiJ9.payload.signature", "eyJhbGciOiJIUzI1NiJ9"),
        ("got bearer 0123456789abcdef", "0123456789abcdef"),
        ("connect postgresql://user:s3cret@host:5432/db", "s3cret"),
    ],
)
def test_secret_shaped_values_are_masked(message, secret):
    assert secret not in _filtered(message)


def test_secrets_in_args_are_masked():
    assert "hunter2" not in _filtered("credentials %s", "password=hunter2")


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


def _test_logger() -> logging.Logger:
    """A logger that earlier tests' alembic fileConfig() (init_db) cannot have disabled."""
    logger = logging.getLogger("db_engine_options_test")
    logger.disabled = False
    return logger


def _json_lines(output: str) -> list[dict]:
    return [json.loads(line) for line in output.splitlines() if line.strip()]


def test_console_output_keeps_ordinary_text_and_masks_secrets(configure):
    setup, read = configure
    setup("console")
    _test_logger().info("Token cache disabled")
    _test_logger().info("connect with password=hunter2")
    out = read()
    assert "Token cache disabled" in out
    assert "hunter2" not in out


def test_json_exception_is_a_field_and_message_stays_clean(configure):
    setup, read = configure
    setup("json")
    try:
        1 / 0
    except ZeroDivisionError:
        _test_logger().exception("boom")

    record = _json_lines(read())[0]

    assert record["message"] == "boom"
    assert "ZeroDivisionError" in record["exception"]
    assert "Traceback" in record["exception"]


def test_json_message_is_formatted_in_the_emitting_thread(configure):
    setup, read = configure
    setup("json")
    _test_logger().info("hello %s #%d", "world", 3)

    assert _json_lines(read())[0]["message"] == "hello world #3"


def test_json_carries_request_and_user_context_from_the_emitting_thread(configure):
    setup, read = configure
    setup("json")
    request_token = request_id_var.set("req-123")
    user_token = user_id_var.set("user-456")
    try:
        _test_logger().info("hello")
    finally:
        request_id_var.reset(request_token)
        user_id_var.reset(user_token)

    record = _json_lines(read())[0]

    assert record["request_id"] == "req-123"
    assert record["user_id"] == "user-456"


def test_json_omits_context_fields_when_unset(configure):
    setup, read = configure
    setup("json")
    _test_logger().info("hello")

    record = _json_lines(read())[0]

    assert "request_id" not in record
    assert "user_id" not in record


def test_json_does_not_leak_stdlib_task_name_attribute(configure):
    setup, read = configure
    setup("json")
    _test_logger().info("hello", extra={"memory_id": 7})

    record = _json_lines(read())[0]

    assert "taskName" not in record
    assert record["memory_id"] == 7


def test_json_masks_sensitive_values_in_queued_records(configure):
    setup, read = configure
    setup("json")
    _test_logger().info("connect %s", "password=hunter2")

    assert "hunter2" not in read()


@pytest.mark.parametrize("log_format", ["console", "json"])
def test_tracebacks_are_masked(configure, log_format):
    """The traceback is rendered after the filter runs, so the filter must mask it itself."""
    setup, read = configure
    setup(log_format)
    try:
        raise RuntimeError("connect failed: password=hunter2")
    except RuntimeError:
        _test_logger().exception("boom")

    out = read()

    assert "RuntimeError" in out
    assert "hunter2" not in out


def test_queue_handler_enqueues_a_copy_and_keeps_exception_details():
    """prepare() hands the listener thread its own record; the original stays untouched."""
    handler = logging_config.RecordPreservingQueueHandler(Queue())
    try:
        1 / 0
    except ZeroDivisionError:
        record = logging.LogRecord("t", logging.ERROR, __file__, 1, "boom %s", ("x",), sys.exc_info())

    prepared = handler.prepare(record)

    assert prepared is not record
    assert prepared.exc_info == record.exc_info and prepared.exc_info is not None
    assert prepared.getMessage() == "boom x"
    assert record.msg == "boom %s" and record.args == ("x",)


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
