"""Regression tests for log ``extra`` dicts that collide with LogRecord attributes.

``Logger.makeRecord`` raises ``KeyError("Attempt to overwrite 'name' in LogRecord")``
for any ``extra`` key that is also a LogRecord attribute (``name``, ``filename``,
``module``, ``args``...). Because the exception is raised by the logging call itself, a
colliding key turns a harmless log line into a crash:

- on the happy path whenever INFO is enabled for the module (``logger.info``), and
- on the error path always (``logger.exception``), where it also replaces the real
  database error with a ``KeyError``.

The Alembic ``fileConfig`` call run by ``init_db`` disables the app loggers that already
exist, which hides these crashes in most test runs. The ``info_logging`` fixture puts the
affected loggers back into the state of a server whose loggers are live.
"""

import ast
import logging
from pathlib import Path
from uuid import uuid4

import pytest

from app.models.file_models import FileCreate
from app.models.project_models import ProjectCreate
from app.models.skill_models import SkillCreate

APP_DIR = Path(__file__).resolve().parents[2] / "app"

AFFECTED_LOGGERS = (
    "app.services.skill_service",
    "app.services.project_service",
    "app.services.file_service",
    "app.repositories.postgres.skill_repository",
    "app.repositories.postgres.project_repository",
    "app.repositories.sqlite.skill_repository",
    "app.repositories.sqlite.project_repository",
    "app.routes.mcp.project_tools",
    "app.routes.mcp.skill_tools",
)

LOG_METHODS = {"debug", "info", "warning", "warn", "error", "exception", "critical", "log"}


def _reserved_logrecord_keys() -> set[str]:
    """Names ``Logger.makeRecord`` refuses in ``extra`` (plus the formatter-set ones)."""
    probe = logging.LogRecord("probe", logging.INFO, "probe.py", 1, "msg", (), None)
    return set(probe.__dict__) | {"message", "asctime"}


@pytest.fixture
def info_logging(caplog):
    """Enable INFO on the affected module loggers and capture what they emit."""
    saved = []
    for name in AFFECTED_LOGGERS:
        module_logger = logging.getLogger(name)
        saved.append((module_logger, module_logger.level, module_logger.disabled))
        module_logger.disabled = False
        module_logger.setLevel(logging.INFO)
    caplog.set_level(logging.INFO)
    yield caplog
    for module_logger, level, disabled in saved:
        module_logger.setLevel(level)
        module_logger.disabled = disabled


def _single_record(caplog, logger_name: str, message: str) -> logging.LogRecord:
    """The one record ``logger_name`` emitted with ``message`` (others, e.g. init logs, ignored)."""
    matches = [
        r for r in caplog.records if r.name == logger_name and r.getMessage() == message
    ]
    assert len(matches) == 1, [r.getMessage() for r in caplog.records]
    return matches[0]


def test_log_extra_never_uses_reserved_logrecord_keys():
    """No ``extra={...}`` literal under app/ may use a key reserved by LogRecord."""
    reserved = _reserved_logrecord_keys()
    offenders = []
    for path in sorted(APP_DIR.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in LOG_METHODS
            ):
                continue
            for keyword in node.keywords:
                if keyword.arg != "extra":
                    continue
                if isinstance(keyword.value, ast.Dict):
                    keys = [k.value for k in keyword.value.keys if isinstance(k, ast.Constant)]
                elif (
                    isinstance(keyword.value, ast.Call)
                    and isinstance(keyword.value.func, ast.Name)
                    and keyword.value.func.id == "dict"
                ):
                    keys = [k.arg for k in keyword.value.keywords if k.arg]
                else:
                    continue
                offenders.extend(
                    f"{path.relative_to(APP_DIR.parent)}:{node.lineno} uses reserved key {key!r}"
                    for key in keys
                    if key in reserved
                )
    assert not offenders, "\n".join(offenders)


async def test_create_skill_with_info_logging(test_skill_service, info_logging):
    user_id = uuid4()

    skill = await test_skill_service.create_skill(
        user_id,
        SkillCreate(name="reserved-key-skill", description="d" * 20, content="c" * 20),
    )

    assert skill.name == "reserved-key-skill"
    record = _single_record(info_logging, "app.services.skill_service", "creating skill")
    assert record.skill_name == "reserved-key-skill"
    assert record.user_id == str(user_id)


async def test_import_skill_with_info_logging(test_skill_service, info_logging):
    skill = await test_skill_service.import_skill(
        uuid4(),
        "---\nname: reserved-key-import\ndescription: imported with INFO logging\n---\n\nbody",
    )

    assert skill.name == "reserved-key-import"


async def test_list_projects_with_info_logging(test_project_service, info_logging):
    user_id = uuid4()
    await test_project_service.create_project(
        user_id,
        ProjectCreate(
            name="Forgetful", description="d" * 20, project_type="development",
        ),
    )

    projects = await test_project_service.list_projects(user_id, name="forget")

    assert [p.name for p in projects] == ["Forgetful"]
    record = _single_record(info_logging, "app.services.project_service", "listing projects")
    assert record.name_filter == "forget"


async def test_create_file_with_info_logging(test_file_service, info_logging):
    file = await test_file_service.create_file(
        uuid4(),
        FileCreate(
            filename="hello.txt",
            description="A greeting file",
            data="SGVsbG8sIFdvcmxkIQ==",
            mime_type="text/plain",
        ),
    )

    assert file.filename == "hello.txt"
    record = _single_record(info_logging, "app.services.file_service", "creating file")
    assert record.file_name == "hello.txt"


class _FailingDbAdapter:
    """db_adapter whose session() fails like an unreachable or locked database."""

    def session(self, user_id):
        raise ConnectionRefusedError("database unavailable")


@pytest.mark.parametrize("backend", ["postgres", "sqlite"])
async def test_skill_name_exists_reraises_original_database_error(backend, caplog):
    """The real database error must propagate, not a KeyError from the logging call."""
    if backend == "postgres":
        from app.repositories.postgres.skill_repository import (
            PostgresSkillRepository as Repo,
        )
    else:
        from app.repositories.sqlite.skill_repository import (
            SqliteSkillRepository as Repo,
        )
    module_logger = logging.getLogger(Repo.__module__)
    previous_disabled = module_logger.disabled
    module_logger.disabled = False
    repository = Repo(db_adapter=_FailingDbAdapter(), embedding_adapter=object())

    try:
        with pytest.raises(ConnectionRefusedError):
            await repository.skill_name_exists(uuid4(), "my-skill")
    finally:
        module_logger.disabled = previous_disabled

    record = _single_record(caplog, Repo.__module__, "Failed to check skill name existence")
    assert record.levelno == logging.ERROR
    assert record.skill_name == "my-skill"


@pytest.mark.parametrize("backend", ["postgres", "sqlite"])
async def test_repository_list_projects_logs_with_info_logging(backend, info_logging):
    if backend == "postgres":
        from app.repositories.postgres.project_repository import (
            PostgresProjectRepository as Repo,
        )
    else:
        from app.repositories.sqlite.project_repository import (
            SqliteProjectRepository as Repo,
        )
    repository = Repo(db_adapter=_FailingDbAdapter())

    # The log line precedes the database access, so reaching the stub's
    # ConnectionRefusedError proves the logging call itself did not raise.
    with pytest.raises(ConnectionRefusedError):
        await repository.list_projects(uuid4(), name="forget")

    record = _single_record(info_logging, Repo.__module__, "Listing projects")
    assert record.name_filter == "forget"


@pytest.fixture
def legacy_mcp(info_logging):
    """FastMCP instance with the legacy project/skill tool modules over in-memory stubs."""
    from fastmcp import FastMCP

    from app.routes.mcp import project_tools
    from app.services.project_service import ProjectService
    from app.services.skill_service import SkillService
    from app.services.user_service import UserService
    from tests.integration.conftest import (
        InMemoryProjectRepository,
        InMemorySkillRepository,
        InMemoryUserRepository,
    )

    mcp = FastMCP("reserved-logrecord-key")
    mcp.user_service = UserService(InMemoryUserRepository())
    mcp.project_service = ProjectService(InMemoryProjectRepository())
    mcp.skill_service = SkillService(InMemorySkillRepository())
    project_tools.register(mcp)
    return mcp


async def test_legacy_list_projects_tool_with_info_logging(legacy_mcp, info_logging):
    from fastmcp import Client

    async with Client(legacy_mcp) as client:
        await client.call_tool("list_projects", {"name": "forget"})

    record = _single_record(
        info_logging, "app.routes.mcp.project_tools", "MCP Tool Called -> list_projects",
    )
    assert record.name_filter == "forget"


async def test_legacy_create_skill_tool_with_info_logging(legacy_mcp, info_logging):
    skill_tools = pytest.importorskip("app.routes.mcp.skill_tools")
    from fastmcp import Client

    skill_tools.register(legacy_mcp)
    async with Client(legacy_mcp) as client:
        await client.call_tool(
            "create_skill",
            {
                "name": "legacy-skill",
                "description": "created through the legacy tool",
                "content": "# Steps\n1. do the thing",
            },
        )

    record = _single_record(
        info_logging, "app.routes.mcp.skill_tools", "MCP Tool Called -> create_skill",
    )
    assert record.skill_name == "legacy-skill"
