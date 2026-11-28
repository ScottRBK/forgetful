"""PostgreSQL coverage for MCP plan ID argument validation."""

import pytest

from tests.plan_id_validation_cases import PlanIdValidationCases as Cases

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio(loop_scope="session")]


class TestMcpPlanIdValidationE2e(Cases):
    pass
