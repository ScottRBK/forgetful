"""E2E tests: INFO logging must not break skills, files and projects on SQLite.

Several log calls passed ``extra={"name": ...}`` (or ``"filename"``), keys reserved by
``logging.LogRecord``. ``Logger.makeRecord`` raises ``KeyError`` for those, so skill
creation, file creation and project listing crashed whenever INFO was enabled for the
module loggers.

``init_db`` runs Alembic, whose ``fileConfig`` call disables every app logger that
already exists and resets the root level, which hides the crash in the default test
setup. The fixtures below re-enable INFO after the app has started, which is the state
the affected code runs in once those loggers are live.
"""

import contextlib
import logging

import pytest

LOGGERS = (
    "app.services.skill_service",
    "app.services.project_service",
    "app.services.file_service",
    "app.repositories.sqlite.skill_repository",
    "app.repositories.sqlite.project_repository",
    "app.repositories.sqlite.file_repository",
)


@contextlib.contextmanager
def _info_enabled(caplog):
    saved = []
    for name in LOGGERS:
        module_logger = logging.getLogger(name)
        saved.append((module_logger, module_logger.level, module_logger.disabled))
        module_logger.disabled = False
        module_logger.setLevel(logging.INFO)
    caplog.set_level(logging.INFO)
    try:
        yield caplog
    finally:
        for module_logger, level, disabled in saved:
            module_logger.setLevel(level)
            module_logger.disabled = disabled


@pytest.fixture
def info_logging_http(http_client, caplog):
    """INFO enabled once the app behind ``http_client`` has finished starting up."""
    with _info_enabled(caplog) as captured:
        yield captured


@pytest.fixture
def info_logging_mcp(mcp_client, caplog):
    """INFO enabled once the app behind ``mcp_client`` has finished starting up."""
    with _info_enabled(caplog) as captured:
        yield captured


def _messages(caplog, logger_name: str) -> set[str]:
    return {r.getMessage() for r in caplog.records if r.name == logger_name}


@pytest.mark.asyncio
async def test_create_skill_via_api_with_info_logging(http_client, info_logging_http):
    response = await http_client.post(
        "/api/v1/skills",
        json={
            "name": "info-logging-skill",
            "description": "Created while INFO logging is enabled",
            "content": "# Steps\n1. do the thing",
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["name"] == "info-logging-skill"
    assert "creating skill" in _messages(info_logging_http, "app.services.skill_service")


@pytest.mark.asyncio
async def test_import_skill_via_api_with_info_logging(http_client, info_logging_http):
    response = await http_client.post(
        "/api/v1/skills/import",
        json={
            "skill_md": (
                "---\nname: info-logging-import\n"
                "description: Imported while INFO logging is enabled\n---\n\n# Body\n"
            ),
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["name"] == "info-logging-import"


@pytest.mark.asyncio
async def test_create_file_via_api_with_info_logging(http_client, info_logging_http):
    response = await http_client.post(
        "/api/v1/files",
        json={
            "filename": "info-logging.txt",
            "description": "Created while INFO logging is enabled",
            "data": "SGVsbG8sIFdvcmxkIQ==",
            "mime_type": "text/plain",
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["filename"] == "info-logging.txt"
    assert "creating file" in _messages(info_logging_http, "app.services.file_service")


@pytest.mark.asyncio
async def test_list_projects_via_api_with_info_logging(http_client, info_logging_http):
    created = await http_client.post(
        "/api/v1/projects",
        json={
            "name": "info-logging-project",
            "description": "Listed while INFO logging is enabled",
            "project_type": "development",
        },
    )
    assert created.status_code == 201, created.text

    response = await http_client.get("/api/v1/projects")

    assert response.status_code == 200, response.text
    assert [p["name"] for p in response.json()["projects"]] == ["info-logging-project"]
    assert "listing projects" in _messages(info_logging_http, "app.services.project_service")
    assert "Listing projects" in _messages(
        info_logging_http, "app.repositories.sqlite.project_repository",
    )


@pytest.mark.asyncio
async def test_list_projects_name_filter_via_mcp_with_info_logging(mcp_client, info_logging_mcp):
    await mcp_client.call_tool(
        "execute_forgetful_tool",
        {
            "tool_name": "create_project",
            "arguments": {
                "name": "Forgetful",
                "description": "Filtered while INFO logging is enabled",
                "project_type": "development",
            },
        },
    )

    result = await mcp_client.call_tool(
        "execute_forgetful_tool",
        {"tool_name": "list_projects", "arguments": {"name": "forget"}},
    )

    assert [p["name"] for p in result.data["projects"]] == ["Forgetful"]
    record = next(
        r for r in info_logging_mcp.records
        if r.name == "app.services.project_service" and r.getMessage() == "listing projects"
    )
    assert record.name_filter == "forget"
