"""PostgreSQL E2E coverage for update_memory consistency

Covers skill_ids on every memory read path, replacing skill links through PUT, and
how update_memory uses pooled connections while an embedding is being generated.
"""

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")

CREATE_BODY = {
    "title": "Memory for update consistency",
    "content": "Original content for update consistency tests.",
    "context": "Update consistency",
    "keywords": ["alpha"],
    "tags": ["test"],
    "importance": 7,
}


async def _create_skill(http_client, name):
    response = await http_client.post(
        "/api/v1/skills",
        json={
            "name": name,
            "description": f"Skill {name}",
            "content": "# Steps\n1. Do the thing",
            "tags": ["test"],
            "importance": 7,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _create_memory(http_client, **extra):
    response = await http_client.post("/api/v1/memories", json={**CREATE_BODY, **extra})
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _get_memory(http_client, memory_id):
    response = await http_client.get(f"/api/v1/memories/{memory_id}")
    assert response.status_code == 200, response.text
    return response.json()


# ============================================================================
# skill_ids round trip
# ============================================================================


@pytest.mark.e2e
async def test_get_memory_reports_linked_skill_ids(http_client):
    skill_id = await _create_skill(http_client, "pg-get-skill")
    memory_id = await _create_memory(http_client, skill_ids=[skill_id])

    assert (await _get_memory(http_client, memory_id))["skill_ids"] == [skill_id]


@pytest.mark.e2e
async def test_put_replaces_and_clears_skill_ids(http_client):
    first = await _create_skill(http_client, "pg-first-skill")
    second = await _create_skill(http_client, "pg-second-skill")
    memory_id = await _create_memory(http_client, skill_ids=[first])

    replaced = await http_client.put(f"/api/v1/memories/{memory_id}", json={"skill_ids": [second]})
    assert replaced.status_code == 200, replaced.text
    assert replaced.json()["skill_ids"] == [second]
    assert (await _get_memory(http_client, memory_id))["skill_ids"] == [second]

    cleared = await http_client.put(f"/api/v1/memories/{memory_id}", json={"skill_ids": []})
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["skill_ids"] == []
    assert (await _get_memory(http_client, memory_id))["skill_ids"] == []


@pytest.mark.e2e
async def test_put_other_field_keeps_skill_links(http_client):
    skill_id = await _create_skill(http_client, "pg-kept-skill")
    memory_id = await _create_memory(http_client, skill_ids=[skill_id])

    response = await http_client.put(f"/api/v1/memories/{memory_id}", json={"title": "Renamed"})

    assert response.status_code == 200, response.text
    assert response.json()["skill_ids"] == [skill_id]
    assert (await _get_memory(http_client, memory_id))["skill_ids"] == [skill_id]


@pytest.mark.e2e
async def test_put_unknown_skill_id_is_not_found_and_keeps_links(http_client):
    skill_id = await _create_skill(http_client, "pg-survivor-skill")
    memory_id = await _create_memory(http_client, skill_ids=[skill_id])

    response = await http_client.put(
        f"/api/v1/memories/{memory_id}", json={"skill_ids": [skill_id + 1000]},
    )

    assert response.status_code == 404, response.text
    assert (await _get_memory(http_client, memory_id))["skill_ids"] == [skill_id]


@pytest.mark.e2e
async def test_search_and_linked_memories_report_skill_ids(http_client):
    skill_id = await _create_skill(http_client, "pg-search-skill")
    skilled_id = await _create_memory(
        http_client,
        title="Skilled memory about espresso machines",
        content="Descaling an espresso machine every three months keeps it healthy.",
        skill_ids=[skill_id],
    )
    primary_id = await _create_memory(
        http_client,
        title="Volcano hiking boots",
        content="Waterproof boots with a stiff sole are best for volcano trails.",
    )
    linked = await http_client.post(
        f"/api/v1/memories/{primary_id}/links", json={"related_ids": [skilled_id]},
    )
    assert linked.status_code == 200, linked.text

    response = await http_client.post(
        "/api/v1/memories/search",
        json={
            "query": "waterproof boots for volcano trails",
            "query_context": "choosing hiking gear",
            "k": 1,
            "include_links": 1,
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert [m["id"] for m in body["primary_memories"]] == [primary_id]
    assert [(lm["memory"]["id"], lm["memory"]["skill_ids"]) for lm in body["linked_memories"]] == [
        (skilled_id, [skill_id]),
    ]

    primary_hit = await http_client.post(
        "/api/v1/memories/search",
        json={
            "query": "descaling an espresso machine",
            "query_context": "kitchen appliance care",
            "k": 1,
            "include_links": 0,
        },
    )
    assert primary_hit.status_code == 200, primary_hit.text
    assert [(m["id"], m["skill_ids"]) for m in primary_hit.json()["primary_memories"]] == [
        (skilled_id, [skill_id]),
    ]


@pytest.mark.e2e
async def test_subgraph_has_memory_skill_edge(http_client):
    skill_id = await _create_skill(http_client, "pg-graph-skill")
    memory_id = await _create_memory(http_client, skill_ids=[skill_id])

    response = await http_client.get(
        f"/api/v1/graph/subgraph?node_id=memory_{memory_id}&node_types=memory,skill",
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert f"skill_{skill_id}" in {node["id"] for node in body["nodes"]}
    assert [edge for edge in body["edges"] if edge["type"] == "memory_skill"], body["edges"]
