"""Input that PostgreSQL cannot store is refused with a 400 instead of a driver error.

jsonb rejects NaN/Infinity and the NUL character, text and varchar columns reject NUL,
documents.size_bytes is a 32-bit INTEGER and skills.tags carries a GIN index whose keys
cannot exceed roughly 2.7KB. Each of these used to surface as an unhandled asyncpg error
(HTTP 500). The same requests are covered without Docker in
tests/e2e_sqlite/test_model_boundary_db_compat_sqlite.py.
"""
import json

import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio(loop_scope="session")]

JSON = {"content-type": "application/json"}
NUL = "\u0000"
INT32_MAX = 2_147_483_647
SKILL = {"name": "a-skill", "description": "d", "content": "c"}


def _raw_json(payload, token):
    """Serialise ``payload``, writing ``token`` (NaN, Infinity, a NUL escape ...) where it holds "TOKEN".

    json.dumps cannot be told to emit these, and they are exactly what a client sends.
    """
    return json.dumps(payload).replace('"TOKEN"', token)


async def _entity(http_client, name):
    response = await http_client.post(
        "/api/v1/entities", json={"name": name, "entity_type": "Individual"},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


class TestRelationshipMetadata:
    @pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity", '"x\\u0000y"'])
    async def test_create_is_refused(self, http_client, value):
        a = await _entity(http_client, "Alice")
        b = await _entity(http_client, "Bob")
        body = _raw_json(
            {"target_entity_id": b, "relationship_type": "knows", "metadata": {"w": "TOKEN"}}, value,
        )

        response = await http_client.post(
            f"/api/v1/entities/{a}/relationships", content=body, headers=JSON,
        )

        assert response.status_code == 400, response.text
        listed = await http_client.get(f"/api/v1/entities/{a}/relationships")
        assert listed.json()["relationships"] == []

    @pytest.mark.parametrize("value", ["NaN", '"x\\u0000y"'])
    async def test_update_is_refused_and_keeps_the_old_value(self, http_client, value):
        a = await _entity(http_client, "Alice")
        b = await _entity(http_client, "Bob")
        created = await http_client.post(
            f"/api/v1/entities/{a}/relationships",
            json={"target_entity_id": b, "relationship_type": "knows", "metadata": {"w": 1}},
        )
        relationship_id = created.json()["id"]

        response = await http_client.put(
            f"/api/v1/entities/relationships/{relationship_id}",
            content=_raw_json({"metadata": {"w": "TOKEN"}}, value), headers=JSON,
        )

        assert response.status_code == 400, response.text
        listed = await http_client.get(f"/api/v1/entities/{a}/relationships")
        assert listed.json()["relationships"][0]["metadata"] == {"w": 1}


class TestSkill:
    @pytest.mark.parametrize("literal", ["NaN", "Infinity"])
    async def test_non_finite_metadata_is_refused_on_create_and_update(self, http_client, literal):
        body = _raw_json({**SKILL, "metadata": {"score": "TOKEN"}}, literal)
        refused = await http_client.post("/api/v1/skills", content=body, headers=JSON)
        assert refused.status_code == 400, refused.text

        created = await http_client.post("/api/v1/skills", json={
            "name": "a-skill", "description": "d", "content": "c", "metadata": {"score": 1},
        })
        skill_id = created.json()["id"]
        updated = await http_client.put(
            f"/api/v1/skills/{skill_id}", content=_raw_json({"metadata": {"score": "TOKEN"}}, literal),
            headers=JSON,
        )
        assert updated.status_code == 400, updated.text
        assert (await http_client.get(f"/api/v1/skills/{skill_id}")).json()["metadata"] == {"score": 1}

    async def test_nul_character_is_refused_on_create_and_update(self, http_client):
        refused = await http_client.post("/api/v1/skills", json={
            "name": "a-skill", "description": "d", "content": f"a{NUL}b",
        })
        assert refused.status_code == 400, refused.text

        created = await http_client.post("/api/v1/skills", json={
            "name": "a-skill", "description": "d", "content": "c",
        })
        updated = await http_client.put(
            f"/api/v1/skills/{created.json()['id']}", json={"metadata": {"k": f"a{NUL}"}},
        )
        assert updated.status_code == 400, updated.text

class TestPlanning:
    async def test_nul_character_is_refused(self, http_client):
        project = await http_client.post("/api/v1/projects", json={
            "name": "boundary-project", "description": "d", "project_type": "development",
        })
        project_id = project.json()["id"]

        plan = await http_client.post("/api/v1/plans", json={
            "title": "plan", "project_id": project_id, "goal": f"a{NUL}b",
        })
        assert plan.status_code == 400, plan.text

        plan = await http_client.post("/api/v1/plans", json={
            "title": "plan", "project_id": project_id, "status": "active",
        })
        plan_id = plan.json()["id"]
        task = await http_client.post("/api/v1/tasks", json={
            "title": "t", "plan_id": plan_id, "description": f"a{NUL}b",
        })
        assert task.status_code == 400, task.text
        task = await http_client.post("/api/v1/tasks", json={"title": "t", "plan_id": plan_id})
        criterion = await http_client.post(
            f"/api/v1/tasks/{task.json()['id']}/criteria", json={"description": f"a{NUL}"},
        )
        assert criterion.status_code == 400, criterion.text


