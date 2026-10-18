"""End-to-end tests for the subgraph traversal CTE on PostgreSQL.

Covers the recursive CTE behind GET /api/v1/graph/subgraph:
- the node_types filter applies to the neighbour type only, so an excluded
  center type does not hide its neighbours
- every node keeps its minimum depth in cyclic graphs
- work is bounded by the number of distinct nodes, not by the number of paths

Requires PostgreSQL with pgvector (provided by the conftest fixtures).
"""
import json
from uuid import uuid4

import pytest
from sqlalchemy import event, text

from app.config.settings import settings
from app.repositories.postgres.memory_repository import PostgresMemoryRepository

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.fixture(autouse=True)
def disable_auto_linking():
    """Disable auto-linking so only the links created by the test exist."""
    original_value = settings.MEMORY_NUM_AUTO_LINK
    settings.MEMORY_NUM_AUTO_LINK = 0
    yield
    settings.MEMORY_NUM_AUTO_LINK = original_value


async def _create_memory(http_client, title: str) -> int:
    response = await http_client.post("/api/v1/memories", json={
        "title": title,
        "content": f"{title} content",
        "context": "Subgraph traversal e2e",
        "keywords": ["subgraph", "traversal"],
        "tags": ["subgraph-traversal"],
        "importance": 6,
    })
    assert response.status_code in [200, 201], response.text
    return response.json()["id"]


async def _subgraph(http_client, center: str, node_types: str, depth: int = 1) -> dict:
    response = await http_client.get(
        f"/api/v1/graph/subgraph?node_id={center}&depth={depth}&node_types={node_types}",
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.e2e
async def test_subgraph_excluded_center_type_still_reaches_requested_neighbours(http_client):
    """node_types=project,memory around an entity returns both kinds of neighbour."""
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

    memory_id = await _create_memory(http_client, "Traversal Memory")
    link_resp = await http_client.post(
        f"/api/v1/entities/{entity_id}/memories", json={"memory_id": memory_id},
    )
    assert link_resp.status_code in [200, 201], link_resp.text

    data = await _subgraph(http_client, f"entity_{entity_id}", "project,memory")

    ids = {node["id"] for node in data["nodes"]}
    assert ids == {f"entity_{entity_id}", f"project_{project_id}", f"memory_{memory_id}"}
    assert data["meta"]["entity_project_count"] == 1
    assert data["meta"]["entity_memory_count"] == 1

    # Same rule from the project side: memory and entity requested, project excluded.
    memory_resp = await http_client.put(
        f"/api/v1/memories/{memory_id}", json={"project_ids": [project_id]},
    )
    assert memory_resp.status_code == 200, memory_resp.text
    data = await _subgraph(http_client, f"project_{project_id}", "memory,entity")
    ids = {node["id"] for node in data["nodes"]}
    assert ids == {f"project_{project_id}", f"memory_{memory_id}", f"entity_{entity_id}"}


@pytest.mark.e2e
async def test_subgraph_nodes_keep_minimum_depth_in_cyclic_graph(http_client):
    """Triangle 1-2-3 with a tail 3-4: depths are 0, 1, 1, 2 from memory 1."""
    ids = [await _create_memory(http_client, f"Cycle Memory {i}") for i in range(4)]
    m1, m2, m3, m4 = ids
    for source, target in [(m1, m2), (m2, m3), (m1, m3), (m3, m4)]:
        response = await http_client.post(
            f"/api/v1/memories/{source}/links", json={"related_ids": [target]},
        )
        assert response.status_code in [200, 201], response.text

    data = await _subgraph(http_client, f"memory_{m1}", "memory", depth=3)

    depths = {node["id"]: node["depth"] for node in data["nodes"]}
    assert depths == {
        f"memory_{m1}": 0,
        f"memory_{m2}": 1,
        f"memory_{m3}": 1,
        f"memory_{m4}": 2,
    }


def _find_plan_node(plan: dict, node_type: str) -> dict | None:
    if plan.get("Node Type") == node_type:
        return plan
    for child in plan.get("Plans", []):
        found = _find_plan_node(child, node_type)
        if found:
            return found
    return None


@pytest.mark.e2e
async def test_subgraph_traversal_work_is_bounded_by_distinct_nodes(db_adapter):
    """A project with N memories sharing E entities needs ~N+E rows, not ~N*E*N."""
    memory_count = 300
    entity_count = 3
    max_nodes = 200
    distinct_nodes = 1 + memory_count + entity_count
    user_id = uuid4()
    dimensions = settings.EMBEDDING_DIMENSIONS

    async with db_adapter.system_session() as session:
        await session.execute(
            text(
                "insert into users(id, external_id, name, email, updated_at, created_at) "
                "values (:i, :x, 'u', 'u@x', now(), now())",
            ),
            {"i": user_id, "x": str(user_id)},
        )
        project_id = (
            await session.execute(
                text(
                    "insert into projects(user_id, name, description, status, created_at, updated_at) "
                    "values (:u, 'p', 'd', 'active', now(), now()) returning id",
                ),
                {"u": user_id},
            )
        ).scalar()
        await session.execute(
            text(
                "insert into entities(user_id, name, entity_type, tags, created_at, updated_at) "
                "select :u, 'e' || g, 'other', ARRAY[]::varchar[], now(), now() "
                "from generate_series(1, :e) g",
            ),
            {"u": user_id, "e": entity_count},
        )
        await session.execute(
            text(
                "insert into memories(user_id, title, content, context, keywords, tags, importance, "
                "embedding, is_obsolete, created_at, updated_at) "
                "select :u, 't' || g, 'c', 'c', ARRAY[]::varchar[], ARRAY[]::varchar[], 5, "
                "array_fill(0.1::real, ARRAY[CAST(:dim AS INTEGER)])::vector, false, now(), now() "
                "from generate_series(1, :n) g",
            ),
            {"u": user_id, "n": memory_count, "dim": dimensions},
        )
        await session.execute(
            text(
                "insert into memory_project_association(memory_id, project_id) "
                "select id, :p from memories",
            ),
            {"p": project_id},
        )
        await session.execute(
            text(
                "insert into memory_entity_association(memory_id, entity_id) "
                "select m.id, e.id from memories m cross join entities e",
            ),
        )
        await session.execute(text("analyze"))

    # Capture the exact SQL the repository sends, then EXPLAIN ANALYZE it.
    captured: list[tuple[str, tuple]] = []

    def _capture(conn, cursor, statement, parameters, context, executemany):
        if "graph_traverse" in statement:
            captured.append((statement, parameters))

    engine = db_adapter._engine.sync_engine
    event.listen(engine, "before_cursor_execute", _capture)
    try:
        repo = PostgresMemoryRepository(db_adapter, None)
        nodes, truncated = await repo.get_subgraph_nodes(
            user_id=user_id,
            center_type="project",
            center_id=project_id,
            depth=3,
            include_memories=True,
            include_entities=True,
            include_projects=True,
            include_documents=True,
            include_code_artifacts=True,
            include_files=True,
            include_skills=True,
            include_plans=True,
            include_tasks=True,
            max_nodes=max_nodes,
        )
    finally:
        event.remove(engine, "before_cursor_execute", _capture)

    assert len(nodes) == max_nodes
    assert truncated is True
    assert captured, "traversal SQL was not captured"
    statement, parameters = captured[-1]

    async with db_adapter._engine.connect() as conn:
        result = await conn.exec_driver_sql(
            "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + statement, parameters,
        )
        plan_doc = result.scalar()
    if isinstance(plan_doc, str):
        plan_doc = json.loads(plan_doc)
    top = plan_doc[0]["Plan"]
    recursive_union = _find_plan_node(top, "Recursive Union")
    assert recursive_union is not None, f"no Recursive Union in plan: {json.dumps(top)[:500]}"

    cte_rows = recursive_union["Actual Rows"] * recursive_union.get("Actual Loops", 1)
    budget = 10 * distinct_nodes
    assert cte_rows <= budget, (
        f"recursive CTE produced {cte_rows} rows for {distinct_nodes} distinct nodes "
        f"(budget {budget}); it is enumerating paths"
    )
