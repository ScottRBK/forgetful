"""E2E tests for Plan REST API endpoints (SQLite)."""
import pytest

from tests.plan_external_ref_cases import (
    TestPlanExternalRefAPI as TestPlanExternalRefAPI,
)


class TestPlanAPICrud:
    """Test Plan GET operations."""

    @pytest.mark.asyncio
    async def test_get_plan_not_found(self, http_client):
        """GET /api/v1/plans/{id} returns 404 for missing plan."""
        response = await http_client.get("/api/v1/plans/99999")
        assert response.status_code == 404
        assert response.json()["error"] == "Plan not found"
