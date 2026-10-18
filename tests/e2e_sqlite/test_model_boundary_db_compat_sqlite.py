"""Input that the database cannot store is refused with a 400, on every backend.

NaN/Infinity, NUL characters, an INTEGER overflow and an oversized GIN key all fail on
PostgreSQL with an unhandled driver error (500). SQLite accepted them instead, and a NaN
stored in a relationship's metadata made every later graph response fail. These tests run
the real REST and MCP stack on in-memory SQLite; the PostgreSQL counterpart is
tests/e2e/test_model_boundary_db_compat_e2e.py.
"""
import json

import pytest
from fastmcp.exceptions import ToolError

JSON = {"content-type": "application/json"}
NUL = "\u0000"
INT32_MAX = 2_147_483_647
SKILL = {"name": "a-skill", "description": "d", "content": "c"}


def _raw_json(payload, token):
    """Serialise ``payload``, writing ``token`` (NaN, Infinity, 1e999 ...) where it holds "TOKEN".

    json.dumps cannot be told to emit these, and they are exactly what a client sends.
    """
    return json.dumps(payload).replace('"TOKEN"', token)


async def _entity(http_client, name):
    response = await http_client.post(
        "/api/v1/entities", json={"name": name, "entity_type": "Individual"},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _relationship(http_client, source, target, metadata):
    response = await http_client.post(
        f"/api/v1/entities/{source}/relationships",
        json={"target_entity_id": target, "relationship_type": "knows", "metadata": metadata},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _graph_is_healthy(http_client, entity_id):
    for url in ("/api/v1/graph", f"/api/v1/graph/subgraph?node_id=entity_{entity_id}&depth=2"):
        response = await http_client.get(url)
        assert response.status_code == 200, (url, response.text[:200])
        json.loads(response.text, parse_constant=lambda c: pytest.fail(f"{c} in {url}"))


def _assert_rejected(response, *loc):
    """A 400 whose body is valid JSON, names the offending field and echoes no value."""
    assert response.status_code == 400, response.text
    errors = json.loads(response.text, parse_constant=lambda c: pytest.fail(c))["error"]
    assert tuple(errors[0]["loc"]) == loc
    return errors[0]


def _assert_skill_rejected(response, location, error_type):
    """The skills routes return the pydantic message as text; it must name the field and rule."""
    assert response.status_code == 400, response.text
    message = response.json()["error"]
    assert f"\n{location}\n" in message
    assert f"type={error_type}" in message
    return message


async def _plan(http_client, **extra):
    project = await http_client.post("/api/v1/projects", json={
        "name": "boundary-project", "description": "d", "project_type": "development",
    })
    assert project.status_code == 201, project.text
    response = await http_client.post("/api/v1/plans", json={
        "title": "plan", "project_id": project.json()["id"], "status": "active", **extra,
    })
    assert response.status_code == 201, response.text
    return response.json()["id"]


class TestRelationshipMetadata:
    @pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity", "1e999"])
    async def test_create_with_non_finite_number_is_refused_and_graph_stays_healthy(
        self, http_client, token,
    ):
        a = await _entity(http_client, "Alice")
        b = await _entity(http_client, "Bob")
        body = _raw_json(
            {"target_entity_id": b, "relationship_type": "knows", "metadata": {"w": "TOKEN"}}, token,
        )

        response = await http_client.post(
            f"/api/v1/entities/{a}/relationships", content=body, headers=JSON,
        )

        _assert_rejected(response, "metadata", "w")
        listed = await http_client.get(f"/api/v1/entities/{a}/relationships")
        assert listed.json()["relationships"] == []
        await _graph_is_healthy(http_client, a)

    @pytest.mark.parametrize("token", ["NaN", "Infinity", "1e999"])
    async def test_update_with_non_finite_number_is_refused_and_keeps_the_old_value(
        self, http_client, token,
    ):
        a = await _entity(http_client, "Alice")
        b = await _entity(http_client, "Bob")
        relationship_id = await _relationship(http_client, a, b, {"w": 1})

        response = await http_client.put(
            f"/api/v1/entities/relationships/{relationship_id}",
            content=_raw_json({"metadata": {"w": "TOKEN"}}, token), headers=JSON,
        )

        _assert_rejected(response, "metadata", "w")
        listed = await http_client.get(f"/api/v1/entities/{a}/relationships")
        assert listed.json()["relationships"][0]["metadata"] == {"w": 1}
        await _graph_is_healthy(http_client, a)

    async def test_nul_character_is_refused(self, http_client):
        a = await _entity(http_client, "Alice")
        b = await _entity(http_client, "Bob")
        created = await http_client.post(
            f"/api/v1/entities/{a}/relationships",
            json={"target_entity_id": b, "relationship_type": "knows", "metadata": {"a": f"x{NUL}y"}},
        )
        error = _assert_rejected(created, "metadata", "a")
        assert error["type"] == "nul_character"

        relationship_id = await _relationship(http_client, a, b, {"w": 1})
        updated = await http_client.put(
            f"/api/v1/entities/relationships/{relationship_id}", json={"metadata": {"a": [f"x{NUL}"]}},
        )
        _assert_rejected(updated, "metadata", "a", 0)

    async def test_ordinary_metadata_still_works(self, http_client):
        a = await _entity(http_client, "Alice")
        b = await _entity(http_client, "Bob")
        metadata = {"w": 0.5, "n": None, "text": "café \U0001f600", "l": [1, {"x": 2.5}]}
        relationship_id = await _relationship(http_client, a, b, metadata)

        updated = await http_client.put(
            f"/api/v1/entities/relationships/{relationship_id}", json={"metadata": {"w": 2}},
        )

        assert updated.status_code == 200, updated.text
        await _graph_is_healthy(http_client, a)


class TestSkill:
    @pytest.mark.parametrize("literal", ["NaN", "Infinity", "-Infinity"])
    async def test_create_with_non_finite_metadata_is_refused(self, http_client, literal):
        body = _raw_json({**SKILL, "metadata": {"score": "TOKEN"}}, literal)

        response = await http_client.post("/api/v1/skills", content=body, headers=JSON)

        _assert_skill_rejected(response, "metadata.score", "non_finite_number")
        assert (await http_client.get("/api/v1/skills")).json()["total"] == 0

    async def test_update_with_non_finite_metadata_is_refused_and_skill_is_intact(self, http_client):
        created = await http_client.post("/api/v1/skills", json={
            "name": "a-skill", "description": "d", "content": "c", "metadata": {"score": 1},
        })
        skill_id = created.json()["id"]

        response = await http_client.put(
            f"/api/v1/skills/{skill_id}", content='{"metadata": {"score": NaN}}', headers=JSON,
        )

        _assert_skill_rejected(response, "metadata.score", "non_finite_number")
        assert (await http_client.get(f"/api/v1/skills/{skill_id}")).json()["metadata"] == {"score": 1}

    async def test_nul_in_content_is_refused(self, http_client):
        response = await http_client.post("/api/v1/skills", json={
            "name": "a-skill", "description": "d", "content": f"a{NUL}b",
        })

        message = _assert_skill_rejected(response, "content", "nul_character")
        assert "a\u0000b" not in message
        control = await http_client.post("/api/v1/skills", json={
            "name": "a-skill", "description": "d", "content": "ab",
        })
        assert control.status_code == 201

    async def test_nul_in_update_is_refused(self, http_client):
        created = await http_client.post("/api/v1/skills", json={
            "name": "a-skill", "description": "d", "content": "c",
        })

        response = await http_client.put(
            f"/api/v1/skills/{created.json()['id']}", json={"description": f"a{NUL}"},
        )

        _assert_skill_rejected(response, "description", "nul_character")

class TestPlanning:
    async def test_task_text_with_nul_is_refused(self, http_client):
        plan_id = await _plan(http_client)

        created = await http_client.post("/api/v1/tasks", json={
            "title": "t", "plan_id": plan_id, "description": f"a{NUL}b",
        })
        _assert_rejected(created, "description")

        task = await http_client.post("/api/v1/tasks", json={"title": "t", "plan_id": plan_id})
        assert task.status_code == 201
        updated = await http_client.put(
            f"/api/v1/tasks/{task.json()['id']}", json={"title": f"a{NUL}"},
        )
        _assert_rejected(updated, "title")

    async def test_inline_criterion_with_nul_is_refused(self, http_client):
        plan_id = await _plan(http_client)

        response = await http_client.post("/api/v1/tasks", json={
            "title": "t", "plan_id": plan_id, "criteria": [{"description": f"a{NUL}"}],
        })

        _assert_rejected(response, "criteria", 0, "description")

    async def test_criterion_with_nul_is_refused(self, http_client):
        plan_id = await _plan(http_client)
        task = await http_client.post("/api/v1/tasks", json={"title": "t", "plan_id": plan_id})
        task_id = task.json()["id"]

        created = await http_client.post(
            f"/api/v1/tasks/{task_id}/criteria", json={"description": f"a{NUL}b"},
        )
        _assert_rejected(created, "description")

        ok = await http_client.post(f"/api/v1/tasks/{task_id}/criteria", json={"description": "ab"})
        assert ok.status_code == 201
        updated = await http_client.put(
            f"/api/v1/criteria/{ok.json()['id']}", json={"description": f"a{NUL}"},
        )
        _assert_rejected(updated, "description")

    async def test_plan_text_with_nul_is_refused(self, http_client):
        project = await http_client.post("/api/v1/projects", json={
            "name": "p", "description": "d", "project_type": "development",
        })
        project_id = project.json()["id"]

        created = await http_client.post("/api/v1/plans", json={
            "title": "p", "project_id": project_id, "goal": f"a{NUL}b",
        })
        _assert_rejected(created, "goal")

        plan = await http_client.post("/api/v1/plans", json={"title": "p", "project_id": project_id})
        updated = await http_client.put(
            f"/api/v1/plans/{plan.json()['id']}", json={"context": f"a{NUL}b"},
        )
        _assert_rejected(updated, "context")

    async def test_unusual_but_storable_text_is_kept(self, http_client):
        plan_id = await _plan(http_client)
        text = "line\nbreak\ttab é \U0001f600"

        response = await http_client.post("/api/v1/tasks", json={
            "title": "t", "plan_id": plan_id, "description": text,
        })

        assert response.status_code == 201
        assert response.json()["description"] == text


class TestMcpTools:
    async def test_create_skill_with_nul_is_refused(self, mcp_client):
        with pytest.raises(ToolError):
            await mcp_client.call_tool("execute_forgetful_tool", {
                "tool_name": "create_skill",
                "arguments": {"name": "a-skill", "description": "d", "content": f"a{NUL}b"},
            })

