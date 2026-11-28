"""PostgreSQL coverage for MCP task-action argument validation."""

import pytest

from tests.task_action_validation_cases import TaskActionValidationCases as Cases

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio(loop_scope="session")]


class TestMcpTaskActionValidationE2e(Cases):
    pass
