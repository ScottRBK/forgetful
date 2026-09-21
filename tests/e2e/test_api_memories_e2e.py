"""PostgreSQL E2E coverage for the memory REST API."""

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.mark.e2e
async def test_importance_filter_applies_before_pagination(http_client):
    """GET /api/v1/memories filters by importance before paginating."""
    project_response = await http_client.post("/api/v1/projects", json={
        "name": "Importance filter project",
        "description": "Project for testing importance filtering",
        "project_type": "development",
    })
    project_id = project_response.json()["id"]

    await http_client.post("/api/v1/memories", json={
        "title": "High importance memory",
        "content": "High importance content",
        "context": "Filter test",
        "keywords": ["filter"],
        "tags": ["test"],
        "importance": 9,
        "project_ids": [project_id],
    })
    await http_client.post("/api/v1/memories", json={
        "title": "Low importance memory",
        "content": "Low importance content",
        "context": "Filter test",
        "keywords": ["filter"],
        "tags": ["test"],
        "importance": 3,
        "project_ids": [project_id],
    })

    response = await http_client.get(
        f"/api/v1/memories?project_id={project_id}&importance_min=8&limit=1",
    )

    assert response.status_code == 200
    data = response.json()
    assert [memory["title"] for memory in data["memories"]] == [
        "High importance memory",
    ]
    assert data["total"] == 1
