"""SQLite coverage for MCP plan ID argument validation."""

import pytest

from tests.plan_id_validation_cases import PlanIdValidationCases as Cases

pytestmark = pytest.mark.asyncio


class TestMcpPlanIdValidationSqlite(Cases):
    pass
