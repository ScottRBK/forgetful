"""PostgreSQL E2E coverage for memory REST route error mapping and obsolete-state validation."""

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")

API = "/api/v1/memories"

MEMORY = {
    "title": "PG REST route memory",
    "content": "Content for the PostgreSQL REST route tests.",
    "context": "Testing memory REST route errors",
    "keywords": ["rest"],
    "tags": ["test"],
    "importance": 5,
}


async def _create_memory(http_client, **overrides) -> int:
    response = await http_client.post(API, json={**MEMORY, **overrides})
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _obsolete(http_client, memory_id, body=None):
    return await http_client.request("DELETE", f"{API}/{memory_id}", json=body)


@pytest.mark.e2e
@pytest.mark.parametrize(("field", "label"), [
    ("project_ids", "Projects"),
    ("code_artifact_ids", "Code artifacts"),
    ("document_ids", "Documents"),
    ("file_ids", "Files"),
    ("skill_ids", "Skills"),
])
async def test_create_with_unknown_association_id_is_404(http_client, field, label):
    response = await http_client.post(API, json={**MEMORY, field: [999999]})

    assert response.status_code == 404, response.text
    assert response.json()["error"].startswith(f"{label} not found")


@pytest.mark.e2e
async def test_update_with_unknown_project_names_the_association(http_client):
    memory_id = await _create_memory(http_client)

    response = await http_client.put(f"{API}/{memory_id}", json={"title": "Renamed", "project_ids": [999999]})

    assert response.status_code == 404, response.text
    assert response.json()["error"].startswith("Projects not found")


@pytest.mark.e2e
async def test_create_response_reports_linked_skill_ids(http_client):
    skill = await http_client.post("/api/v1/skills", json={
        "name": "pg-memory-route-skill",
        "description": "Skill linked from a memory",
        "content": "# Steps\n1. Do it",
        "tags": ["test"],
        "importance": 7,
    })
    assert skill.status_code == 201, skill.text

    response = await http_client.post(API, json={**MEMORY, "skill_ids": [skill.json()["id"]]})

    assert response.status_code == 201, response.text
    assert response.json()["skill_ids"] == [skill.json()["id"]]


@pytest.mark.e2e
async def test_delete_errors_are_client_errors(http_client):
    memory_id = await _create_memory(http_client)

    missing = await _obsolete(http_client, 999999)
    assert missing.status_code == 404
    assert missing.json() == {"error": "Memory not found"}

    for superseded_by in (999999, 0):
        unknown = await _obsolete(http_client, memory_id, {"reason": "r", "superseded_by": superseded_by})
        assert unknown.status_code == 404, unknown.text
        assert unknown.json() == {"error": f"Superseding memory {superseded_by} not found"}

    bad_type = await _obsolete(http_client, memory_id, {"reason": "r", "superseded_by": "abc"})
    assert bad_type.status_code == 400

    assert (await http_client.get(f"{API}/{memory_id}")).json()["is_obsolete"] is False


@pytest.mark.e2e
async def test_self_supersede_and_second_obsolete_are_rejected(http_client):
    memory_id = await _create_memory(http_client)

    own = await _obsolete(http_client, memory_id, {"reason": "r", "superseded_by": memory_id})
    assert own.status_code == 422, own.text
    assert (await http_client.get(f"{API}/{memory_id}")).json()["is_obsolete"] is False

    assert (await _obsolete(http_client, memory_id, {"reason": "first reason"})).status_code == 200
    before = (await http_client.get(f"{API}/{memory_id}")).json()

    second = await _obsolete(http_client, memory_id, {"reason": "second reason"})
    assert second.status_code == 422, second.text
    assert "already obsolete" in second.json()["error"]

    after = (await http_client.get(f"{API}/{memory_id}")).json()
    assert after["obsolete_reason"] == "first reason"
    assert after["obsoleted_at"] == before["obsoleted_at"]
