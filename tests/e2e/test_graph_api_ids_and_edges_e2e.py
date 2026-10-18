"""PostgreSQL E2E tests for graph node ids, memory links and cross-page links.

PostgreSQL stores ids in 32-bit INTEGER columns and asyncpg refuses to encode a
larger value instead of matching no row, so these checks differ from SQLite:
- node ids above the 32-bit range are rejected before reaching the database,
- link_memories skips target ids that cannot exist instead of failing half way,
- GET /api/v1/graph reports links to memories on other pages (the filter query
  runs on PostgreSQL), and still drops obsolete memories.
"""
import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")

SETTINGS_OVERRIDE = {"MEMORY_NUM_AUTO_LINK": 0}


async def _create_memory(http_client, title):
    response = await http_client.post("/api/v1/memories", json={
        "title": title,
        "content": f"Content of {title}",
        "context": "graph ids and edges on PostgreSQL",
        "keywords": ["graph"],
        "tags": ["graph"],
        "importance": 7,
    })
    assert response.status_code in (200, 201), response.text
    return response.json()["id"]


@pytest.mark.e2e
@pytest.mark.parametrize("node_type", ["memory", "entity", "project"])
async def test_subgraph_rejects_ids_beyond_the_integer_column(http_client, node_type):
    response = await http_client.get(
        "/api/v1/graph/subgraph", params={"node_id": f"{node_type}_3000000000"},
    )

    assert response.status_code == 400, response.text
    assert "out of range" in response.json()["error"]


@pytest.mark.e2e
async def test_link_memories_skips_ids_beyond_the_integer_column(http_client):
    ids = [await _create_memory(http_client, f"Memory {n}") for n in range(1, 5)]
    source, first, _unused, last = ids

    response = await http_client.post(
        f"/api/v1/memories/{source}/links",
        json={"related_ids": [last, 3_000_000_000, 2**70, first]},
    )

    assert response.status_code == 200, response.text
    assert response.json()["linked_ids"] == [last, first]
    stored = await http_client.get(f"/api/v1/memories/{source}")
    assert sorted(stored.json()["linked_memory_ids"]) == sorted([first, last])


@pytest.mark.e2e
async def test_graph_reports_links_between_pages(http_client):
    oldest, second, third, newest = [
        await _create_memory(http_client, f"Memory {n}") for n in range(1, 5)
    ]
    response = await http_client.post(
        f"/api/v1/memories/{oldest}/links", json={"related_ids": [newest, second]},
    )
    assert response.status_code == 200, response.text
    deleted = await http_client.request(
        "DELETE", f"/api/v1/memories/{second}", json={"reason": "obsolete for graph test"},
    )
    assert deleted.status_code == 200, deleted.text

    # Newest first: the first page holds [newest, third], the second page [oldest]
    first_page = (await http_client.get(
        "/api/v1/graph?node_types=memory&limit=2&offset=0",
    )).json()
    second_page = (await http_client.get(
        "/api/v1/graph?node_types=memory&limit=2&offset=2",
    )).json()

    edge_id = f"memory_{oldest}_memory_{newest}"
    assert {n["id"] for n in first_page["nodes"]} == {f"memory_{newest}", f"memory_{third}"}
    assert first_page["edges"] == []
    assert [e["id"] for e in first_page["cross_page_edges"]] == [edge_id]
    assert {n["id"] for n in second_page["nodes"]} == {f"memory_{oldest}"}
    assert second_page["edges"] == []
    # The obsolete memory is not reported
    assert [e["id"] for e in second_page["cross_page_edges"]] == [edge_id]
    assert second_page["meta"]["cross_page_edge_count"] == 1
