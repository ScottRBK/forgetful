"""SQLite coverage for MCP task-action argument validation."""

import pytest

from tests.task_action_validation_cases import TaskActionValidationCases as Cases

pytestmark = pytest.mark.asyncio


class TestMcpTaskActionValidationSqlite(Cases):
    pass
