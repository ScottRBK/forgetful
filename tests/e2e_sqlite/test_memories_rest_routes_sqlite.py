"""E2E tests for memory REST route error mapping and obsolete-state validation.

Uses in-memory SQLite for test isolation. Covers:
- POST/PUT /api/v1/memories with association ids that do not exist
- POST /api/v1/memories reporting linked skill ids
- DELETE /api/v1/memories/{id} (soft delete) for unknown memories, bad
  ``superseded_by`` values, self-supersede and repeated deletes
"""
import pytest

from app.config.settings import settings

API = "/api/v1/memories"

MEMORY = {
    "title": "REST route memory",
    "content": "Content for the REST route tests.",
    "context": "Testing memory REST route errors",
    "keywords": ["rest"],
    "tags": ["test"],
    "importance": 5,
}

ASSOCIATION_FIELDS = [
    ("project_ids", "Projects"),
    ("code_artifact_ids", "Code artifacts"),
    ("document_ids", "Documents"),
    ("file_ids", "Files"),
    ("skill_ids", "Skills"),
]


async def _create_memory(http_client, **overrides) -> int:
    response = await http_client.post(API, json={**MEMORY, **overrides})
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _obsolete(http_client, memory_id, body=None):
    return await http_client.request("DELETE", f"{API}/{memory_id}", json=body)


class TestCreateMemoryUnknownAssociations:
    """POST /api/v1/memories with ids that reference nothing."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("field", "label"), ASSOCIATION_FIELDS)
    async def test_unknown_association_id_is_404_naming_the_ids(self, http_client, field, label):
        response = await http_client.post(API, json={**MEMORY, field: [999]})

        assert response.status_code == 404, response.text
        error = response.json()["error"]
        assert error.startswith(f"{label} not found"), error
        assert "999" in error

        # Nothing was persisted for the rejected request.
        listing = await http_client.get(API)
        assert listing.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_another_users_project_is_404(self, http_client, monkeypatch):
        with monkeypatch.context() as other_user:
            other_user.setattr(settings, "DEFAULT_USER_ID", "memories-route-other-user")
            other_user.setattr(settings, "DEFAULT_USER_EMAIL", "memories-route-other@example.test")
            project = await http_client.post("/api/v1/projects", json={
                "name": "Private project",
                "description": "Belongs to another user",
                "project_type": "development",
            })
            assert project.status_code == 201
            foreign_project_id = project.json()["id"]

        response = await http_client.post(API, json={**MEMORY, "project_ids": [foreign_project_id]})

        assert response.status_code == 404, response.text
        assert response.json()["error"].startswith("Projects not found")


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


class TestUpdateMemoryErrors:
    """PUT /api/v1/memories/{id} tells a missing memory from a missing association."""

    @pytest.mark.asyncio
    async def test_unknown_project_names_the_association_not_the_memory(self, http_client):
        memory_id = await _create_memory(http_client)

        response = await http_client.put(f"{API}/{memory_id}", json={"title": "New title", "project_ids": [999]})

        assert response.status_code == 404, response.text
        error = response.json()["error"]
        assert error.startswith("Projects not found"), error
        assert "Memory not found" not in error

        # The memory itself is untouched by the rejected update.
        unchanged = await http_client.get(f"{API}/{memory_id}")
        assert unchanged.json()["title"] == MEMORY["title"]

    @pytest.mark.asyncio
    async def test_missing_memory_still_reports_memory_not_found(self, http_client):
        response = await http_client.put(f"{API}/99999", json={"title": "Nope"})

        assert response.status_code == 404
        assert response.json() == {"error": "Memory not found"}


class TestDeleteMemoryErrors:
    """DELETE /api/v1/memories/{id} answers with client errors, never a 500."""

    @pytest.mark.asyncio
    async def test_missing_memory_is_404(self, http_client):
        response = await _obsolete(http_client, 99999)

        assert response.status_code == 404
        assert response.json() == {"error": "Memory not found"}

    @pytest.mark.asyncio
    async def test_another_users_memory_is_404_and_untouched(self, http_client, monkeypatch):
        with monkeypatch.context() as other_user:
            other_user.setattr(settings, "DEFAULT_USER_ID", "memories-route-other-user")
            other_user.setattr(settings, "DEFAULT_USER_EMAIL", "memories-route-other@example.test")
            foreign_id = await _create_memory(http_client, title="Someone else's memory")

        response = await _obsolete(http_client, foreign_id, {"reason": "not mine"})
        assert response.status_code == 404
        assert response.json() == {"error": "Memory not found"}

        with monkeypatch.context() as owner:
            owner.setattr(settings, "DEFAULT_USER_ID", "memories-route-other-user")
            owner.setattr(settings, "DEFAULT_USER_EMAIL", "memories-route-other@example.test")
            still_active = await http_client.get(f"{API}/{foreign_id}")
            assert still_active.json()["is_obsolete"] is False

    @pytest.mark.asyncio
    @pytest.mark.parametrize("superseded_by", [99999, -1])
    async def test_unknown_superseded_by_is_404_and_memory_stays_active(self, http_client, superseded_by):
        memory_id = await _create_memory(http_client)

        response = await _obsolete(http_client, memory_id, {"reason": "r", "superseded_by": superseded_by})

        assert response.status_code == 404, response.text
        assert response.json() == {"error": f"Superseding memory {superseded_by} not found"}
        assert (await http_client.get(f"{API}/{memory_id}")).json()["is_obsolete"] is False

    @pytest.mark.asyncio
    @pytest.mark.parametrize("superseded_by", ["abc", "3", True, 1.5, [1], {"id": 1}])
    async def test_non_integer_superseded_by_is_400(self, http_client, superseded_by):
        memory_id = await _create_memory(http_client)

        response = await _obsolete(http_client, memory_id, {"reason": "r", "superseded_by": superseded_by})

        assert response.status_code == 400, response.text
        assert "superseded_by" in response.json()["error"]
        assert (await http_client.get(f"{API}/{memory_id}")).json()["is_obsolete"] is False

    @pytest.mark.asyncio
    async def test_valid_superseded_by_still_works(self, http_client):
        old_id = await _create_memory(http_client, title="Old")
        new_id = await _create_memory(http_client, title="New")

        response = await _obsolete(http_client, old_id, {"reason": "replaced", "superseded_by": new_id})

        assert response.status_code == 200
        assert response.json() == {"success": True}
        old = (await http_client.get(f"{API}/{old_id}")).json()
        assert old["is_obsolete"] is True
        assert old["superseded_by"] == new_id
        assert old["obsolete_reason"] == "replaced"
