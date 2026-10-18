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
