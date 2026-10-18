"""E2E tests (in-memory SQLite) for graph API node ids and edge construction.

Covers:
- GET /api/v1/graph/subgraph node_id handling: out-of-range ids, non-canonical
  ids, the placeholder text of the 400 message, and the generic 500 body.
- One entity_relationship edge per (entity pair, relationship type) on every
  endpoint that builds entity edges.
- memory_link edges between memories that sit on different pages of
  GET /api/v1/graph.
- Bulk memory linking with ids that cannot exist.
"""
from urllib.parse import quote

import pytest

from app.services.graph_service import MAX_NODE_ID

NODE_TYPES = [
    "memory",
    "entity",
    "project",
    "document",
    "code_artifact",
    "file",
    "skill",
    "plan",
    "task",
]
HUGE_ID = "99999999999999999999"


@pytest.fixture
def no_auto_link():
    """Create memories without automatic links so tests control every link."""
    from app.config.settings import settings

    original_value = settings.MEMORY_NUM_AUTO_LINK
    settings.MEMORY_NUM_AUTO_LINK = 0
    yield
    settings.MEMORY_NUM_AUTO_LINK = original_value


async def _create_memory(http_client, title, **extra):
    response = await http_client.post("/api/v1/memories", json={
        "title": title,
        "content": f"Content of {title}",
        "context": "graph ids and edges",
        "keywords": ["graph"],
        "tags": ["graph"],
        "importance": 7,
        **extra,
    })
    assert response.status_code in (200, 201), response.text
    return response.json()["id"]


async def _link(http_client, memory_id, related_ids):
    response = await http_client.post(
        f"/api/v1/memories/{memory_id}/links", json={"related_ids": related_ids},
    )
    assert response.status_code == 200, response.text
    return response.json()["linked_ids"]


async def _create_entity(http_client, name):
    response = await http_client.post(
        "/api/v1/entities", json={"name": name, "entity_type": "Individual"},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _create_relationship(http_client, source_id, target_id, relationship_type):
    response = await http_client.post(
        f"/api/v1/entities/{source_id}/relationships",
        json={"target_entity_id": target_id, "relationship_type": relationship_type},
    )
    assert response.status_code == 201, response.text


def _entity_edges(data):
    return [e for e in data["edges"] if e["type"] == "entity_relationship"]


def _relationship_types(data):
    return sorted(e["data"]["relationship_type"] for e in _entity_edges(data))


# ============================================================================
# Subgraph node_id handling
# ============================================================================


class TestSubgraphNodeIds:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("node_type", NODE_TYPES)
    async def test_out_of_range_id_is_a_client_error(self, http_client, node_type):
        response = await http_client.get(
            "/api/v1/graph/subgraph", params={"node_id": f"{node_type}_{HUGE_ID}"},
        )

        assert response.status_code == 400, response.text
        error = response.json()["error"]
        assert "out of range" in error
        assert "too large to convert" not in error

    @pytest.mark.asyncio
    @pytest.mark.parametrize("node_type", ["memory", "entity"])
    async def test_largest_supported_id_is_not_found(self, http_client, node_type):
        response = await http_client.get(
            "/api/v1/graph/subgraph", params={"node_id": f"{node_type}_{MAX_NODE_ID}"},
        )

        assert response.status_code == 404, response.text

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "raw",
        ["memory_1\n", "memory_١", "memory_1 "],
        ids=["trailing-newline", "arabic-indic-digit", "trailing-space"],
    )
    async def test_non_canonical_id_is_rejected(self, http_client, raw):
        await _create_memory(http_client, "Center memory")

        response = await http_client.get(f"/api/v1/graph/subgraph?node_id={quote(raw)}")

        assert response.status_code == 400, response.text
        assert "Invalid node_id format" in response.json()["error"]

    @pytest.mark.asyncio
    async def test_leading_zeros_report_the_canonical_center_node(self, http_client):
        memory_id = await _create_memory(http_client, "Center memory")
        assert memory_id == 1

        response = await http_client.get("/api/v1/graph/subgraph?node_id=memory_001")

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["meta"]["center_node_id"] == "memory_1"
        assert data["meta"]["center_node_id"] in {n["id"] for n in data["nodes"]}

    @pytest.mark.asyncio
    async def test_invalid_format_message_shows_id_placeholders(self, http_client):
        response = await http_client.get("/api/v1/graph/subgraph?node_id=bad")

        assert response.status_code == 400
        error = response.json()["error"]
        assert "'memory_{id}'" in error
        assert "'task_{id}'" in error
        assert "{{" not in error

    @pytest.mark.asyncio
    async def test_unexpected_failure_does_not_leak_exception_text(
        self, http_client, sqlite_app, monkeypatch,
    ):
        async def explode(**_kwargs):
            raise RuntimeError(
                "SELECT secret FROM memories [parameters: ('00000000-0000-0000-0000-000000000001',)]",
            )

        monkeypatch.setattr(sqlite_app.graph_service, "get_subgraph", explode)

        response = await http_client.get("/api/v1/graph/subgraph?node_id=memory_1")

        assert response.status_code == 500
        assert response.json() == {"error": "Internal server error"}
        assert "secret" not in response.text
        assert "parameters" not in response.text


# ============================================================================
# Entity relationship edges: one per (pair, relationship type)
# ============================================================================


class TestEntityRelationshipEdges:
    @pytest.mark.asyncio
    async def test_subgraph_keeps_distinct_types_in_the_same_direction(self, http_client):
        a = await _create_entity(http_client, "A")
        b = await _create_entity(http_client, "B")
        await _create_relationship(http_client, a, b, "knows")
        await _create_relationship(http_client, a, b, "mentors")

        response = await http_client.get(f"/api/v1/graph/subgraph?node_id=entity_{a}")

        assert response.status_code == 200, response.text
        data = response.json()
        assert _relationship_types(data) == ["knows", "mentors"]
        assert data["meta"]["entity_relationship_count"] == 2
        edge_ids = [e["id"] for e in data["edges"]]
        assert len(edge_ids) == len(set(edge_ids))

    @pytest.mark.asyncio
    async def test_subgraph_keeps_distinct_types_in_opposite_directions(self, http_client):
        a = await _create_entity(http_client, "A")
        b = await _create_entity(http_client, "B")
        await _create_relationship(http_client, a, b, "works_with")
        await _create_relationship(http_client, b, a, "manages")

        response = await http_client.get(f"/api/v1/graph/subgraph?node_id=entity_{a}")

        assert response.status_code == 200, response.text
        data = response.json()
        assert _relationship_types(data) == ["manages", "works_with"]
        assert data["meta"]["entity_relationship_count"] == 2

    @pytest.mark.asyncio
    async def test_subgraph_still_merges_reverse_edges_of_the_same_type(self, http_client):
        a = await _create_entity(http_client, "A")
        b = await _create_entity(http_client, "B")
        await _create_relationship(http_client, a, b, "partners_with")
        await _create_relationship(http_client, b, a, "partners_with")

        response = await http_client.get(f"/api/v1/graph/subgraph?node_id=entity_{a}")

        assert len(_entity_edges(response.json())) == 1

    @pytest.mark.asyncio
    async def test_full_graph_keeps_distinct_types(self, http_client):
        a = await _create_entity(http_client, "A")
        b = await _create_entity(http_client, "B")
        await _create_relationship(http_client, a, b, "knows")
        await _create_relationship(http_client, a, b, "mentors")
        await _create_relationship(http_client, b, a, "knows")

        response = await http_client.get("/api/v1/graph?node_types=entity")

        assert response.status_code == 200, response.text
        data = response.json()
        # knows (both directions merged) + mentors
        assert _relationship_types(data) == ["knows", "mentors"]
        assert data["meta"]["entity_relationship_count"] == 2
        edge_ids = [e["id"] for e in data["edges"]]
        assert len(edge_ids) == len(set(edge_ids))

    @pytest.mark.asyncio
    async def test_memory_subgraph_keeps_distinct_types(self, http_client):
        memory_id = await _create_memory(http_client, "Center memory")
        a = await _create_entity(http_client, "A")
        b = await _create_entity(http_client, "B")
        for entity_id in (a, b):
            response = await http_client.post(
                f"/api/v1/entities/{entity_id}/memories", json={"memory_id": memory_id},
            )
            assert response.status_code in (200, 201), response.text
        await _create_relationship(http_client, a, b, "knows")
        await _create_relationship(http_client, a, b, "mentors")

        response = await http_client.get(f"/api/v1/graph/memory/{memory_id}")

        assert response.status_code == 200, response.text
        data = response.json()
        assert _relationship_types(data) == ["knows", "mentors"]
        assert data["meta"]["entity_relationship_count"] == 2


# ============================================================================
# memory_link edges across pages of GET /api/v1/graph
# ============================================================================


def _cross_page_edge(source, target):
    return {
        "id": f"memory_{min(source, target)}_memory_{max(source, target)}",
        "source": f"memory_{source}",
        "target": f"memory_{target}",
        "type": "memory_link",
    }


@pytest.mark.usefixtures("no_auto_link")
class TestCrossPageMemoryLinks:
    @pytest.mark.asyncio
    async def test_link_between_pages_is_delivered_by_both_pages(self, http_client):
        ids = [await _create_memory(http_client, f"Memory {n}") for n in range(1, 5)]
        assert ids == [1, 2, 3, 4]
        await _link(http_client, 1, [4])

        first = await http_client.get("/api/v1/graph?node_types=memory&limit=2&offset=0")
        second = await http_client.get("/api/v1/graph?node_types=memory&limit=2&offset=2")

        assert first.status_code == 200 and second.status_code == 200
        first_data, second_data = first.json(), second.json()
        # Nodes and edges keep describing the page only
        assert {n["id"] for n in first_data["nodes"]} == {"memory_4", "memory_3"}
        assert {n["id"] for n in second_data["nodes"]} == {"memory_2", "memory_1"}
        assert first_data["edges"] == []
        assert second_data["edges"] == []
        # The link is reported by each page that holds one of its endpoints
        assert first_data["cross_page_edges"] == [_cross_page_edge(4, 1)]
        assert second_data["cross_page_edges"] == [_cross_page_edge(1, 4)]
        assert first_data["cross_page_edges"][0]["id"] == second_data["cross_page_edges"][0]["id"]

    @pytest.mark.asyncio
    async def test_page_metadata_still_describes_the_page(self, http_client):
        for n in range(1, 5):
            await _create_memory(http_client, f"Memory {n}")
        await _link(http_client, 1, [4])

        first = (await http_client.get("/api/v1/graph?node_types=memory&limit=2&offset=0")).json()
        second = (await http_client.get("/api/v1/graph?node_types=memory&limit=2&offset=2")).json()

        assert first["meta"]["memory_count"] == 2
        assert first["meta"]["has_more"] is True
        assert first["meta"]["memory_link_count"] == 0
        assert first["meta"]["cross_page_edge_count"] == 1
        assert second["meta"]["memory_count"] == 2
        assert second["meta"]["has_more"] is False
        assert second["meta"]["cross_page_edge_count"] == 1

    @pytest.mark.asyncio
    async def test_links_inside_a_page_stay_in_edges(self, http_client):
        for n in range(1, 5):
            await _create_memory(http_client, f"Memory {n}")
        await _link(http_client, 3, [4])
        await _link(http_client, 1, [4])

        data = (await http_client.get("/api/v1/graph?node_types=memory&limit=2&offset=0")).json()

        assert [e["id"] for e in data["edges"]] == ["memory_3_memory_4"]
        assert data["cross_page_edges"] == [_cross_page_edge(4, 1)]
        assert data["meta"]["memory_link_count"] == 1

    @pytest.mark.asyncio
    async def test_single_page_graph_has_no_cross_page_edges(self, http_client):
        for n in range(1, 4):
            await _create_memory(http_client, f"Memory {n}")
        await _link(http_client, 1, [3])

        data = (await http_client.get("/api/v1/graph?node_types=memory")).json()

        assert [e["id"] for e in data["edges"]] == ["memory_1_memory_3"]
        assert data["cross_page_edges"] == []
        assert data["meta"]["cross_page_edge_count"] == 0

    @pytest.mark.asyncio
    async def test_obsolete_memories_are_not_reported(self, http_client):
        for n in range(1, 4):
            await _create_memory(http_client, f"Memory {n}")
        await _link(http_client, 2, [1, 3])
        deleted = await http_client.request(
            "DELETE", "/api/v1/memories/3", json={"reason": "obsolete for graph test"},
        )
        assert deleted.status_code == 200, deleted.text

        data = (await http_client.get("/api/v1/graph?node_types=memory&limit=1")).json()

        assert {n["id"] for n in data["nodes"]} == {"memory_2"}
        assert data["cross_page_edges"] == [_cross_page_edge(2, 1)]

    @pytest.mark.asyncio
    async def test_project_filter_excludes_links_to_outside_memories(self, http_client):
        project = await http_client.post("/api/v1/projects", json={
            "name": "Graph project",
            "description": "Project for the graph filter test",
            "project_type": "development",
        })
        assert project.status_code in (200, 201), project.text
        project_id = project.json()["id"]
        await _create_memory(http_client, "In project 1", project_ids=[project_id])
        await _create_memory(http_client, "In project 2", project_ids=[project_id])
        await _create_memory(http_client, "Outside project")
        await _link(http_client, 2, [1, 3])

        data = (await http_client.get(
            f"/api/v1/graph?node_types=memory&project_id={project_id}&limit=1",
        )).json()

        assert {n["id"] for n in data["nodes"]} == {"memory_2"}
        assert data["cross_page_edges"] == [_cross_page_edge(2, 1)]


# ============================================================================
# Bulk linking with ids that cannot exist
# ============================================================================


@pytest.mark.usefixtures("no_auto_link")
class TestLinkMemoriesWithImpossibleIds:
    @pytest.mark.asyncio
    async def test_out_of_range_target_is_skipped_and_the_rest_linked(self, http_client):
        for n in range(1, 5):
            await _create_memory(http_client, f"Memory {n}")

        linked = await _link(http_client, 1, [4, 2**70, 3])

        assert linked == [4, 3]
        stored = await http_client.get("/api/v1/memories/1")
        assert sorted(stored.json()["linked_memory_ids"]) == [3, 4]
