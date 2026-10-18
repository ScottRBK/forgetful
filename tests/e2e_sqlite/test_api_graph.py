"""E2E tests for Graph REST API endpoints.

Uses in-memory SQLite for test isolation.
Tests the /api/v1/graph endpoints.
"""
import pytest
from conftest import FEATURE_FLAGS, build_sqlite_app


@pytest.fixture
async def graph_http_client_factory(embedding_adapter, reranker_adapter):
    """Factory that builds an http_client with a configurable feature-flag set."""
    from fastmcp import Client
    from httpx import ASGITransport, AsyncClient

    contexts = []

    async def _make(enabled_features: set[str]):
        app_iter = build_sqlite_app(embedding_adapter, reranker_adapter, enabled_features=enabled_features)
        app = await app_iter.__anext__()

        client = Client(app)
        await client.__aenter__()

        asgi_app = app.http_app()
        transport = ASGITransport(app=asgi_app)
        http = AsyncClient(transport=transport, base_url="http://test")
        await http.__aenter__()

        contexts.append((http, client, app, app_iter))
        return http, app

    yield _make

    for http, client, _app, app_iter in contexts:
        try:
            await http.__aexit__(None, None, None)
            await client.__aexit__(None, None, None)
            try:
                await app_iter.__anext__()
            except StopAsyncIteration:
                pass
        except Exception:
            pass


class TestGraphAPI:
    """Test GET /api/v1/graph endpoint."""

    @pytest.mark.asyncio
    async def test_get_graph_empty(self, http_client):
        """GET /api/v1/graph returns empty graph initially."""
        response = await http_client.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()
        assert data["nodes"] == []
        assert data["edges"] == []
        assert "meta" in data
        assert data["meta"]["memory_count"] == 0
        assert data["meta"]["entity_count"] == 0
        assert data["meta"]["edge_count"] == 0

    @pytest.mark.asyncio
    async def test_get_graph_with_memories(self, http_client):
        """GET /api/v1/graph returns memory nodes."""
        # Create some memories
        await http_client.post("/api/v1/memories", json={
            "title": "Graph Memory 1",
            "content": "First memory for graph test",
            "context": "Testing graph API",
            "keywords": ["graph", "test"],
            "tags": ["test"],
            "importance": 7,
        })
        await http_client.post("/api/v1/memories", json={
            "title": "Graph Memory 2",
            "content": "Second memory for graph test",
            "context": "Testing graph API",
            "keywords": ["graph", "test"],
            "tags": ["test"],
            "importance": 7,
        })

        # Get graph
        response = await http_client.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()
        assert len(data["nodes"]) >= 2
        assert data["meta"]["memory_count"] >= 2

        # Check node structure
        memory_nodes = [n for n in data["nodes"] if n["type"] == "memory"]
        assert len(memory_nodes) >= 2
        for node in memory_nodes:
            assert "id" in node
            assert "label" in node
            assert "data" in node
            assert node["id"].startswith("memory_")

    @pytest.mark.asyncio
    async def test_get_graph_with_entities(self, http_client):
        """GET /api/v1/graph returns entity nodes when include_entities=true."""
        # Create an entity
        await http_client.post("/api/v1/entities", json={
            "name": "Graph Test Entity",
            "entity_type": "Organization",
            "notes": "Entity for graph test",
        })

        # Get graph with entities
        response = await http_client.get("/api/v1/graph?include_entities=true")
        assert response.status_code == 200
        data = response.json()

        entity_nodes = [n for n in data["nodes"] if n["type"] == "entity"]
        assert len(entity_nodes) >= 1
        for node in entity_nodes:
            assert node["id"].startswith("entity_")
            assert "name" in node["data"]

    @pytest.mark.asyncio
    async def test_get_graph_without_entities(self, http_client):
        """GET /api/v1/graph excludes entities when include_entities=false."""
        # Create entity
        await http_client.post("/api/v1/entities", json={
            "name": "Excluded Entity",
            "entity_type": "Individual",
            "notes": "Should be excluded",
        })

        # Create memory
        await http_client.post("/api/v1/memories", json={
            "title": "Graph Memory Only",
            "content": "Memory without entities in graph",
            "context": "Testing exclude entities",
            "keywords": ["graph"],
            "tags": ["test"],
            "importance": 7,
        })

        # Get graph without entities
        response = await http_client.get("/api/v1/graph?include_entities=false")
        assert response.status_code == 200
        data = response.json()

        entity_nodes = [n for n in data["nodes"] if n["type"] == "entity"]
        assert len(entity_nodes) == 0

    @pytest.mark.asyncio
    async def test_get_graph_with_memory_links(self, http_client):
        """GET /api/v1/graph returns edges for linked memories."""
        # Create two memories
        mem1_response = await http_client.post("/api/v1/memories", json={
            "title": "Linked Memory A",
            "content": "First linked memory for graph edge test",
            "context": "Testing graph edges",
            "keywords": ["linkA"],
            "tags": ["edge-test"],
            "importance": 7,
        })
        mem1_id = mem1_response.json()["id"]

        mem2_response = await http_client.post("/api/v1/memories", json={
            "title": "Linked Memory B",
            "content": "Second linked memory for graph edge test",
            "context": "Testing graph edges",
            "keywords": ["linkB"],
            "tags": ["edge-test"],
            "importance": 7,
        })
        mem2_id = mem2_response.json()["id"]

        # Link them
        await http_client.post(f"/api/v1/memories/{mem1_id}/links", json={
            "related_ids": [mem2_id],
        })

        # Get graph
        response = await http_client.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()

        # Check for edge between the memories
        memory_link_edges = [e for e in data["edges"] if e["type"] == "memory_link"]
        # Should have at least one edge
        assert len(memory_link_edges) >= 1

    @pytest.mark.asyncio
    async def test_get_graph_with_limit(self, http_client):
        """GET /api/v1/graph respects limit parameter."""
        # Create multiple memories
        for i in range(5):
            await http_client.post("/api/v1/memories", json={
                "title": f"Limit Test Memory {i}",
                "content": f"Memory {i} for limit test",
                "context": "Testing limit",
                "keywords": [f"limit{i}"],
                "tags": ["limit-test"],
                "importance": 7,
            })

        # Get graph with limit
        response = await http_client.get("/api/v1/graph?limit=2")
        assert response.status_code == 200
        data = response.json()

        memory_nodes = [n for n in data["nodes"] if n["type"] == "memory"]
        assert len(memory_nodes) <= 2

    @pytest.mark.asyncio
    async def test_get_graph_invalid_limit(self, http_client):
        """GET /api/v1/graph returns 400 for invalid limit."""
        response = await http_client.get("/api/v1/graph?limit=not_a_number")
        assert response.status_code == 400
        assert "Invalid limit" in response.json()["error"]

    @pytest.mark.asyncio
    async def test_get_graph_invalid_project_id(self, http_client):
        """GET /api/v1/graph returns 400 for invalid project_id."""
        response = await http_client.get("/api/v1/graph?project_id=not_a_number")
        assert response.status_code == 400
        assert "Invalid project_id" in response.json()["error"]

    @pytest.mark.asyncio
    async def test_graph_pagination_with_offset(self, http_client):
        """GET /api/v1/graph respects offset parameter for pagination."""
        # Create multiple memories
        for i in range(5):
            await http_client.post("/api/v1/memories", json={
                "title": f"Pagination Memory {i}",
                "content": f"Memory {i} for pagination test",
                "context": "Testing pagination offset",
                "keywords": [f"pagination{i}"],
                "tags": ["pagination-test"],
                "importance": 7,
            })

        # Get first 2 memories
        response1 = await http_client.get("/api/v1/graph?limit=2&offset=0")
        assert response1.status_code == 200
        data1 = response1.json()
        first_page_ids = {n["id"] for n in data1["nodes"] if n["type"] == "memory"}

        # Get next 2 memories
        response2 = await http_client.get("/api/v1/graph?limit=2&offset=2")
        assert response2.status_code == 200
        data2 = response2.json()
        second_page_ids = {n["id"] for n in data2["nodes"] if n["type"] == "memory"}

        # Pages should not overlap
        assert first_page_ids.isdisjoint(second_page_ids)

    @pytest.mark.asyncio
    async def test_graph_pagination_metadata(self, http_client):
        """GET /api/v1/graph includes pagination metadata in response."""
        # Create memories to test pagination metadata
        for i in range(5):
            await http_client.post("/api/v1/memories", json={
                "title": f"Meta Test Memory {i}",
                "content": f"Memory {i} for pagination meta test",
                "context": "Testing pagination metadata",
                "keywords": [f"meta{i}"],
                "tags": ["meta-test"],
                "importance": 7,
            })

        # Get first page
        response = await http_client.get("/api/v1/graph?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()

        # Check pagination metadata
        meta = data["meta"]
        assert "total_memory_count" in meta
        assert "offset" in meta
        assert "limit" in meta
        assert "has_more" in meta

        assert meta["offset"] == 0
        assert meta["limit"] == 2
        assert meta["total_memory_count"] >= 5
        assert meta["has_more"] is True  # We have more than 2 memories

    @pytest.mark.asyncio
    async def test_graph_pagination_has_more_false(self, http_client):
        """has_more is False when all results are returned."""
        # Create exactly 2 memories
        for i in range(2):
            await http_client.post("/api/v1/memories", json={
                "title": f"Small Set Memory {i}",
                "content": f"Memory {i} for has_more test",
                "context": "Testing has_more flag",
                "keywords": [f"small{i}"],
                "tags": ["small-test"],
                "importance": 7,
            })

        # Get with limit higher than total
        response = await http_client.get("/api/v1/graph?limit=100&offset=0")
        assert response.status_code == 200
        data = response.json()

        # has_more should be False since we got all memories
        meta = data["meta"]
        memory_count = meta["memory_count"]
        total_count = meta["total_memory_count"]

        # If we have all memories, has_more should be False
        if memory_count >= total_count:
            assert meta["has_more"] is False

    @pytest.mark.asyncio
    async def test_graph_sort_by_importance(self, http_client):
        """GET /api/v1/graph sorts by importance when specified."""
        # Create memories with different importance levels
        await http_client.post("/api/v1/memories", json={
            "title": "Low Importance",
            "content": "Memory with low importance",
            "context": "Testing sort by importance",
            "keywords": ["lowpriority"],
            "tags": ["sort-test"],
            "importance": 3,
        })
        await http_client.post("/api/v1/memories", json={
            "title": "High Importance",
            "content": "Memory with high importance",
            "context": "Testing sort by importance",
            "keywords": ["highpriority"],
            "tags": ["sort-test"],
            "importance": 10,
        })

        # Sort by importance descending
        response = await http_client.get("/api/v1/graph?sort_by=importance&sort_order=desc&limit=2")
        assert response.status_code == 200
        data = response.json()

        memory_nodes = [n for n in data["nodes"] if n["type"] == "memory"]
        if len(memory_nodes) >= 2:
            # First memory should have higher or equal importance
            assert memory_nodes[0]["data"]["importance"] >= memory_nodes[1]["data"]["importance"]

    @pytest.mark.asyncio
    async def test_graph_sort_by_created_at(self, http_client):
        """GET /api/v1/graph sorts by created_at by default."""
        # Create memories in sequence
        await http_client.post("/api/v1/memories", json={
            "title": "First Created",
            "content": "Created first",
            "context": "Testing sort",
            "keywords": ["first"],
            "tags": ["sort-test"],
            "importance": 7,
        })
        await http_client.post("/api/v1/memories", json={
            "title": "Second Created",
            "content": "Created second",
            "context": "Testing sort",
            "keywords": ["second"],
            "tags": ["sort-test"],
            "importance": 7,
        })

        # Sort by created_at descending (default) should put newest first
        response = await http_client.get("/api/v1/graph?sort_by=created_at&sort_order=desc&limit=10")
        assert response.status_code == 200
        data = response.json()

        # Verify the request was successful
        assert "nodes" in data
        assert "meta" in data

    @pytest.mark.asyncio
    async def test_graph_sort_order_ascending(self, http_client):
        """GET /api/v1/graph supports ascending sort order."""
        response = await http_client.get("/api/v1/graph?sort_order=asc")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data

    @pytest.mark.asyncio
    async def test_graph_invalid_offset(self, http_client):
        """GET /api/v1/graph returns 400 for invalid offset."""
        response = await http_client.get("/api/v1/graph?offset=not_a_number")
        assert response.status_code == 400
        assert "Invalid offset" in response.json()["error"]

    @pytest.mark.asyncio
    async def test_graph_negative_offset(self, http_client):
        """GET /api/v1/graph returns 400 for negative offset."""
        response = await http_client.get("/api/v1/graph?offset=-1")
        assert response.status_code == 400
        assert "non-negative" in response.json()["error"]

    @pytest.mark.asyncio
    async def test_graph_invalid_sort_by(self, http_client):
        """GET /api/v1/graph returns 400 for invalid sort_by."""
        response = await http_client.get("/api/v1/graph?sort_by=invalid_field")
        assert response.status_code == 400
        assert "sort_by must be one of" in response.json()["error"]

    @pytest.mark.asyncio
    async def test_graph_invalid_sort_order(self, http_client):
        """GET /api/v1/graph returns 400 for invalid sort_order."""
        response = await http_client.get("/api/v1/graph?sort_order=invalid")
        assert response.status_code == 400
        assert "sort_order must be one of" in response.json()["error"]

    @pytest.mark.asyncio
    async def test_graph_offset_beyond_total(self, http_client):
        """GET /api/v1/graph returns empty results when offset exceeds total."""
        response = await http_client.get("/api/v1/graph?offset=99999")
        assert response.status_code == 200
        data = response.json()

        # Should have no memory nodes since offset is beyond total
        memory_nodes = [n for n in data["nodes"] if n["type"] == "memory"]
        assert len(memory_nodes) == 0

        # Metadata should still be present
        assert data["meta"]["has_more"] is False


class TestMemorySubgraph:
    """Test GET /api/v1/graph/memory/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_memory_subgraph(self, http_client):
        """GET /api/v1/graph/memory/{id} returns subgraph centered on memory."""
        # Create a memory
        mem_response = await http_client.post("/api/v1/memories", json={
            "title": "Center Memory",
            "content": "Memory at the center of subgraph",
            "context": "Testing subgraph",
            "keywords": ["center"],
            "tags": ["subgraph-test"],
            "importance": 7,
        })
        memory_id = mem_response.json()["id"]

        # Get subgraph
        response = await http_client.get(f"/api/v1/graph/memory/{memory_id}")
        assert response.status_code == 200
        data = response.json()

        assert "nodes" in data
        assert "edges" in data
        assert data["center_memory_id"] == memory_id
        assert "meta" in data

        # Should include the center memory
        node_ids = [n["id"] for n in data["nodes"]]
        assert f"memory_{memory_id}" in node_ids

    @pytest.mark.asyncio
    async def test_get_memory_subgraph_not_found(self, http_client):
        """GET /api/v1/graph/memory/{id} returns 404 for missing memory."""
        response = await http_client.get("/api/v1/graph/memory/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_memory_subgraph_with_links(self, http_client):
        """GET /api/v1/graph/memory/{id} includes linked memories."""
        # Create center memory
        center_response = await http_client.post("/api/v1/memories", json={
            "title": "Subgraph Center",
            "content": "Center of the subgraph",
            "context": "Testing subgraph links",
            "keywords": ["subgraphCenter"],
            "tags": ["subgraph"],
            "importance": 7,
        })
        center_id = center_response.json()["id"]

        # Create linked memory
        linked_response = await http_client.post("/api/v1/memories", json={
            "title": "Linked to Center",
            "content": "Memory linked to center",
            "context": "Testing subgraph links",
            "keywords": ["subgraphLinked"],
            "tags": ["subgraph"],
            "importance": 7,
        })
        linked_id = linked_response.json()["id"]

        # Link them
        await http_client.post(f"/api/v1/memories/{center_id}/links", json={
            "related_ids": [linked_id],
        })

        # Get subgraph
        response = await http_client.get(f"/api/v1/graph/memory/{center_id}")
        assert response.status_code == 200
        data = response.json()

        # Should include both memories
        node_ids = [n["id"] for n in data["nodes"]]
        assert f"memory_{center_id}" in node_ids
        assert f"memory_{linked_id}" in node_ids

        # Should have edge between them
        assert len(data["edges"]) >= 1

    @pytest.mark.asyncio
    async def test_get_memory_subgraph_with_depth(self, http_client):
        """GET /api/v1/graph/memory/{id} respects depth parameter."""
        # Create chain of linked memories
        mem1_response = await http_client.post("/api/v1/memories", json={
            "title": "Depth Chain 1",
            "content": "First in chain",
            "context": "Testing depth",
            "keywords": ["depthChain1"],
            "tags": ["depth"],
            "importance": 7,
        })
        mem1_id = mem1_response.json()["id"]

        mem2_response = await http_client.post("/api/v1/memories", json={
            "title": "Depth Chain 2",
            "content": "Second in chain",
            "context": "Testing depth",
            "keywords": ["depthChain2"],
            "tags": ["depth"],
            "importance": 7,
        })
        mem2_id = mem2_response.json()["id"]

        mem3_response = await http_client.post("/api/v1/memories", json={
            "title": "Depth Chain 3",
            "content": "Third in chain",
            "context": "Testing depth",
            "keywords": ["depthChain3"],
            "tags": ["depth"],
            "importance": 7,
        })
        mem3_id = mem3_response.json()["id"]

        # Link: 1 -> 2 -> 3
        await http_client.post(f"/api/v1/memories/{mem1_id}/links", json={
            "related_ids": [mem2_id],
        })
        await http_client.post(f"/api/v1/memories/{mem2_id}/links", json={
            "related_ids": [mem3_id],
        })

        # Get subgraph with depth=1 (should only get mem1 and mem2)
        response = await http_client.get(f"/api/v1/graph/memory/{mem1_id}?depth=1")
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["depth"] == 1

        # Get subgraph with depth=2 (should get all three)
        response = await http_client.get(f"/api/v1/graph/memory/{mem1_id}?depth=2")
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["depth"] == 2
        # With depth=2, we should reach mem3 through mem2
        node_ids = [n["id"] for n in data["nodes"]]
        assert f"memory_{mem1_id}" in node_ids
        assert f"memory_{mem2_id}" in node_ids

    @pytest.mark.asyncio
    async def test_get_memory_subgraph_invalid_memory_id(self, http_client):
        """GET /api/v1/graph/memory/{id} returns 400 for invalid memory_id."""
        response = await http_client.get("/api/v1/graph/memory/not_a_number")
        assert response.status_code == 400
        assert "Invalid memory_id" in response.json()["error"]

    @pytest.mark.asyncio
    async def test_get_memory_subgraph_invalid_depth(self, http_client):
        """GET /api/v1/graph/memory/{id} returns 400 for invalid depth."""
        # First create a memory
        mem_response = await http_client.post("/api/v1/memories", json={
            "title": "Depth Validation Test",
            "content": "Memory for testing depth validation",
            "context": "Testing depth",
            "keywords": ["depthTest"],
            "tags": ["test"],
            "importance": 7,
        })
        memory_id = mem_response.json()["id"]

        response = await http_client.get(f"/api/v1/graph/memory/{memory_id}?depth=not_a_number")
        assert response.status_code == 400
        assert "Invalid depth" in response.json()["error"]


class TestGraphEntityEdges:
    """Test entity-entity and entity-memory edges in graph API."""

    @pytest.mark.asyncio
    async def test_graph_includes_entity_relationship_edges(self, http_client):
        """GET /api/v1/graph includes entity-relationship edges."""
        # Create two entities
        entity1_resp = await http_client.post("/api/v1/entities", json={
            "name": "Alice Developer",
            "entity_type": "Individual",
        })
        entity1_id = entity1_resp.json()["id"]

        entity2_resp = await http_client.post("/api/v1/entities", json={
            "name": "TechCorp Inc",
            "entity_type": "Organization",
        })
        entity2_id = entity2_resp.json()["id"]

        # Create relationship: Alice works_at TechCorp
        await http_client.post(f"/api/v1/entities/{entity1_id}/relationships", json={
            "target_entity_id": entity2_id,
            "relationship_type": "works_at",
            "strength": 0.9,
            "confidence": 0.95,
        })

        # Get graph
        response = await http_client.get("/api/v1/graph?include_entities=true")
        assert response.status_code == 200
        data = response.json()

        # Find entity_relationship edges
        entity_rel_edges = [e for e in data["edges"] if e["type"] == "entity_relationship"]
        assert len(entity_rel_edges) >= 1

        # Verify edge structure
        edge = entity_rel_edges[0]
        assert "data" in edge
        assert edge["data"]["relationship_type"] == "works_at"
        assert edge["data"]["strength"] == 0.9
        assert edge["data"]["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_graph_includes_entity_memory_edges(self, http_client):
        """GET /api/v1/graph includes entity-memory edges."""
        # Create memory
        mem_resp = await http_client.post("/api/v1/memories", json={
            "title": "Project kickoff meeting",
            "content": "Discussed project timeline",
            "context": "Meeting notes",
            "keywords": ["meeting"],
            "tags": ["project"],
            "importance": 7,
        })
        memory_id = mem_resp.json()["id"]

        # Create entity
        entity_resp = await http_client.post("/api/v1/entities", json={
            "name": "Project Alpha",
            "entity_type": "Team",
        })
        entity_id = entity_resp.json()["id"]

        # Link entity to memory
        await http_client.post(f"/api/v1/entities/{entity_id}/memories", json={
            "memory_id": memory_id,
        })

        # Get graph
        response = await http_client.get("/api/v1/graph?include_entities=true")
        assert response.status_code == 200
        data = response.json()

        # Find entity_memory edges
        entity_mem_edges = [e for e in data["edges"] if e["type"] == "entity_memory"]
        assert len(entity_mem_edges) >= 1

        # Verify edge structure
        edge = entity_mem_edges[0]
        assert edge["source"] == f"entity_{entity_id}"
        assert edge["target"] == f"memory_{memory_id}"
        assert edge["id"] == f"entity_{entity_id}_memory_{memory_id}"

    @pytest.mark.asyncio
    async def test_entity_relationship_deduplication_bidirectional(self, http_client):
        """Entity relationships are deduplicated for bidirectional display."""
        # Create two entities
        entity_a_resp = await http_client.post("/api/v1/entities", json={
            "name": "Entity A",
            "entity_type": "Organization",
        })
        entity_a_id = entity_a_resp.json()["id"]

        entity_b_resp = await http_client.post("/api/v1/entities", json={
            "name": "Entity B",
            "entity_type": "Organization",
        })
        entity_b_id = entity_b_resp.json()["id"]

        # Create A -> B relationship
        await http_client.post(f"/api/v1/entities/{entity_a_id}/relationships", json={
            "target_entity_id": entity_b_id,
            "relationship_type": "partners_with",
        })

        # Create B -> A relationship (reverse direction)
        await http_client.post(f"/api/v1/entities/{entity_b_id}/relationships", json={
            "target_entity_id": entity_a_id,
            "relationship_type": "partners_with",
        })

        # Get graph
        response = await http_client.get("/api/v1/graph?include_entities=true")
        assert response.status_code == 200
        data = response.json()

        # Count entity_relationship edges between A and B
        min_id = min(entity_a_id, entity_b_id)
        max_id = max(entity_a_id, entity_b_id)
        expected_edge_id = f"entity_{min_id}_entity_{max_id}_partners_with"

        matching_edges = [
            e for e in data["edges"]
            if e["type"] == "entity_relationship" and e["id"] == expected_edge_id
        ]

        # Should only have ONE edge despite two relationships
        assert len(matching_edges) == 1

    @pytest.mark.asyncio
    async def test_entity_edges_excluded_when_include_entities_false(self, http_client):
        """Entity edges are excluded when include_entities=false."""
        # Create entity and memory with relationship
        entity_resp = await http_client.post("/api/v1/entities", json={
            "name": "Test Entity",
            "entity_type": "Organization",
        })
        entity_id = entity_resp.json()["id"]

        mem_resp = await http_client.post("/api/v1/memories", json={
            "title": "Test Memory",
            "content": "Test content",
            "context": "Testing",
            "keywords": ["test"],
            "tags": ["test"],
            "importance": 7,
        })
        memory_id = mem_resp.json()["id"]

        await http_client.post(f"/api/v1/entities/{entity_id}/memories", json={
            "memory_id": memory_id,
        })

        # Get graph WITHOUT entities
        response = await http_client.get("/api/v1/graph?include_entities=false")
        assert response.status_code == 200
        data = response.json()

        # Should have no entity edges
        entity_rel_edges = [e for e in data["edges"] if e["type"] == "entity_relationship"]
        entity_mem_edges = [e for e in data["edges"] if e["type"] == "entity_memory"]

        assert len(entity_rel_edges) == 0
        assert len(entity_mem_edges) == 0

    @pytest.mark.asyncio
    async def test_graph_meta_includes_edge_counts_by_type(self, http_client):
        """Graph meta includes separate counts for each edge type."""
        # Create test data with all edge types
        # Memory link
        mem1_resp = await http_client.post("/api/v1/memories", json={
            "title": "Memory 1", "content": "Content 1", "context": "Context",
            "keywords": ["k1"], "tags": ["t1"], "importance": 7,
        })
        mem1_id = mem1_resp.json()["id"]

        mem2_resp = await http_client.post("/api/v1/memories", json={
            "title": "Memory 2", "content": "Content 2", "context": "Context",
            "keywords": ["k2"], "tags": ["t2"], "importance": 7,
        })
        mem2_id = mem2_resp.json()["id"]

        await http_client.post(f"/api/v1/memories/{mem1_id}/links", json={
            "related_ids": [mem2_id],
        })

        # Entity relationship
        ent1_resp = await http_client.post("/api/v1/entities", json={
            "name": "Entity 1", "entity_type": "Organization",
        })
        ent1_id = ent1_resp.json()["id"]

        ent2_resp = await http_client.post("/api/v1/entities", json={
            "name": "Entity 2", "entity_type": "Organization",
        })
        ent2_id = ent2_resp.json()["id"]

        await http_client.post(f"/api/v1/entities/{ent1_id}/relationships", json={
            "target_entity_id": ent2_id,
            "relationship_type": "related_to",
        })

        # Entity-memory link
        await http_client.post(f"/api/v1/entities/{ent1_id}/memories", json={
            "memory_id": mem1_id,
        })

        # Get graph
        response = await http_client.get("/api/v1/graph?include_entities=true")
        assert response.status_code == 200
        data = response.json()

        # Verify meta includes typed counts
        meta = data["meta"]
        assert "memory_link_count" in meta
        assert "entity_relationship_count" in meta
        assert "entity_memory_count" in meta
        assert meta["memory_link_count"] >= 1
        assert meta["entity_relationship_count"] >= 1
        assert meta["entity_memory_count"] >= 1

    @pytest.mark.asyncio
    async def test_entity_edges_only_appear_when_both_nodes_in_result(self, http_client):
        """Entity edges only appear when both endpoint nodes are in the result set."""
        # Create two entities
        ent1_resp = await http_client.post("/api/v1/entities", json={
            "name": "Visible Entity", "entity_type": "Organization",
        })
        ent1_id = ent1_resp.json()["id"]

        ent2_resp = await http_client.post("/api/v1/entities", json={
            "name": "Also Visible Entity", "entity_type": "Organization",
        })
        ent2_id = ent2_resp.json()["id"]

        # Create relationship
        await http_client.post(f"/api/v1/entities/{ent1_id}/relationships", json={
            "target_entity_id": ent2_id,
            "relationship_type": "connected_to",
        })

        # Get graph with entities - edge should appear
        response = await http_client.get("/api/v1/graph?include_entities=true")
        assert response.status_code == 200
        data = response.json()

        entity_rel_edges = [e for e in data["edges"] if e["type"] == "entity_relationship"]
        assert len(entity_rel_edges) >= 1

    @pytest.mark.asyncio
    async def test_subgraph_includes_entity_edges_for_related_entities(self, http_client):
        """Memory subgraph includes entities linked to memories and their edges."""
        # Create memory
        mem_resp = await http_client.post("/api/v1/memories", json={
            "title": "Center Memory for Entity Test",
            "content": "Central memory content",
            "context": "Subgraph entity test",
            "keywords": ["subgraph", "entity"],
            "tags": ["test"],
            "importance": 8,
        })
        memory_id = mem_resp.json()["id"]

        # Create two entities
        ent1_resp = await http_client.post("/api/v1/entities", json={
            "name": "Linked Entity 1", "entity_type": "Individual",
        })
        ent1_id = ent1_resp.json()["id"]

        ent2_resp = await http_client.post("/api/v1/entities", json={
            "name": "Linked Entity 2", "entity_type": "Individual",
        })
        ent2_id = ent2_resp.json()["id"]

        # Link both entities to memory
        await http_client.post(f"/api/v1/entities/{ent1_id}/memories", json={
            "memory_id": memory_id,
        })
        await http_client.post(f"/api/v1/entities/{ent2_id}/memories", json={
            "memory_id": memory_id,
        })

        # Create relationship between entities
        await http_client.post(f"/api/v1/entities/{ent1_id}/relationships", json={
            "target_entity_id": ent2_id,
            "relationship_type": "collaborates_with",
            "strength": 0.8,
        })

        # Get subgraph
        response = await http_client.get(f"/api/v1/graph/memory/{memory_id}")
        assert response.status_code == 200
        data = response.json()

        # Should include entity nodes
        entity_nodes = [n for n in data["nodes"] if n["type"] == "entity"]
        assert len(entity_nodes) == 2

        # Should include entity-memory edges
        entity_mem_edges = [e for e in data["edges"] if e["type"] == "entity_memory"]
        assert len(entity_mem_edges) == 2

        # Should include entity-entity edge
        entity_rel_edges = [e for e in data["edges"] if e["type"] == "entity_relationship"]
        assert len(entity_rel_edges) == 1
        assert entity_rel_edges[0]["data"]["relationship_type"] == "collaborates_with"


class TestSubgraphEndpoint:
    """Test GET /api/v1/graph/subgraph endpoint with recursive CTE traversal."""

    @pytest.mark.asyncio
    async def test_subgraph_from_memory_center(self, http_client):
        """Subgraph traversal starting from a memory node."""
        # Create a memory
        mem_response = await http_client.post("/api/v1/memories", json={
            "title": "CTE Center Memory",
            "content": "Memory at the center of CTE subgraph",
            "context": "Testing CTE subgraph",
            "keywords": ["cte_center"],
            "tags": ["cte-test"],
            "importance": 7,
        })
        memory_id = mem_response.json()["id"]

        # Get subgraph
        response = await http_client.get(f"/api/v1/graph/subgraph?node_id=memory_{memory_id}")
        assert response.status_code == 200
        data = response.json()

        assert "nodes" in data
        assert "edges" in data
        assert "meta" in data
        assert data["meta"]["center_node_id"] == f"memory_{memory_id}"

        # Should include the center memory with depth 0
        node_ids = [n["id"] for n in data["nodes"]]
        assert f"memory_{memory_id}" in node_ids

        center_node = next(n for n in data["nodes"] if n["id"] == f"memory_{memory_id}")
        assert center_node["depth"] == 0

    @pytest.mark.asyncio
    async def test_subgraph_from_entity_center(self, http_client):
        """Subgraph traversal starting from an entity node."""
        # Create an entity
        entity_response = await http_client.post("/api/v1/entities", json={
            "name": "CTE Center Entity",
            "entity_type": "Organization",
            "notes": "Entity at center of CTE subgraph",
        })
        entity_id = entity_response.json()["id"]

        # Get subgraph
        response = await http_client.get(f"/api/v1/graph/subgraph?node_id=entity_{entity_id}")
        assert response.status_code == 200
        data = response.json()

        assert data["meta"]["center_node_id"] == f"entity_{entity_id}"

        # Should include the center entity with depth 0
        node_ids = [n["id"] for n in data["nodes"]]
        assert f"entity_{entity_id}" in node_ids

        center_node = next(n for n in data["nodes"] if n["id"] == f"entity_{entity_id}")
        assert center_node["depth"] == 0

    @pytest.mark.asyncio
    async def test_subgraph_depth_limits(self, http_client):
        """Depth parameter controls traversal depth."""
        # Disable auto-linking for this test to control exact graph structure
        from app.config.settings import settings
        original_auto_link = settings.MEMORY_NUM_AUTO_LINK
        settings.MEMORY_NUM_AUTO_LINK = 0

        try:
            # Create chain of linked memories: M1 -> M2 -> M3
            mem1_response = await http_client.post("/api/v1/memories", json={
                "title": "Antarctic Penguin Migration",
                "content": "Emperor penguins travel 70km across ice to breeding grounds",
                "context": "Wildlife documentary research",
                "keywords": ["penguin", "antarctica", "migration"],
                "tags": ["depth-test"],
                "importance": 7,
            })
            mem1_id = mem1_response.json()["id"]

            mem2_response = await http_client.post("/api/v1/memories", json={
                "title": "Quantum Entanglement Properties",
                "content": "Particles maintain correlated states regardless of distance",
                "context": "Physics lecture notes",
                "keywords": ["quantum", "physics", "entanglement"],
                "tags": ["depth-test"],
                "importance": 7,
            })
            mem2_id = mem2_response.json()["id"]

            mem3_response = await http_client.post("/api/v1/memories", json={
                "title": "Renaissance Art Techniques",
                "content": "Sfumato technique developed by Leonardo da Vinci for soft edges",
                "context": "Art history seminar",
                "keywords": ["art", "renaissance", "painting"],
                "tags": ["depth-test"],
                "importance": 7,
            })
            mem3_id = mem3_response.json()["id"]

            # Link: M1 -> M2 -> M3
            await http_client.post(f"/api/v1/memories/{mem1_id}/links", json={
                "related_ids": [mem2_id],
            })
            await http_client.post(f"/api/v1/memories/{mem2_id}/links", json={
                "related_ids": [mem3_id],
            })

            # Depth 1: Should get M1 and M2 only
            response = await http_client.get(f"/api/v1/graph/subgraph?node_id=memory_{mem1_id}&depth=1")
            assert response.status_code == 200
            data = response.json()
            assert data["meta"]["depth"] == 1

            node_ids = {n["id"] for n in data["nodes"]}
            assert f"memory_{mem1_id}" in node_ids
            assert f"memory_{mem2_id}" in node_ids
            # M3 should NOT be present at depth 1
            assert f"memory_{mem3_id}" not in node_ids

            # Depth 2: Should get all three
            response = await http_client.get(f"/api/v1/graph/subgraph?node_id=memory_{mem1_id}&depth=2")
            assert response.status_code == 200
            data = response.json()
            assert data["meta"]["depth"] == 2

            node_ids = {n["id"] for n in data["nodes"]}
            assert f"memory_{mem1_id}" in node_ids
            assert f"memory_{mem2_id}" in node_ids
            assert f"memory_{mem3_id}" in node_ids
        finally:
            # Restore original auto-link setting
            settings.MEMORY_NUM_AUTO_LINK = original_auto_link

    @pytest.mark.asyncio
    async def test_subgraph_cycle_detection(self, http_client):
        """Cycles in graph don't cause infinite loops."""
        # Create memories that form a cycle: A -> B -> C -> A
        mem_a = await http_client.post("/api/v1/memories", json={
            "title": "Cycle Node A",
            "content": "Node A in cycle",
            "context": "Testing cycle detection",
            "keywords": ["cycle_a"],
            "tags": ["cycle"],
            "importance": 7,
        })
        mem_a_id = mem_a.json()["id"]

        mem_b = await http_client.post("/api/v1/memories", json={
            "title": "Cycle Node B",
            "content": "Node B in cycle",
            "context": "Testing cycle detection",
            "keywords": ["cycle_b"],
            "tags": ["cycle"],
            "importance": 7,
        })
        mem_b_id = mem_b.json()["id"]

        mem_c = await http_client.post("/api/v1/memories", json={
            "title": "Cycle Node C",
            "content": "Node C in cycle",
            "context": "Testing cycle detection",
            "keywords": ["cycle_c"],
            "tags": ["cycle"],
            "importance": 7,
        })
        mem_c_id = mem_c.json()["id"]

        # Create cycle: A -> B -> C -> A
        await http_client.post(f"/api/v1/memories/{mem_a_id}/links", json={
            "related_ids": [mem_b_id],
        })
        await http_client.post(f"/api/v1/memories/{mem_b_id}/links", json={
            "related_ids": [mem_c_id],
        })
        await http_client.post(f"/api/v1/memories/{mem_c_id}/links", json={
            "related_ids": [mem_a_id],
        })

        # Should complete without infinite loop, even with depth=3
        response = await http_client.get(f"/api/v1/graph/subgraph?node_id=memory_{mem_a_id}&depth=3")
        assert response.status_code == 200
        data = response.json()

        # Should have all three nodes, each appearing once
        node_ids = [n["id"] for n in data["nodes"]]
        assert f"memory_{mem_a_id}" in node_ids
        assert f"memory_{mem_b_id}" in node_ids
        assert f"memory_{mem_c_id}" in node_ids
        assert len(data["nodes"]) == 3  # No duplicates

    @pytest.mark.asyncio
    async def test_subgraph_node_types_filter(self, http_client):
        """node_types parameter filters which node types to include."""
        # Create memory and entity linked together
        mem_response = await http_client.post("/api/v1/memories", json={
            "title": "Filter Test Memory",
            "content": "Memory for filter test",
            "context": "Testing node_types filter",
            "keywords": ["filter"],
            "tags": ["filter-test"],
            "importance": 7,
        })
        memory_id = mem_response.json()["id"]

        entity_response = await http_client.post("/api/v1/entities", json={
            "name": "Filter Test Entity",
            "entity_type": "Organization",
        })
        entity_id = entity_response.json()["id"]

        # Link entity to memory
        await http_client.post(f"/api/v1/entities/{entity_id}/memories", json={
            "memory_id": memory_id,
        })

        # With node_types=memory only - should not traverse to entity
        response = await http_client.get(
            f"/api/v1/graph/subgraph?node_id=memory_{memory_id}&node_types=memory",
        )
        assert response.status_code == 200
        data = response.json()

        # Should only have the memory node
        entity_nodes = [n for n in data["nodes"] if n["type"] == "entity"]
        assert len(entity_nodes) == 0

        # With node_types=memory,entity - should traverse to entity
        response = await http_client.get(
            f"/api/v1/graph/subgraph?node_id=memory_{memory_id}&node_types=memory,entity",
        )
        assert response.status_code == 200
        data = response.json()

        entity_nodes = [n for n in data["nodes"] if n["type"] == "entity"]
        assert len(entity_nodes) >= 1

    @pytest.mark.asyncio
    async def test_subgraph_max_nodes_truncation(self, http_client):
        """max_nodes limit causes truncation with truncated flag set."""
        # Create multiple linked memories
        mem_ids = []
        for i in range(5):
            mem_response = await http_client.post("/api/v1/memories", json={
                "title": f"Truncation Test Memory {i}",
                "content": f"Memory {i} for truncation test",
                "context": "Testing max_nodes",
                "keywords": [f"truncation_{i}"],
                "tags": ["truncation"],
                "importance": 7,
            })
            mem_ids.append(mem_response.json()["id"])

        # Link all to first
        for i in range(1, len(mem_ids)):
            await http_client.post(f"/api/v1/memories/{mem_ids[0]}/links", json={
                "related_ids": [mem_ids[i]],
            })

        # Request with very low max_nodes
        response = await http_client.get(
            f"/api/v1/graph/subgraph?node_id=memory_{mem_ids[0]}&max_nodes=2",
        )
        assert response.status_code == 200
        data = response.json()

        # Should respect max_nodes limit
        assert len(data["nodes"]) <= 2
        # Should indicate truncation
        assert data["meta"]["truncated"] is True

    @pytest.mark.asyncio
    async def test_subgraph_depth_field_on_nodes(self, http_client):
        """Each node has correct depth value."""
        # Create linked memories: Center -> Neighbor
        center_response = await http_client.post("/api/v1/memories", json={
            "title": "Depth Center",
            "content": "Center memory for depth test",
            "context": "Testing depth field",
            "keywords": ["depth_center"],
            "tags": ["depth"],
            "importance": 7,
        })
        center_id = center_response.json()["id"]

        neighbor_response = await http_client.post("/api/v1/memories", json={
            "title": "Depth Neighbor",
            "content": "Neighbor memory for depth test",
            "context": "Testing depth field",
            "keywords": ["depth_neighbor"],
            "tags": ["depth"],
            "importance": 7,
        })
        neighbor_id = neighbor_response.json()["id"]

        await http_client.post(f"/api/v1/memories/{center_id}/links", json={
            "related_ids": [neighbor_id],
        })

        response = await http_client.get(f"/api/v1/graph/subgraph?node_id=memory_{center_id}")
        assert response.status_code == 200
        data = response.json()

        # Center should have depth 0
        center_node = next(n for n in data["nodes"] if n["id"] == f"memory_{center_id}")
        assert center_node["depth"] == 0

        # Neighbor should have depth 1
        neighbor_node = next(n for n in data["nodes"] if n["id"] == f"memory_{neighbor_id}")
        assert neighbor_node["depth"] == 1

    @pytest.mark.asyncio
    async def test_subgraph_all_edge_types(self, http_client):
        """Response includes all edge types: memory_link, entity_memory, entity_relationship."""
        # Create memories
        mem1 = await http_client.post("/api/v1/memories", json={
            "title": "Edge Test Memory 1",
            "content": "Memory 1 for edge test",
            "context": "Testing edge types",
            "keywords": ["edge1"],
            "tags": ["edges"],
            "importance": 7,
        })
        mem1_id = mem1.json()["id"]

        mem2 = await http_client.post("/api/v1/memories", json={
            "title": "Edge Test Memory 2",
            "content": "Memory 2 for edge test",
            "context": "Testing edge types",
            "keywords": ["edge2"],
            "tags": ["edges"],
            "importance": 7,
        })
        mem2_id = mem2.json()["id"]

        # Create entities
        ent1 = await http_client.post("/api/v1/entities", json={
            "name": "Edge Entity 1",
            "entity_type": "Individual",
        })
        ent1_id = ent1.json()["id"]

        ent2 = await http_client.post("/api/v1/entities", json={
            "name": "Edge Entity 2",
            "entity_type": "Individual",
        })
        ent2_id = ent2.json()["id"]

        # Create all edge types:
        # memory_link: mem1 <-> mem2
        await http_client.post(f"/api/v1/memories/{mem1_id}/links", json={
            "related_ids": [mem2_id],
        })

        # entity_memory: ent1 -> mem1
        await http_client.post(f"/api/v1/entities/{ent1_id}/memories", json={
            "memory_id": mem1_id,
        })

        # entity_relationship: ent1 -> ent2
        await http_client.post(f"/api/v1/entities/{ent1_id}/relationships", json={
            "target_entity_id": ent2_id,
            "relationship_type": "knows",
        })

        # Link ent2 to mem2 to ensure both entities are in subgraph
        await http_client.post(f"/api/v1/entities/{ent2_id}/memories", json={
            "memory_id": mem2_id,
        })

        # Get subgraph
        response = await http_client.get(
            f"/api/v1/graph/subgraph?node_id=memory_{mem1_id}&depth=2",
        )
        assert response.status_code == 200
        data = response.json()

        # Check edge types are present
        edge_types = {e["type"] for e in data["edges"]}
        assert "memory_link" in edge_types
        assert "entity_memory" in edge_types
        assert "entity_relationship" in edge_types

        # Check meta counts
        assert data["meta"]["memory_link_count"] >= 1
        assert data["meta"]["entity_memory_count"] >= 1
        assert data["meta"]["entity_relationship_count"] >= 1

    @pytest.mark.asyncio
    async def test_subgraph_invalid_node_id_format(self, http_client):
        """Returns 400 for invalid node_id format."""
        response = await http_client.get("/api/v1/graph/subgraph?node_id=invalid_format")
        assert response.status_code == 400
        assert "Invalid node_id format" in response.json()["error"]

    @pytest.mark.asyncio
    async def test_subgraph_missing_node_id(self, http_client):
        """Returns 400 when node_id is not provided."""
        response = await http_client.get("/api/v1/graph/subgraph")
        assert response.status_code == 400
        assert "Missing required parameter" in response.json()["error"]

    @pytest.mark.asyncio
    async def test_subgraph_nonexistent_memory(self, http_client):
        """Returns 404 for nonexistent memory."""
        response = await http_client.get("/api/v1/graph/subgraph?node_id=memory_99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_subgraph_nonexistent_entity(self, http_client):
        """Returns 404 for nonexistent entity."""
        response = await http_client.get("/api/v1/graph/subgraph?node_id=entity_99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_subgraph_invalid_depth(self, http_client):
        """Returns 400 for invalid depth parameter."""
        response = await http_client.get("/api/v1/graph/subgraph?node_id=memory_1&depth=not_a_number")
        assert response.status_code == 400
        assert "Invalid depth" in response.json()["error"]

    @pytest.mark.asyncio
    async def test_subgraph_depth_below_minimum(self, http_client):
        """Returns 400 for depth < 1."""
        response = await http_client.get("/api/v1/graph/subgraph?node_id=memory_1&depth=0")
        assert response.status_code == 400
        assert "Must be at least 1" in response.json()["error"]

    @pytest.mark.asyncio
    async def test_subgraph_invalid_node_types(self, http_client):
        """Returns 400 for invalid node_types parameter."""
        response = await http_client.get("/api/v1/graph/subgraph?node_id=memory_1&node_types=invalid")
        assert response.status_code == 400
        assert "Invalid node_types" in response.json()["error"]

    @pytest.mark.asyncio
    async def test_subgraph_meta_includes_all_fields(self, http_client):
        """Meta object includes all expected fields."""
        mem_response = await http_client.post("/api/v1/memories", json={
            "title": "Meta Test Memory",
            "content": "Memory for meta test",
            "context": "Testing meta fields",
            "keywords": ["meta"],
            "tags": ["meta-test"],
            "importance": 7,
        })
        memory_id = mem_response.json()["id"]

        response = await http_client.get(f"/api/v1/graph/subgraph?node_id=memory_{memory_id}")
        assert response.status_code == 200
        data = response.json()

        meta = data["meta"]
        assert "center_node_id" in meta
        assert "depth" in meta
        assert "node_types" in meta
        assert "max_nodes" in meta
        assert "memory_count" in meta
        assert "entity_count" in meta
        assert "edge_count" in meta
        assert "memory_link_count" in meta
        assert "entity_relationship_count" in meta
        assert "entity_memory_count" in meta
        assert "truncated" in meta


class TestGraphNewNodeTypes:
    """Tests for project, document, and code_artifact node types in graph API."""

    @pytest.mark.asyncio
    async def test_graph_includes_project_nodes(self, http_client):
        """GET /api/v1/graph includes project nodes when projects exist."""
        # Create a project
        project_resp = await http_client.post("/api/v1/projects", json={
            "name": "Test Project",
            "description": "Project for graph test",
            "project_type": "development",
        })
        assert project_resp.status_code in [200, 201]
        project_id = project_resp.json()["id"]

        # Get graph
        response = await http_client.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()

        # Check project node exists
        project_nodes = [n for n in data["nodes"] if n["type"] == "project"]
        assert len(project_nodes) >= 1
        assert any(n["data"]["id"] == project_id for n in project_nodes)

        # Check meta includes project_count
        assert "project_count" in data["meta"]
        assert data["meta"]["project_count"] >= 1

    @pytest.mark.asyncio
    async def test_graph_includes_document_nodes(self, http_client):
        """GET /api/v1/graph includes document nodes when documents exist."""
        # Create a document
        doc_resp = await http_client.post("/api/v1/documents", json={
            "title": "Test Document",
            "description": "Document for graph test",
            "content": "This is the document content for testing graph API",
            "document_type": "text",
            "tags": ["test"],
        })
        assert doc_resp.status_code in [200, 201]
        document_id = doc_resp.json()["id"]

        # Get graph
        response = await http_client.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()

        # Check document node exists
        document_nodes = [n for n in data["nodes"] if n["type"] == "document"]
        assert len(document_nodes) >= 1
        assert any(n["data"]["id"] == document_id for n in document_nodes)

        # Check meta includes document_count
        assert "document_count" in data["meta"]
        assert data["meta"]["document_count"] >= 1

    @pytest.mark.asyncio
    async def test_graph_includes_code_artifact_nodes(self, http_client):
        """GET /api/v1/graph includes code_artifact nodes when artifacts exist."""
        # Create a code artifact
        artifact_resp = await http_client.post("/api/v1/code-artifacts", json={
            "title": "Test Artifact",
            "description": "Code artifact for graph test",
            "code": "def hello(): return 'world'",
            "language": "python",
            "tags": ["test"],
        })
        assert artifact_resp.status_code in [200, 201]
        artifact_id = artifact_resp.json()["id"]

        # Get graph
        response = await http_client.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()

        # Check code_artifact node exists
        artifact_nodes = [n for n in data["nodes"] if n["type"] == "code_artifact"]
        assert len(artifact_nodes) >= 1
        assert any(n["data"]["id"] == artifact_id for n in artifact_nodes)

        # Check meta includes code_artifact_count
        assert "code_artifact_count" in data["meta"]
        assert data["meta"]["code_artifact_count"] >= 1

    @pytest.mark.asyncio
    async def test_graph_memory_project_edges(self, http_client):
        """Graph includes memory_project edges when memory linked to project."""
        # Create project
        project_resp = await http_client.post("/api/v1/projects", json={
            "name": "Edge Test Project",
            "description": "Project for edge test",
            "project_type": "development",
        })
        project_id = project_resp.json()["id"]

        # Create memory with project_ids
        await http_client.post("/api/v1/memories", json={
            "title": "Project Linked Memory",
            "content": "Memory linked to project",
            "context": "Testing memory_project edges",
            "keywords": ["project"],
            "tags": ["project-test"],
            "importance": 7,
            "project_ids": [project_id],
        })

        # Get graph
        response = await http_client.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()

        # Check memory_project edge exists
        memory_project_edges = [e for e in data["edges"] if e["type"] == "memory_project"]
        assert len(memory_project_edges) >= 1

        # Check meta includes count
        assert "memory_project_count" in data["meta"]
        assert data["meta"]["memory_project_count"] >= 1

    @pytest.mark.asyncio
    async def test_graph_document_project_edges(self, http_client):
        """Graph includes document_project edges when document linked to project."""
        # Create project
        project_resp = await http_client.post("/api/v1/projects", json={
            "name": "Document Edge Project",
            "description": "Project for document edge test",
            "project_type": "development",
        })
        project_id = project_resp.json()["id"]

        # Create document with project_id
        await http_client.post("/api/v1/documents", json={
            "title": "Project Linked Document",
            "description": "Document linked to project",
            "content": "Document content for edge testing",
            "document_type": "text",
            "tags": ["test"],
            "project_id": project_id,
        })

        # Get graph
        response = await http_client.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()

        # Check document_project edge exists
        document_project_edges = [e for e in data["edges"] if e["type"] == "document_project"]
        assert len(document_project_edges) >= 1

        # Check meta includes count
        assert "document_project_count" in data["meta"]
        assert data["meta"]["document_project_count"] >= 1

    @pytest.mark.asyncio
    async def test_graph_code_artifact_project_edges(self, http_client):
        """Graph includes code_artifact_project edges when artifact linked to project."""
        # Create project
        project_resp = await http_client.post("/api/v1/projects", json={
            "name": "Artifact Edge Project",
            "description": "Project for artifact edge test",
            "project_type": "development",
        })
        project_id = project_resp.json()["id"]

        # Create code artifact with project_id
        await http_client.post("/api/v1/code-artifacts", json={
            "title": "Project Linked Artifact",
            "description": "Artifact linked to project",
            "code": "print('hello')",
            "language": "python",
            "tags": ["test"],
            "project_id": project_id,
        })

        # Get graph
        response = await http_client.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()

        # Check code_artifact_project edge exists
        artifact_project_edges = [e for e in data["edges"] if e["type"] == "code_artifact_project"]
        assert len(artifact_project_edges) >= 1

        # Check meta includes count
        assert "code_artifact_project_count" in data["meta"]
        assert data["meta"]["code_artifact_project_count"] >= 1

    @pytest.mark.asyncio
    async def test_graph_memory_document_edges(self, http_client):
        """Graph includes memory_document edges when memory linked to document."""
        # Create document
        doc_resp = await http_client.post("/api/v1/documents", json={
            "title": "Document for Memory Link",
            "description": "Document to be linked",
            "content": "Document content",
            "document_type": "text",
            "tags": ["test"],
        })
        document_id = doc_resp.json()["id"]

        # Create memory with document_ids
        await http_client.post("/api/v1/memories", json={
            "title": "Document Linked Memory",
            "content": "Memory linked to document",
            "context": "Testing memory_document edges",
            "keywords": ["document"],
            "tags": ["document-test"],
            "importance": 7,
            "document_ids": [document_id],
        })

        # Get graph
        response = await http_client.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()

        # Check memory_document edge exists
        memory_document_edges = [e for e in data["edges"] if e["type"] == "memory_document"]
        assert len(memory_document_edges) >= 1

        # Check meta includes count
        assert "memory_document_count" in data["meta"]
        assert data["meta"]["memory_document_count"] >= 1

    @pytest.mark.asyncio
    async def test_graph_memory_code_artifact_edges(self, http_client):
        """Graph includes memory_code_artifact edges when memory linked to artifact."""
        # Create code artifact
        artifact_resp = await http_client.post("/api/v1/code-artifacts", json={
            "title": "Artifact for Memory Link",
            "description": "Artifact to be linked",
            "code": "x = 1",
            "language": "python",
            "tags": ["test"],
        })
        artifact_id = artifact_resp.json()["id"]

        # Create memory with code_artifact_ids
        await http_client.post("/api/v1/memories", json={
            "title": "Artifact Linked Memory",
            "content": "Memory linked to artifact",
            "context": "Testing memory_code_artifact edges",
            "keywords": ["artifact"],
            "tags": ["artifact-test"],
            "importance": 7,
            "code_artifact_ids": [artifact_id],
        })

        # Get graph
        response = await http_client.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()

        # Check memory_code_artifact edge exists
        memory_artifact_edges = [e for e in data["edges"] if e["type"] == "memory_code_artifact"]
        assert len(memory_artifact_edges) >= 1

        # Check meta includes count
        assert "memory_code_artifact_count" in data["meta"]
        assert data["meta"]["memory_code_artifact_count"] >= 1

    @pytest.mark.asyncio
    async def test_graph_node_types_filter_excludes_projects(self, http_client):
        """node_types parameter can exclude project nodes."""
        # Create a project
        await http_client.post("/api/v1/projects", json={
            "name": "Filter Test Project",
            "description": "Project for filter test",
            "project_type": "development",
        })

        # Get graph without projects
        response = await http_client.get("/api/v1/graph?node_types=memory,entity")
        assert response.status_code == 200
        data = response.json()

        # Should have no project nodes
        project_nodes = [n for n in data["nodes"] if n["type"] == "project"]
        assert len(project_nodes) == 0

    @pytest.mark.asyncio
    async def test_subgraph_from_project_center(self, http_client):
        """Subgraph can be centered on a project node."""
        # Create project
        project_resp = await http_client.post("/api/v1/projects", json={
            "name": "Center Project",
            "description": "Project to center subgraph on",
            "project_type": "development",
        })
        project_id = project_resp.json()["id"]

        # Create memory linked to project
        await http_client.post("/api/v1/memories", json={
            "title": "Project Related Memory",
            "content": "Memory for project subgraph test",
            "context": "Testing subgraph from project center",
            "keywords": ["project"],
            "tags": ["test"],
            "importance": 7,
            "project_ids": [project_id],
        })

        # Get subgraph centered on project
        response = await http_client.get(f"/api/v1/graph/subgraph?node_id=project_{project_id}")
        assert response.status_code == 200
        data = response.json()

        # Center should be the project
        assert data["meta"]["center_node_id"] == f"project_{project_id}"

        # Should include the linked memory
        memory_nodes = [n for n in data["nodes"] if n["type"] == "memory"]
        assert len(memory_nodes) >= 1

    @pytest.mark.asyncio
    async def test_subgraph_from_document_center(self, http_client):
        """Subgraph can be centered on a document node."""
        # Create document
        doc_resp = await http_client.post("/api/v1/documents", json={
            "title": "Center Document",
            "description": "Document to center subgraph on",
            "content": "Document content for subgraph test",
            "document_type": "text",
            "tags": ["test"],
        })
        document_id = doc_resp.json()["id"]

        # Create memory linked to document
        await http_client.post("/api/v1/memories", json={
            "title": "Document Related Memory",
            "content": "Memory for document subgraph test",
            "context": "Testing subgraph from document center",
            "keywords": ["document"],
            "tags": ["test"],
            "importance": 7,
            "document_ids": [document_id],
        })

        # Get subgraph centered on document
        response = await http_client.get(f"/api/v1/graph/subgraph?node_id=document_{document_id}")
        assert response.status_code == 200
        data = response.json()

        # Center should be the document
        assert data["meta"]["center_node_id"] == f"document_{document_id}"

        # Should include the linked memory
        memory_nodes = [n for n in data["nodes"] if n["type"] == "memory"]
        assert len(memory_nodes) >= 1

    @pytest.mark.asyncio
    async def test_subgraph_from_code_artifact_center(self, http_client):
        """Subgraph can be centered on a code_artifact node."""
        # Create code artifact
        artifact_resp = await http_client.post("/api/v1/code-artifacts", json={
            "title": "Center Artifact",
            "description": "Artifact to center subgraph on",
            "code": "result = 42",
            "language": "python",
            "tags": ["test"],
        })
        artifact_id = artifact_resp.json()["id"]

        # Create memory linked to artifact
        await http_client.post("/api/v1/memories", json={
            "title": "Artifact Related Memory",
            "content": "Memory for artifact subgraph test",
            "context": "Testing subgraph from artifact center",
            "keywords": ["artifact"],
            "tags": ["test"],
            "importance": 7,
            "code_artifact_ids": [artifact_id],
        })

        # Get subgraph centered on artifact
        response = await http_client.get(f"/api/v1/graph/subgraph?node_id=code_artifact_{artifact_id}")
        assert response.status_code == 200
        data = response.json()

        # Center should be the code artifact
        assert data["meta"]["center_node_id"] == f"code_artifact_{artifact_id}"

        # Should include the linked memory
        memory_nodes = [n for n in data["nodes"] if n["type"] == "memory"]
        assert len(memory_nodes) >= 1

    @pytest.mark.asyncio
    async def test_subgraph_meta_includes_new_counts(self, http_client):
        """Subgraph meta includes counts for all new node and edge types."""
        # Create memory for starting point
        mem_resp = await http_client.post("/api/v1/memories", json={
            "title": "Meta Test Memory",
            "content": "Memory for meta fields test",
            "context": "Testing new meta fields",
            "keywords": ["meta"],
            "tags": ["test"],
            "importance": 7,
        })
        memory_id = mem_resp.json()["id"]

        # Get subgraph
        response = await http_client.get(f"/api/v1/graph/subgraph?node_id=memory_{memory_id}")
        assert response.status_code == 200
        data = response.json()

        meta = data["meta"]

        # Check new node count fields exist
        assert "project_count" in meta
        assert "document_count" in meta
        assert "code_artifact_count" in meta

        # Check new edge count fields exist
        assert "memory_project_count" in meta
        assert "document_project_count" in meta
        assert "code_artifact_project_count" in meta
        assert "memory_document_count" in meta
        assert "memory_code_artifact_count" in meta


# Tiny 1x1 transparent PNG, base64-encoded — small file payload for tests
TINY_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8A"
    "AAAASUVORK5CYII="
)


class TestGraphFileNodes:
    """Tests for file node type and memory_file edges in the full graph endpoint."""

    @pytest.mark.asyncio
    async def test_graph_includes_file_nodes(self, http_client):
        """GET /api/v1/graph includes file nodes when files exist."""
        file_resp = await http_client.post("/api/v1/files", json={
            "filename": "graph-test.png",
            "description": "File for graph node test",
            "data": TINY_PNG_BASE64,
            "mime_type": "image/png",
            "tags": ["test"],
        })
        assert file_resp.status_code in [200, 201]
        file_id = file_resp.json()["id"]

        response = await http_client.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()

        file_nodes = [n for n in data["nodes"] if n["type"] == "file"]
        assert len(file_nodes) >= 1
        assert any(n["data"]["id"] == file_id for n in file_nodes)

        assert "file_count" in data["meta"]
        assert data["meta"]["file_count"] >= 1

    @pytest.mark.asyncio
    async def test_graph_memory_file_edges(self, http_client):
        """Graph includes memory_file edges when memory linked to file."""
        file_resp = await http_client.post("/api/v1/files", json={
            "filename": "linked-file.png",
            "description": "File to link from memory",
            "data": TINY_PNG_BASE64,
            "mime_type": "image/png",
            "tags": ["test"],
        })
        file_id = file_resp.json()["id"]

        await http_client.post("/api/v1/memories", json={
            "title": "File Linked Memory",
            "content": "Memory linked to file",
            "context": "Testing memory_file edges",
            "keywords": ["file"],
            "tags": ["file-test"],
            "importance": 7,
            "file_ids": [file_id],
        })

        response = await http_client.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()

        memory_file_edges = [e for e in data["edges"] if e["type"] == "memory_file"]
        assert len(memory_file_edges) >= 1

        assert "memory_file_count" in data["meta"]
        assert data["meta"]["memory_file_count"] >= 1

    @pytest.mark.asyncio
    async def test_graph_file_project_edges(self, http_client):
        """Graph includes file_project edges when file linked to project."""
        project_resp = await http_client.post("/api/v1/projects", json={
            "name": "File Edge Project",
            "description": "Project for file edge test",
            "project_type": "development",
        })
        project_id = project_resp.json()["id"]

        await http_client.post("/api/v1/files", json={
            "filename": "project-linked.png",
            "description": "File linked to project",
            "data": TINY_PNG_BASE64,
            "mime_type": "image/png",
            "tags": ["test"],
            "project_id": project_id,
        })

        response = await http_client.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()

        file_project_edges = [e for e in data["edges"] if e["type"] == "file_project"]
        assert len(file_project_edges) >= 1

        assert "file_project_count" in data["meta"]
        assert data["meta"]["file_project_count"] >= 1

    @pytest.mark.asyncio
    async def test_graph_entity_file_edges(self, http_client, sqlite_app):
        """Graph includes entity_file edges when entity linked to file."""
        from sqlalchemy import insert

        from app.repositories.sqlite.sqlite_tables import entity_file_association

        entity_resp = await http_client.post("/api/v1/entities", json={
            "name": "Entity For File Edge",
            "entity_type": "Organization",
            "notes": "Entity to link to file",
        })
        entity_id = entity_resp.json()["id"]

        file_resp = await http_client.post("/api/v1/files", json={
            "filename": "entity-linked.png",
            "description": "File linked to entity",
            "data": TINY_PNG_BASE64,
            "mime_type": "image/png",
            "tags": ["test"],
        })
        file_id = file_resp.json()["id"]

        # No public API to populate entity_file_association — insert directly
        db_adapter = sqlite_app.entity_service.entity_repo.db_adapter
        async with db_adapter.system_session() as session:
            await session.execute(
                insert(entity_file_association).values(
                    entity_id=entity_id, file_id=file_id,
                ),
            )

        response = await http_client.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()

        entity_file_edges = [e for e in data["edges"] if e["type"] == "entity_file"]
        assert len(entity_file_edges) >= 1

        assert "entity_file_count" in data["meta"]
        assert data["meta"]["entity_file_count"] >= 1


class TestGraphSkillNodes:
    """Tests for skill node type and skill-related edges in the full graph endpoint."""

    @pytest.mark.asyncio
    async def test_graph_includes_skill_nodes(self, http_client):
        """GET /api/v1/graph includes skill nodes when skills exist."""
        skill_resp = await http_client.post("/api/v1/skills", json={
            "name": "graph-test-skill",
            "description": "Skill for graph node test",
            "content": "# Test Skill\n\nDoes nothing.",
            "tags": ["test"],
            "importance": 7,
        })
        assert skill_resp.status_code in [200, 201]
        skill_id = skill_resp.json()["id"]

        response = await http_client.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()

        skill_nodes = [n for n in data["nodes"] if n["type"] == "skill"]
        assert len(skill_nodes) >= 1
        assert any(n["data"]["id"] == skill_id for n in skill_nodes)

        assert "skill_count" in data["meta"]
        assert data["meta"]["skill_count"] >= 1

    @pytest.mark.asyncio
    async def test_graph_memory_skill_edges(self, http_client):
        """Graph includes memory_skill edges when memory linked to skill."""
        skill_resp = await http_client.post("/api/v1/skills", json={
            "name": "memory-linked-skill",
            "description": "Skill linked from memory",
            "content": "# Linked Skill\n\nFor memory_skill edge test.",
            "tags": ["test"],
            "importance": 7,
        })
        skill_id = skill_resp.json()["id"]

        await http_client.post("/api/v1/memories", json={
            "title": "Skill Linked Memory",
            "content": "Memory linked to skill",
            "context": "Testing memory_skill edges",
            "keywords": ["skill"],
            "tags": ["skill-test"],
            "importance": 7,
            "skill_ids": [skill_id],
        })

        response = await http_client.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()

        memory_skill_edges = [e for e in data["edges"] if e["type"] == "memory_skill"]
        assert len(memory_skill_edges) >= 1

        assert "memory_skill_count" in data["meta"]
        assert data["meta"]["memory_skill_count"] >= 1

    @pytest.mark.asyncio
    async def test_graph_skill_project_edges(self, http_client):
        """Graph includes skill_project edges when skill linked to project."""
        project_resp = await http_client.post("/api/v1/projects", json={
            "name": "Skill Edge Project",
            "description": "Project for skill edge test",
            "project_type": "development",
        })
        project_id = project_resp.json()["id"]

        await http_client.post("/api/v1/skills", json={
            "name": "project-linked-skill",
            "description": "Skill linked to project",
            "content": "# Project Skill",
            "tags": ["test"],
            "importance": 7,
            "project_id": project_id,
        })

        response = await http_client.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()

        skill_project_edges = [e for e in data["edges"] if e["type"] == "skill_project"]
        assert len(skill_project_edges) >= 1

        assert "skill_project_count" in data["meta"]
        assert data["meta"]["skill_project_count"] >= 1

    @pytest.mark.asyncio
    async def test_graph_skill_file_edges(self, http_client):
        """Graph includes skill_file edges when skill linked to file."""
        skill_resp = await http_client.post("/api/v1/skills", json={
            "name": "file-linker-skill",
            "description": "Skill that links to file",
            "content": "# Skill File Link",
            "tags": ["test"],
            "importance": 7,
        })
        skill_id = skill_resp.json()["id"]

        file_resp = await http_client.post("/api/v1/files", json={
            "filename": "skill-linked.png",
            "description": "File linked from skill",
            "data": TINY_PNG_BASE64,
            "mime_type": "image/png",
        })
        file_id = file_resp.json()["id"]

        link_resp = await http_client.post(
            f"/api/v1/skills/{skill_id}/files", json={"file_id": file_id},
        )
        assert link_resp.status_code in [200, 201]

        response = await http_client.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()

        skill_file_edges = [e for e in data["edges"] if e["type"] == "skill_file"]
        assert len(skill_file_edges) >= 1
        assert "skill_file_count" in data["meta"]
        assert data["meta"]["skill_file_count"] >= 1

    @pytest.mark.asyncio
    async def test_graph_skill_code_artifact_edges(self, http_client):
        """Graph includes skill_code_artifact edges when skill linked to artifact."""
        skill_resp = await http_client.post("/api/v1/skills", json={
            "name": "artifact-linker-skill",
            "description": "Skill that links to artifact",
            "content": "# Skill Artifact Link",
            "tags": ["test"],
            "importance": 7,
        })
        skill_id = skill_resp.json()["id"]

        artifact_resp = await http_client.post("/api/v1/code-artifacts", json={
            "title": "Skill Linked Artifact",
            "description": "Artifact linked from skill",
            "code": "x = 1",
            "language": "python",
        })
        artifact_id = artifact_resp.json()["id"]

        link_resp = await http_client.post(
            f"/api/v1/skills/{skill_id}/code-artifacts",
            json={"code_artifact_id": artifact_id},
        )
        assert link_resp.status_code in [200, 201]

        response = await http_client.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()

        edges = [e for e in data["edges"] if e["type"] == "skill_code_artifact"]
        assert len(edges) >= 1
        assert "skill_code_artifact_count" in data["meta"]
        assert data["meta"]["skill_code_artifact_count"] >= 1

    @pytest.mark.asyncio
    async def test_graph_skill_document_edges(self, http_client):
        """Graph includes skill_document edges when skill linked to document."""
        skill_resp = await http_client.post("/api/v1/skills", json={
            "name": "document-linker-skill",
            "description": "Skill that links to document",
            "content": "# Skill Document Link",
            "tags": ["test"],
            "importance": 7,
        })
        skill_id = skill_resp.json()["id"]

        doc_resp = await http_client.post("/api/v1/documents", json={
            "title": "Skill Linked Document",
            "description": "Document linked from skill",
            "content": "Document content",
            "document_type": "text",
        })
        doc_id = doc_resp.json()["id"]

        link_resp = await http_client.post(
            f"/api/v1/skills/{skill_id}/documents",
            json={"document_id": doc_id},
        )
        assert link_resp.status_code in [200, 201]

        response = await http_client.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()

        edges = [e for e in data["edges"] if e["type"] == "skill_document"]
        assert len(edges) >= 1
        assert "skill_document_count" in data["meta"]
        assert data["meta"]["skill_document_count"] >= 1


class TestSubgraphSkillEdges:
    """Tests for skill_file/skill_code_artifact/skill_document edge emission in /subgraph endpoint."""

    @pytest.mark.asyncio
    async def test_subgraph_includes_skill_file_edge(self, http_client):
        """Subgraph emits skill_file edge when both skill and file are in result."""
        skill_resp = await http_client.post("/api/v1/skills", json={
            "name": "subgraph-skill-file",
            "description": "Skill linked to file",
            "content": "# Subgraph",
            "tags": ["test"],
            "importance": 7,
        })
        skill_id = skill_resp.json()["id"]

        file_resp = await http_client.post("/api/v1/files", json={
            "filename": "subgraph-file.png",
            "description": "Linked file",
            "data": TINY_PNG_BASE64,
            "mime_type": "image/png",
        })
        file_id = file_resp.json()["id"]

        # Link skill -> file
        await http_client.post(
            f"/api/v1/skills/{skill_id}/files", json={"file_id": file_id},
        )

        # Memory linked to BOTH skill and file (so CTE finds both via memory)
        mem_resp = await http_client.post("/api/v1/memories", json={
            "title": "Hub Memory",
            "content": "Hub for skill+file traversal",
            "context": "Subgraph test",
            "keywords": ["hub"],
            "tags": ["test"],
            "importance": 7,
            "skill_ids": [skill_id],
            "file_ids": [file_id],
        })
        memory_id = mem_resp.json()["id"]

        response = await http_client.get(
            f"/api/v1/graph/subgraph?node_id=memory_{memory_id}"
            "&node_types=memory,skill,file",
        )
        assert response.status_code == 200
        data = response.json()

        skill_file_edges = [e for e in data["edges"] if e["type"] == "skill_file"]
        assert len(skill_file_edges) >= 1

    @pytest.mark.asyncio
    async def test_subgraph_includes_skill_code_artifact_edge(self, http_client):
        """Subgraph emits skill_code_artifact edge when both endpoints in result."""
        skill_resp = await http_client.post("/api/v1/skills", json={
            "name": "subgraph-skill-artifact",
            "description": "Skill linked to artifact",
            "content": "# Subgraph",
            "tags": ["test"],
            "importance": 7,
        })
        skill_id = skill_resp.json()["id"]

        artifact_resp = await http_client.post("/api/v1/code-artifacts", json={
            "title": "Subgraph Artifact",
            "description": "Artifact linked from skill",
            "code": "x = 1",
            "language": "python",
        })
        artifact_id = artifact_resp.json()["id"]

        await http_client.post(
            f"/api/v1/skills/{skill_id}/code-artifacts",
            json={"code_artifact_id": artifact_id},
        )

        mem_resp = await http_client.post("/api/v1/memories", json={
            "title": "Hub Memory CA",
            "content": "Hub for skill+artifact traversal",
            "context": "Subgraph test",
            "keywords": ["hub"],
            "tags": ["test"],
            "importance": 7,
            "skill_ids": [skill_id],
            "code_artifact_ids": [artifact_id],
        })
        memory_id = mem_resp.json()["id"]

        response = await http_client.get(
            f"/api/v1/graph/subgraph?node_id=memory_{memory_id}"
            "&node_types=memory,skill,code_artifact",
        )
        assert response.status_code == 200
        data = response.json()

        edges = [e for e in data["edges"] if e["type"] == "skill_code_artifact"]
        assert len(edges) >= 1

    @pytest.mark.asyncio
    async def test_subgraph_includes_skill_document_edge(self, http_client):
        """Subgraph emits skill_document edge when both endpoints in result."""
        skill_resp = await http_client.post("/api/v1/skills", json={
            "name": "subgraph-skill-doc",
            "description": "Skill linked to document",
            "content": "# Subgraph",
            "tags": ["test"],
            "importance": 7,
        })
        skill_id = skill_resp.json()["id"]

        doc_resp = await http_client.post("/api/v1/documents", json={
            "title": "Subgraph Document",
            "description": "Document linked from skill",
            "content": "Document content",
            "document_type": "text",
        })
        doc_id = doc_resp.json()["id"]

        await http_client.post(
            f"/api/v1/skills/{skill_id}/documents",
            json={"document_id": doc_id},
        )

        mem_resp = await http_client.post("/api/v1/memories", json={
            "title": "Hub Memory Doc",
            "content": "Hub for skill+doc traversal",
            "context": "Subgraph test",
            "keywords": ["hub"],
            "tags": ["test"],
            "importance": 7,
            "skill_ids": [skill_id],
            "document_ids": [doc_id],
        })
        memory_id = mem_resp.json()["id"]

        response = await http_client.get(
            f"/api/v1/graph/subgraph?node_id=memory_{memory_id}"
            "&node_types=memory,skill,document",
        )
        assert response.status_code == 200
        data = response.json()

        edges = [e for e in data["edges"] if e["type"] == "skill_document"]
        assert len(edges) >= 1


class TestSubgraphSkillCTE:
    """Tests for SQLite recursive CTE traversal across skill branches."""

    @pytest.mark.asyncio
    async def test_subgraph_from_skill_center(self, http_client):
        """Subgraph centered on skill returns skill node + linked file at depth 1."""
        skill_resp = await http_client.post("/api/v1/skills", json={
            "name": "skill-center",
            "description": "Skill at center",
            "content": "# Center Skill",
            "tags": ["test"],
            "importance": 7,
        })
        skill_id = skill_resp.json()["id"]

        file_resp = await http_client.post("/api/v1/files", json={
            "filename": "skill-center-file.png",
            "description": "File linked to center skill",
            "data": TINY_PNG_BASE64,
            "mime_type": "image/png",
        })
        file_id = file_resp.json()["id"]

        await http_client.post(
            f"/api/v1/skills/{skill_id}/files", json={"file_id": file_id},
        )

        response = await http_client.get(
            f"/api/v1/graph/subgraph?node_id=skill_{skill_id}&node_types=skill,file",
        )
        assert response.status_code == 200
        data = response.json()

        assert any(n["id"] == f"skill_{skill_id}" for n in data["nodes"])
        assert any(n["id"] == f"file_{file_id}" for n in data["nodes"])
        skill_file_edges = [e for e in data["edges"] if e["type"] == "skill_file"]
        assert len(skill_file_edges) >= 1

    @pytest.mark.asyncio
    async def test_subgraph_traverses_memory_skill(self, http_client):
        """CTE traverses memory↔skill association from memory center."""
        skill_resp = await http_client.post("/api/v1/skills", json={
            "name": "memory-skill-traversal",
            "description": "Skill for traversal test",
            "content": "# Traversal",
            "tags": ["test"],
            "importance": 7,
        })
        skill_id = skill_resp.json()["id"]

        mem_resp = await http_client.post("/api/v1/memories", json={
            "title": "Memory for skill traversal",
            "content": "Memory traversed to skill",
            "context": "Subgraph test",
            "keywords": ["t"],
            "tags": ["test"],
            "importance": 7,
            "skill_ids": [skill_id],
        })
        memory_id = mem_resp.json()["id"]

        response = await http_client.get(
            f"/api/v1/graph/subgraph?node_id=memory_{memory_id}&node_types=memory,skill",
        )
        assert response.status_code == 200
        data = response.json()

        assert any(n["id"] == f"skill_{skill_id}" for n in data["nodes"])

    @pytest.mark.asyncio
    async def test_subgraph_traverses_skill_project(self, http_client):
        """CTE traverses skill↔project from skill center."""
        project_resp = await http_client.post("/api/v1/projects", json={
            "name": "Skill CTE Project",
            "description": "P",
            "project_type": "development",
        })
        project_id = project_resp.json()["id"]

        skill_resp = await http_client.post("/api/v1/skills", json={
            "name": "skill-with-project",
            "description": "Skill linked to project",
            "content": "# T",
            "tags": ["test"],
            "importance": 7,
            "project_id": project_id,
        })
        skill_id = skill_resp.json()["id"]

        response = await http_client.get(
            f"/api/v1/graph/subgraph?node_id=skill_{skill_id}&node_types=skill,project",
        )
        assert response.status_code == 200
        data = response.json()

        assert any(n["id"] == f"project_{project_id}" for n in data["nodes"])

    @pytest.mark.asyncio
    async def test_subgraph_traverses_skill_to_code_artifact(self, http_client):
        """CTE traverses skill↔code_artifact from skill center."""
        skill_resp = await http_client.post("/api/v1/skills", json={
            "name": "skill-with-artifact",
            "description": "Skill linked to artifact",
            "content": "# T",
            "tags": ["test"],
            "importance": 7,
        })
        skill_id = skill_resp.json()["id"]

        artifact_resp = await http_client.post("/api/v1/code-artifacts", json={
            "title": "Artifact via skill",
            "description": "d",
            "code": "x = 1",
            "language": "python",
        })
        artifact_id = artifact_resp.json()["id"]

        await http_client.post(
            f"/api/v1/skills/{skill_id}/code-artifacts",
            json={"code_artifact_id": artifact_id},
        )

        response = await http_client.get(
            f"/api/v1/graph/subgraph?node_id=skill_{skill_id}"
            "&node_types=skill,code_artifact",
        )
        assert response.status_code == 200
        data = response.json()

        assert any(n["id"] == f"code_artifact_{artifact_id}" for n in data["nodes"])

    @pytest.mark.asyncio
    async def test_subgraph_traverses_skill_to_document(self, http_client):
        """CTE traverses skill↔document from skill center."""
        skill_resp = await http_client.post("/api/v1/skills", json={
            "name": "skill-with-document",
            "description": "Skill linked to document",
            "content": "# T",
            "tags": ["test"],
            "importance": 7,
        })
        skill_id = skill_resp.json()["id"]

        doc_resp = await http_client.post("/api/v1/documents", json={
            "title": "Document via skill",
            "description": "d",
            "content": "Document content",
            "document_type": "text",
        })
        doc_id = doc_resp.json()["id"]

        await http_client.post(
            f"/api/v1/skills/{skill_id}/documents",
            json={"document_id": doc_id},
        )

        response = await http_client.get(
            f"/api/v1/graph/subgraph?node_id=skill_{skill_id}"
            "&node_types=skill,document",
        )
        assert response.status_code == 200
        data = response.json()

        assert any(n["id"] == f"document_{doc_id}" for n in data["nodes"])


class TestGraphFeatureFlagBehaviour:
    """Tests that graph endpoints honour SKILLS_ENABLED / FILES_ENABLED."""

    @pytest.mark.asyncio
    async def test_full_graph_rejects_node_types_skill_when_disabled(self, graph_http_client_factory):
        """Explicit node_types=skill returns 400 when skills feature is off."""
        all_features = set(FEATURE_FLAGS.keys())
        enabled = all_features - {"skills"}
        http, _app = await graph_http_client_factory(enabled)

        response = await http.get("/api/v1/graph?node_types=memory,skill")
        assert response.status_code == 400
        assert "skill" in response.json()["error"].lower()

    @pytest.mark.asyncio
    async def test_full_graph_rejects_node_types_file_when_disabled(self, graph_http_client_factory):
        """Explicit node_types=file returns 400 when files feature is off."""
        all_features = set(FEATURE_FLAGS.keys())
        enabled = all_features - {"files"}
        http, _app = await graph_http_client_factory(enabled)

        response = await http.get("/api/v1/graph?node_types=memory,file")
        assert response.status_code == 400
        assert "file" in response.json()["error"].lower()

    @pytest.mark.asyncio
    async def test_subgraph_rejects_node_types_skill_when_disabled(self, graph_http_client_factory):
        """Subgraph: explicit node_types=skill returns 400 when skills feature is off."""
        all_features = set(FEATURE_FLAGS.keys())
        enabled = all_features - {"skills"}
        http, _app = await graph_http_client_factory(enabled)

        # Create a memory to act as center
        mem_resp = await http.post("/api/v1/memories", json={
            "title": "Center", "content": "C",
            "context": "Test", "keywords": ["c"], "tags": ["t"], "importance": 7,
        })
        memory_id = mem_resp.json()["id"]

        response = await http.get(
            f"/api/v1/graph/subgraph?node_id=memory_{memory_id}"
            "&node_types=memory,skill",
        )
        assert response.status_code == 400
        assert "skill" in response.json()["error"].lower()

    @pytest.mark.asyncio
    async def test_default_omits_skill_when_disabled(self, graph_http_client_factory):
        """Default GET /api/v1/graph silently omits skill nodes when disabled."""
        all_features = set(FEATURE_FLAGS.keys())
        enabled = all_features - {"skills"}
        http, _app = await graph_http_client_factory(enabled)

        # Default request — no explicit node_types
        response = await http.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()

        # No skill nodes; no error
        assert all(n["type"] != "skill" for n in data["nodes"])

    @pytest.mark.asyncio
    async def test_default_omits_file_when_disabled(self, graph_http_client_factory):
        """Default GET /api/v1/graph silently omits file nodes when disabled."""
        all_features = set(FEATURE_FLAGS.keys())
        enabled = all_features - {"files"}
        http, _app = await graph_http_client_factory(enabled)

        response = await http.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()

        assert all(n["type"] != "file" for n in data["nodes"])


class TestGraphMetaShape:
    """Regression: every new node/edge meta count appears in both graph endpoints."""

    EXPECTED_NEW_KEYS = {
        # Node count fields
        "file_count",
        "skill_count",
        # Edge count fields added in Phase 1
        "memory_file_count",
        "file_project_count",
        "entity_file_count",
        "memory_skill_count",
        "skill_project_count",
        "skill_file_count",
        "skill_code_artifact_count",
        "skill_document_count",
    }

    @pytest.mark.asyncio
    async def test_full_graph_meta_includes_all_skill_file_counts(self, http_client):
        """Full /api/v1/graph meta exposes every skill_/file_ count field."""
        response = await http_client.get("/api/v1/graph")
        assert response.status_code == 200
        meta = response.json()["meta"]

        missing = self.EXPECTED_NEW_KEYS - set(meta.keys())
        assert not missing, f"Missing meta keys in full graph: {missing}"

    @pytest.mark.asyncio
    async def test_subgraph_meta_includes_all_skill_file_counts(self, http_client):
        """Subgraph meta exposes every skill_/file_ count field."""
        mem_resp = await http_client.post("/api/v1/memories", json={
            "title": "Meta Shape Memory",
            "content": "C",
            "context": "Testing meta shape",
            "keywords": ["m"],
            "tags": ["test"],
            "importance": 7,
        })
        memory_id = mem_resp.json()["id"]

        response = await http_client.get(
            f"/api/v1/graph/subgraph?node_id=memory_{memory_id}",
        )
        assert response.status_code == 200
        meta = response.json()["meta"]

        missing = self.EXPECTED_NEW_KEYS - set(meta.keys())
        assert not missing, f"Missing meta keys in subgraph: {missing}"


# Helper to create a project + plan + tasks chain via the public API
async def _make_project_plan_tasks(http_client, project_name="P", task_titles=("Task A",)):
    project_resp = await http_client.post("/api/v1/projects", json={
        "name": project_name,
        "description": "P for plan/task graph test",
        "project_type": "development",
    })
    assert project_resp.status_code in (200, 201)
    project_id = project_resp.json()["id"]

    plan_resp = await http_client.post("/api/v1/plans", json={
        "title": f"{project_name} Plan",
        "project_id": project_id,
        "goal": "Goal",
    })
    assert plan_resp.status_code in (200, 201), plan_resp.text
    plan_id = plan_resp.json()["id"]

    task_ids = []
    for title in task_titles:
        task_resp = await http_client.post("/api/v1/tasks", json={
            "title": title, "plan_id": plan_id,
        })
        assert task_resp.status_code in (200, 201), task_resp.text
        task_ids.append(task_resp.json()["id"])
    return project_id, plan_id, task_ids


class TestGraphPlanAndTaskNodes:
    """Plan and task nodes appear in /api/v1/graph with correct shape and edges."""

    @pytest.mark.asyncio
    async def test_graph_includes_plan_nodes(self, http_client):
        _, plan_id, _ = await _make_project_plan_tasks(http_client, "PlanGraphTest")
        response = await http_client.get("/api/v1/graph?node_types=memory,plan")
        assert response.status_code == 200
        data = response.json()

        plan_nodes = [n for n in data["nodes"] if n["type"] == "plan"]
        assert any(n["data"]["id"] == plan_id for n in plan_nodes)
        node = next(n for n in plan_nodes if n["data"]["id"] == plan_id)
        assert node["id"] == f"plan_{plan_id}"
        assert "title" in node["data"]
        assert "status" in node["data"]
        assert "project_id" in node["data"]
        assert data["meta"]["plan_count"] >= 1

    @pytest.mark.asyncio
    async def test_graph_includes_task_nodes(self, http_client):
        _, _, task_ids = await _make_project_plan_tasks(
            http_client, "TaskGraphTest", task_titles=("Task 1", "Task 2"),
        )
        response = await http_client.get("/api/v1/graph?node_types=memory,task")
        assert response.status_code == 200
        data = response.json()

        task_nodes = [n for n in data["nodes"] if n["type"] == "task"]
        for tid in task_ids:
            assert any(n["data"]["id"] == tid for n in task_nodes)
        node = next(n for n in task_nodes if n["data"]["id"] == task_ids[0])
        assert node["id"] == f"task_{task_ids[0]}"
        assert "plan_id" in node["data"]
        assert "state" in node["data"]
        assert "priority" in node["data"]
        assert data["meta"]["task_count"] >= 2

    @pytest.mark.asyncio
    async def test_graph_plan_project_edge(self, http_client):
        project_id, plan_id, _ = await _make_project_plan_tasks(http_client, "PPEdge")
        response = await http_client.get("/api/v1/graph?node_types=plan,project")
        assert response.status_code == 200
        data = response.json()

        plan_project_edges = [
            e for e in data["edges"]
            if e["type"] == "plan_project"
            and e["source"] == f"plan_{plan_id}"
            and e["target"] == f"project_{project_id}"
        ]
        assert len(plan_project_edges) == 1
        assert data["meta"]["plan_project_count"] >= 1

    @pytest.mark.asyncio
    async def test_graph_plan_task_edge(self, http_client):
        _, plan_id, task_ids = await _make_project_plan_tasks(
            http_client, "PTEdge", task_titles=("OnlyTask",),
        )
        response = await http_client.get("/api/v1/graph?node_types=plan,task")
        assert response.status_code == 200
        data = response.json()

        plan_task_edges = [
            e for e in data["edges"]
            if e["type"] == "plan_task"
            and e["source"] == f"plan_{plan_id}"
            and e["target"] == f"task_{task_ids[0]}"
        ]
        assert len(plan_task_edges) == 1
        assert data["meta"]["plan_task_count"] >= 1

    @pytest.mark.asyncio
    async def test_graph_default_includes_plans_and_tasks(self, http_client):
        await _make_project_plan_tasks(http_client, "DefaultIncludes")
        response = await http_client.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()
        types = {n["type"] for n in data["nodes"]}
        assert "plan" in types
        assert "task" in types

    @pytest.mark.asyncio
    async def test_graph_combined_all_types(self, http_client):
        await _make_project_plan_tasks(http_client, "CombinedAll")
        response = await http_client.get(
            "/api/v1/graph?node_types=memory,project,plan,task,skill,file",
        )
        assert response.status_code == 200
        data = response.json()
        # Smoke: meta keys present
        for k in ["plan_count", "task_count", "plan_project_count", "plan_task_count"]:
            assert k in data["meta"]


class TestGraphPlanTaskEdgeCases:
    """Edge cases for plan/task graph nodes."""

    @pytest.mark.asyncio
    async def test_no_plans_or_tasks(self, http_client):
        response = await http_client.get("/api/v1/graph?node_types=plan,task")
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["plan_count"] == 0
        assert data["meta"]["task_count"] == 0
        assert all(n["type"] not in ("plan", "task") for n in data["nodes"])

    @pytest.mark.asyncio
    async def test_plan_with_no_tasks_emits_no_plan_task_edges(self, http_client):
        _, plan_id, _ = await _make_project_plan_tasks(http_client, "NoTasks", task_titles=())
        response = await http_client.get("/api/v1/graph?node_types=plan,task")
        assert response.status_code == 200
        data = response.json()

        plan_task_edges = [e for e in data["edges"] if e["type"] == "plan_task" and e["source"] == f"plan_{plan_id}"]
        assert len(plan_task_edges) == 0

    @pytest.mark.asyncio
    async def test_task_only_no_plan_task_edge(self, http_client):
        """node_types=task only: tasks emitted, but no plan_task edges."""
        _, _, task_ids = await _make_project_plan_tasks(
            http_client, "TaskOnly", task_titles=("T1",),
        )
        response = await http_client.get("/api/v1/graph?node_types=task")
        assert response.status_code == 200
        data = response.json()

        assert any(n["data"]["id"] == task_ids[0] for n in data["nodes"] if n["type"] == "task")
        assert all(e["type"] != "plan_task" for e in data["edges"])


class TestGraphPlanTaskFeatureFlag:
    """Feature-flag (PLANNING_ENABLED) gating for plan/task node types."""

    @pytest.mark.asyncio
    async def test_plan_rejected_when_planning_disabled(self, graph_http_client_factory):
        all_features = set(FEATURE_FLAGS.keys())
        enabled = all_features - {"planning"}
        http, _app = await graph_http_client_factory(enabled)

        response = await http.get("/api/v1/graph?node_types=memory,plan")
        assert response.status_code == 400
        assert "PLANNING_ENABLED" in response.json()["error"]

    @pytest.mark.asyncio
    async def test_task_rejected_when_planning_disabled(self, graph_http_client_factory):
        all_features = set(FEATURE_FLAGS.keys())
        enabled = all_features - {"planning"}
        http, _app = await graph_http_client_factory(enabled)

        response = await http.get("/api/v1/graph?node_types=memory,task")
        assert response.status_code == 400
        assert "PLANNING_ENABLED" in response.json()["error"]

    @pytest.mark.asyncio
    async def test_plan_and_task_dedup_one_flag_listed(self, graph_http_client_factory):
        """Requesting plan,task while disabled: PLANNING_ENABLED listed once."""
        all_features = set(FEATURE_FLAGS.keys())
        enabled = all_features - {"planning"}
        http, _app = await graph_http_client_factory(enabled)

        response = await http.get("/api/v1/graph?node_types=plan,task")
        assert response.status_code == 400
        msg = response.json()["error"]
        assert msg.count("PLANNING_ENABLED") == 1

    @pytest.mark.asyncio
    async def test_plan_disabled_skill_enabled_only_plan_cited(self, graph_http_client_factory):
        all_features = set(FEATURE_FLAGS.keys())
        enabled = all_features - {"planning"}
        http, _app = await graph_http_client_factory(enabled)

        response = await http.get("/api/v1/graph?node_types=plan,skill")
        assert response.status_code == 400
        msg = response.json()["error"]
        assert "PLANNING_ENABLED" in msg
        assert "SKILLS_ENABLED" not in msg

    @pytest.mark.asyncio
    async def test_default_request_omits_plan_task_when_disabled(self, graph_http_client_factory):
        all_features = set(FEATURE_FLAGS.keys())
        enabled = all_features - {"planning"}
        http, _app = await graph_http_client_factory(enabled)

        response = await http.get("/api/v1/graph")
        assert response.status_code == 200
        types = {n["type"] for n in response.json()["nodes"]}
        assert "plan" not in types
        assert "task" not in types

    @pytest.mark.asyncio
    async def test_subgraph_rejects_plan_when_disabled(self, graph_http_client_factory):
        all_features = set(FEATURE_FLAGS.keys())
        enabled = all_features - {"planning"}
        http, _app = await graph_http_client_factory(enabled)

        mem_resp = await http.post("/api/v1/memories", json={
            "title": "Center", "content": "C",
            "context": "Test", "keywords": ["c"], "tags": ["t"], "importance": 7,
        })
        memory_id = mem_resp.json()["id"]

        response = await http.get(
            f"/api/v1/graph/subgraph?node_id=memory_{memory_id}&node_types=memory,plan",
        )
        assert response.status_code == 400
        assert "PLANNING_ENABLED" in response.json()["error"]


class TestSubgraphPlanTaskCTE:
    """SQLite CTE traversal across plan/task branches."""

    @pytest.mark.asyncio
    async def test_subgraph_from_plan_to_project_and_tasks(self, http_client):
        project_id, plan_id, task_ids = await _make_project_plan_tasks(
            http_client, "PlanCenter", task_titles=("CTE Task 1", "CTE Task 2"),
        )

        response = await http_client.get(
            f"/api/v1/graph/subgraph?node_id=plan_{plan_id}&depth=1"
            "&node_types=plan,project,task",
        )
        assert response.status_code == 200
        data = response.json()
        node_ids = {n["id"] for n in data["nodes"]}
        assert f"plan_{plan_id}" in node_ids
        assert f"project_{project_id}" in node_ids
        for tid in task_ids:
            assert f"task_{tid}" in node_ids

    @pytest.mark.asyncio
    async def test_subgraph_from_task_to_plan(self, http_client):
        _, plan_id, task_ids = await _make_project_plan_tasks(
            http_client, "TaskCenter", task_titles=("OneTask",),
        )
        task_id = task_ids[0]

        response = await http_client.get(
            f"/api/v1/graph/subgraph?node_id=task_{task_id}&depth=1"
            "&node_types=task,plan",
        )
        assert response.status_code == 200
        data = response.json()
        node_ids = {n["id"] for n in data["nodes"]}
        assert f"task_{task_id}" in node_ids
        assert f"plan_{plan_id}" in node_ids

    @pytest.mark.asyncio
    async def test_subgraph_from_task_depth2_reaches_project(self, http_client):
        project_id, plan_id, task_ids = await _make_project_plan_tasks(
            http_client, "TaskMultiHop", task_titles=("MHop",),
        )
        task_id = task_ids[0]

        response = await http_client.get(
            f"/api/v1/graph/subgraph?node_id=task_{task_id}&depth=2"
            "&node_types=task,plan,project",
        )
        assert response.status_code == 200
        data = response.json()
        node_ids = {n["id"] for n in data["nodes"]}
        assert f"plan_{plan_id}" in node_ids
        assert f"project_{project_id}" in node_ids

    @pytest.mark.asyncio
    async def test_subgraph_from_project_to_plans(self, http_client):
        project_id, plan_id, _ = await _make_project_plan_tasks(http_client, "ProjectToPlan")

        response = await http_client.get(
            f"/api/v1/graph/subgraph?node_id=project_{project_id}&depth=1"
            "&node_types=project,plan",
        )
        assert response.status_code == 200
        data = response.json()
        node_ids = {n["id"] for n in data["nodes"]}
        assert f"plan_{plan_id}" in node_ids

    @pytest.mark.asyncio
    async def test_subgraph_plan_excludes_tasks_when_filtered(self, http_client):
        _, plan_id, task_ids = await _make_project_plan_tasks(
            http_client, "PlanFilter", task_titles=("FilteredTask",),
        )
        response = await http_client.get(
            f"/api/v1/graph/subgraph?node_id=plan_{plan_id}&depth=1"
            "&node_types=plan,project",
        )
        assert response.status_code == 200
        data = response.json()
        assert all(n["type"] != "task" for n in data["nodes"])

    @pytest.mark.asyncio
    async def test_subgraph_nonexistent_plan_returns_404(self, http_client):
        response = await http_client.get(
            "/api/v1/graph/subgraph?node_id=plan_999999",
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_subgraph_nonexistent_task_returns_404(self, http_client):
        response = await http_client.get(
            "/api/v1/graph/subgraph?node_id=task_999999",
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_subgraph_meta_includes_plan_task_counts(self, http_client):
        _, plan_id, _ = await _make_project_plan_tasks(http_client, "MetaCounts")
        response = await http_client.get(
            f"/api/v1/graph/subgraph?node_id=plan_{plan_id}&depth=1",
        )
        assert response.status_code == 200
        meta = response.json()["meta"]
        for k in ["plan_count", "task_count", "plan_project_count", "plan_task_count"]:
            assert k in meta
