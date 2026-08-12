"""E2E tests for Task REST API endpoints (SQLite)."""
import pytest


class TestTaskAPICrud:
    """Test Task GET operations."""

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, http_client):
        """GET /api/v1/tasks/{id} returns 404 for missing task."""
        response = await http_client.get("/api/v1/tasks/99999")
        assert response.status_code == 404
        assert response.json()["error"] == "Task not found"
