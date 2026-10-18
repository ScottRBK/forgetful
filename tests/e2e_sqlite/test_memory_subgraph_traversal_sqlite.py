"""E2E tests for GET /api/v1/graph/subgraph traversal on in-memory SQLite.

Covers neighbours whose id is a decimal prefix of an id already visited
(entity_1 next to entity_10) and the node_types filter around a center whose
own type is not requested.
"""
import pytest

from app.config.settings import settings


@pytest.fixture(autouse=True)
def disable_auto_linking():
    """Disable auto-linking so only the links created by the test exist."""
    original_value = settings.MEMORY_NUM_AUTO_LINK
    settings.MEMORY_NUM_AUTO_LINK = 0
    yield
    settings.MEMORY_NUM_AUTO_LINK = original_value


async def _create_entities(http_client, count: int) -> list[int]:
    ids = []
    for i in range(count):
        response = await http_client.post("/api/v1/entities", json={
            "name": f"Traversal Entity {i + 1}",
            "entity_type": "Individual",
        })
        assert response.status_code in [200, 201], response.text
        ids.append(response.json()["id"])
    return ids


async def _create_memories(http_client, count: int) -> list[int]:
    ids = []
    for i in range(count):
        response = await http_client.post("/api/v1/memories", json={
            "title": f"Traversal Memory {i + 1}",
            "content": f"Memory number {i + 1} for subgraph traversal",
            "context": "Testing subgraph traversal",
            "keywords": [f"traversal{i + 1}"],
            "tags": ["subgraph-traversal"],
            "importance": 5,
        })
        assert response.status_code in [200, 201], response.text
        ids.append(response.json()["id"])
    return ids


async def _subgraph(http_client, center: str, node_types: str, depth: int = 1) -> dict:
    response = await http_client.get(
        f"/api/v1/graph/subgraph?node_id={center}&depth={depth}&node_types={node_types}",
    )
    assert response.status_code == 200, response.text
    return response.json()


class TestSubgraphPrefixIds:
    """A neighbour whose id is a prefix of the center id must not count as visited."""

    @pytest.mark.asyncio
    async def test_entity_neighbour_with_prefix_id_is_returned(self, http_client):
        ids = await _create_entities(http_client, 10)
        assert ids == list(range(1, 11))
        response = await http_client.post(
            "/api/v1/entities/10/relationships",
            json={"target_entity_id": 1, "relationship_type": "knows"},
        )
        assert response.status_code in [200, 201], response.text

        from_ten = await _subgraph(http_client, "entity_10", "entity")
        from_one = await _subgraph(http_client, "entity_1", "entity")

        assert {n["id"] for n in from_ten["nodes"]} == {"entity_1", "entity_10"}
        assert {n["id"] for n in from_one["nodes"]} == {"entity_1", "entity_10"}
        assert len(from_ten["edges"]) == 1
        assert len(from_one["edges"]) == 1

    @pytest.mark.asyncio
    async def test_memory_neighbour_with_prefix_id_is_returned(self, http_client):
        ids = await _create_memories(http_client, 10)
        assert ids == list(range(1, 11))
        response = await http_client.post(
            "/api/v1/memories/10/links", json={"related_ids": [1]},
        )
        assert response.status_code in [200, 201], response.text

        data = await _subgraph(http_client, "memory_10", "memory")

        assert {n["id"] for n in data["nodes"]} == {"memory_1", "memory_10"}
        assert data["meta"]["memory_link_count"] == 1


class TestSubgraphExcludedCenterType:
    """node_types selects neighbour types; the center type need not be requested."""

    async def _build(self, http_client) -> tuple[int, int, int]:
        project_resp = await http_client.post("/api/v1/projects", json={
            "name": "Traversal Project",
            "description": "Project linked to the center entity",
            "project_type": "development",
        })
        assert project_resp.status_code in [200, 201], project_resp.text
        project_id = project_resp.json()["id"]

        entity_resp = await http_client.post("/api/v1/entities", json={
            "name": "Traversal Entity",
            "entity_type": "Organization",
            "project_ids": [project_id],
        })
        assert entity_resp.status_code in [200, 201], entity_resp.text
        entity_id = entity_resp.json()["id"]

        [memory_id] = await _create_memories(http_client, 1)
        link_resp = await http_client.post(
            f"/api/v1/entities/{entity_id}/memories", json={"memory_id": memory_id},
        )
        assert link_resp.status_code in [200, 201], link_resp.text

        update_resp = await http_client.put(
            f"/api/v1/memories/{memory_id}", json={"project_ids": [project_id]},
        )
        assert update_resp.status_code == 200, update_resp.text
        return project_id, entity_id, memory_id

    @pytest.mark.asyncio
    async def test_entity_center_reaches_project_and_memory(self, http_client):
        project_id, entity_id, memory_id = await self._build(http_client)

        data = await _subgraph(http_client, f"entity_{entity_id}", "project,memory")

        assert {n["id"] for n in data["nodes"]} == {
            f"entity_{entity_id}", f"project_{project_id}", f"memory_{memory_id}",
        }
        edge_types = {e["type"] for e in data["edges"]}
        assert {"entity_project", "entity_memory", "memory_project"} <= edge_types

    @pytest.mark.asyncio
    async def test_entity_center_with_one_requested_type(self, http_client):
        project_id, entity_id, _ = await self._build(http_client)

        data = await _subgraph(http_client, f"entity_{entity_id}", "project")

        assert {n["id"] for n in data["nodes"]} == {
            f"entity_{entity_id}", f"project_{project_id}",
        }
        assert data["meta"]["entity_project_count"] == 1

    @pytest.mark.asyncio
    async def test_project_center_reaches_memory_and_entity(self, http_client):
        project_id, entity_id, memory_id = await self._build(http_client)

        data = await _subgraph(http_client, f"project_{project_id}", "memory,entity")

        assert {n["id"] for n in data["nodes"]} == {
            f"project_{project_id}", f"memory_{memory_id}", f"entity_{entity_id}",
        }
