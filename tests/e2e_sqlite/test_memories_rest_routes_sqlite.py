"""E2E tests for memory REST route error mapping and obsolete-state validation.

Uses in-memory SQLite for test isolation. Covers:
- POST/PUT /api/v1/memories with association ids that do not exist
- POST /api/v1/memories reporting linked skill ids
- DELETE /api/v1/memories/{id} (soft delete) for unknown memories, bad
  ``superseded_by`` values, self-supersede and repeated deletes
"""
import pytest

API = "/api/v1/memories"

MEMORY = {
    "title": "REST route memory",
    "content": "Content for the REST route tests.",
    "context": "Testing memory REST route errors",
    "keywords": ["rest"],
    "tags": ["test"],
    "importance": 5,
}


class TestCreateMemoryResponse:
    """POST /api/v1/memories response mirrors the associations that were linked."""

    @pytest.mark.asyncio
    async def test_response_reports_linked_skill_and_project_ids(self, http_client):
        skill = await http_client.post("/api/v1/skills", json={
            "name": "memory-route-skill",
            "description": "Skill linked from a memory",
            "content": "# Steps\n1. Do it",
            "tags": ["test"],
            "importance": 7,
        })
        assert skill.status_code == 201, skill.text
        project = await http_client.post("/api/v1/projects", json={
            "name": "Memory route project",
            "description": "Project linked from a memory",
            "project_type": "development",
        })
        assert project.status_code == 201, project.text

        response = await http_client.post(API, json={
            **MEMORY,
            "skill_ids": [skill.json()["id"]],
            "project_ids": [project.json()["id"]],
        })

        assert response.status_code == 201, response.text
        body = response.json()
        assert body["skill_ids"] == [skill.json()["id"]]
        assert body["project_ids"] == [project.json()["id"]]
        assert body["file_ids"] == []
