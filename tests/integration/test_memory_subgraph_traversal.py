"""Integration tests for MemoryRepository.get_subgraph_nodes on in-memory SQLite.

Covers the recursive traversal behind GET /api/v1/graph/subgraph:
- neighbours whose id is a decimal prefix of an id already visited (1 vs 10)
- the node_types filter applies to the neighbour type only, for every edge type
- work is bounded by the number of distinct nodes, not by the number of paths
- each node keeps its minimum depth
"""
from contextlib import asynccontextmanager
from uuid import UUID, uuid4

import pytest
from sqlalchemy import event

from app.config.settings import settings
from app.repositories.sqlite.memory_repository import SqliteMemoryRepository
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter
from app.repositories.sqlite.sqlite_tables import (
    CodeArtifactsTable,
    DocumentsTable,
    EntitiesTable,
    EntityRelationshipsTable,
    FilesTable,
    MemoryLinkTable,
    MemoryTable,
    PlansTable,
    ProjectsTable,
    SkillsTable,
    TasksTable,
    UsersTable,
    entity_file_association,
    entity_project_association,
    memory_code_artifact_association,
    memory_document_association,
    memory_entity_association,
    memory_file_association,
    memory_project_association,
    memory_skill_association,
    skill_code_artifact_association,
    skill_document_association,
    skill_file_association,
)

NODE_TYPES = (
    "memory",
    "entity",
    "project",
    "document",
    "code_artifact",
    "file",
    "skill",
    "plan",
    "task",
)

# Every edge type the traversal knows about, as an undirected pair of node types.
EDGE_TYPE_PAIRS = [
    ("memory", "memory"),
    ("memory", "entity"),
    ("entity", "entity"),
    ("memory", "project"),
    ("memory", "document"),
    ("memory", "code_artifact"),
    ("document", "project"),
    ("code_artifact", "project"),
    ("entity", "project"),
    ("memory", "file"),
    ("file", "project"),
    ("entity", "file"),
    ("memory", "skill"),
    ("skill", "project"),
    ("skill", "file"),
    ("skill", "code_artifact"),
    ("skill", "document"),
    ("plan", "project"),
    ("plan", "task"),
]

# One test per direction of every edge type (36 traversal branches).
DIRECTED_EDGES = sorted(
    {(a, b) for a, b in EDGE_TYPE_PAIRS} | {(b, a) for a, b in EDGE_TYPE_PAIRS},
)


@asynccontextmanager
async def _sqlite_repo():
    """Fresh in-memory SQLite database with a user and the repository under test."""
    original_database = settings.DATABASE
    original_sqlite_memory = settings.SQLITE_MEMORY
    settings.DATABASE = "SQLite"
    settings.SQLITE_MEMORY = True

    db_adapter = SqliteDatabaseAdapter()
    try:
        await db_adapter.init_db()
        user_id = uuid4()
        async with db_adapter.system_session() as session:
            session.add(UsersTable(
                id=str(user_id),
                external_id=f"ext-{user_id}",
                name="Subgraph Tester",
                email="subgraph@example.com",
            ))
        repo = SqliteMemoryRepository(db_adapter=db_adapter, embedding_adapter=None)
        yield db_adapter, repo, user_id
    finally:
        try:
            await db_adapter.dispose()
        finally:
            settings.DATABASE = original_database
            settings.SQLITE_MEMORY = original_sqlite_memory


def _memories(user_id: UUID, ids):
    return [
        MemoryTable(
            id=i, user_id=str(user_id), title=f"m{i}", content="c", context="c",
            keywords=[], tags=[], importance=5,
        )
        for i in ids
    ]


def _entities(user_id: UUID, ids):
    return [
        EntitiesTable(id=i, user_id=str(user_id), name=f"e{i}", entity_type="Other", tags=[])
        for i in ids
    ]


def _projects(user_id: UUID, ids):
    return [
        ProjectsTable(id=i, user_id=str(user_id), name=f"p{i}", description="d")
        for i in ids
    ]


async def _traverse(repo, user_id, center_type, center_id, depth=1, include=NODE_TYPES, max_nodes=500):
    nodes, truncated = await repo.get_subgraph_nodes(
        user_id=user_id,
        center_type=center_type,
        center_id=center_id,
        depth=depth,
        include_memories="memory" in include,
        include_entities="entity" in include,
        include_projects="project" in include,
        include_documents="document" in include,
        include_code_artifacts="code_artifact" in include,
        include_files="file" in include,
        include_skills="skill" in include,
        include_plans="plan" in include,
        include_tasks="task" in include,
        max_nodes=max_nodes,
    )
    return {(n["node_type"], n["node_id"]): n["depth"] for n in nodes}, truncated


# ---------------------------------------------------------------------------
# Prefix ids: entity_1 must not be treated as visited because entity_10 is
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_neighbour_whose_id_is_a_prefix_of_the_center_is_returned():
    async with _sqlite_repo() as (db_adapter, repo, user_id):
        async with db_adapter.system_session() as session:
            session.add_all(_memories(user_id, range(1, 11)))
            session.add_all(_entities(user_id, range(1, 11)))
            await session.flush()
            session.add(MemoryLinkTable(user_id=str(user_id), source_id=10, target_id=1))
            session.add(EntityRelationshipsTable(
                user_id=str(user_id), source_entity_id=10, target_entity_id=1,
                relationship_type="knows",
            ))

        memory_nodes, _ = await _traverse(repo, user_id, "memory", 10, include=("memory",))
        assert memory_nodes == {("memory", 10): 0, ("memory", 1): 1}

        entity_nodes, _ = await _traverse(repo, user_id, "entity", 10, include=("entity",))
        assert entity_nodes == {("entity", 10): 0, ("entity", 1): 1}

        # Same relationship seen from the other end gives the same pair.
        entity_nodes, _ = await _traverse(repo, user_id, "entity", 1, include=("entity",))
        assert entity_nodes == {("entity", 1): 0, ("entity", 10): 1}


@pytest.mark.asyncio
async def test_prefix_id_reached_through_an_intermediate_node_is_returned():
    """project_12 -> memory_1 -> project_1: project_1 is a prefix of project_12."""
    async with _sqlite_repo() as (db_adapter, repo, user_id):
        async with db_adapter.system_session() as session:
            session.add_all(_projects(user_id, range(1, 13)))
            session.add_all(_memories(user_id, [1]))
            await session.flush()
            await session.execute(memory_project_association.insert(), [
                {"memory_id": 1, "project_id": 12},
                {"memory_id": 1, "project_id": 1},
            ])

        nodes, _ = await _traverse(repo, user_id, "project", 12, depth=2)

        assert nodes == {("project", 12): 0, ("memory", 1): 1, ("project", 1): 2}


# ---------------------------------------------------------------------------
# Depth bookkeeping survives de-duplication of visited nodes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nodes_keep_their_minimum_depth_in_cyclic_graphs():
    async with _sqlite_repo() as (db_adapter, repo, user_id):
        async with db_adapter.system_session() as session:
            session.add_all(_memories(user_id, range(1, 6)))
            await session.flush()
            # Triangle 1-2-3 plus a tail 3-4-5.
            session.add_all([
                MemoryLinkTable(user_id=str(user_id), source_id=s, target_id=t)
                for s, t in [(1, 2), (2, 3), (1, 3), (3, 4), (4, 5)]
            ])

        nodes, truncated = await _traverse(repo, user_id, "memory", 1, depth=3)
        assert truncated is False
        assert nodes == {
            ("memory", 1): 0,
            ("memory", 2): 1,
            ("memory", 3): 1,
            ("memory", 4): 2,
            ("memory", 5): 3,
        }

        shallow, _ = await _traverse(repo, user_id, "memory", 1, depth=2)
        assert ("memory", 5) not in shallow
        assert shallow[("memory", 4)] == 2


# ---------------------------------------------------------------------------
# node_types filter: the same rule for every edge type and both directions
# ---------------------------------------------------------------------------


async def _seed_universe(db_adapter, user_id: UUID) -> None:
    """One node of every type with id 1, wired together by every edge type.

    memory_2 and entity_2 exist only to give the memory-memory and entity-entity
    edge types a second endpoint.
    """
    uid = str(user_id)
    async with db_adapter.system_session() as session:
        session.add_all(_projects(user_id, [1]))
        session.add_all(_memories(user_id, [1, 2]))
        session.add_all(_entities(user_id, [1, 2]))
        await session.flush()
        session.add_all([
            DocumentsTable(
                id=1, user_id=uid, project_id=1, title="d", description="d",
                content="c", size_bytes=1, tags=[],
            ),
            CodeArtifactsTable(
                id=1, user_id=uid, project_id=1, title="c", description="d",
                code="x = 1", language="python", tags=[],
            ),
            FilesTable(
                id=1, user_id=uid, project_id=1, filename="f.txt", description="d",
                data=b"x", mime_type="text/plain", size_bytes=1, tags=[],
            ),
            SkillsTable(
                id=1, user_id=uid, project_id=1, name="s", description="d",
                content="c", tags=[],
            ),
            PlansTable(id=1, user_id=uid, project_id=1, title="plan"),
        ])
        await session.flush()
        session.add(TasksTable(id=1, user_id=uid, plan_id=1, title="task"))
        session.add(MemoryLinkTable(user_id=uid, source_id=1, target_id=2))
        session.add(EntityRelationshipsTable(
            user_id=uid, source_entity_id=1, target_entity_id=2, relationship_type="knows",
        ))
        await session.flush()
        for table, values in [
            (memory_entity_association, {"memory_id": 1, "entity_id": 1}),
            (memory_project_association, {"memory_id": 1, "project_id": 1}),
            (memory_document_association, {"memory_id": 1, "document_id": 1}),
            (memory_code_artifact_association, {"memory_id": 1, "code_artifact_id": 1}),
            (memory_file_association, {"memory_id": 1, "file_id": 1}),
            (memory_skill_association, {"memory_id": 1, "skill_id": 1}),
            (entity_project_association, {"entity_id": 1, "project_id": 1}),
            (entity_file_association, {"entity_id": 1, "file_id": 1}),
            (skill_file_association, {"skill_id": 1, "file_id": 1}),
            (skill_code_artifact_association, {"skill_id": 1, "code_artifact_id": 1}),
            (skill_document_association, {"skill_id": 1, "document_id": 1}),
        ]:
            await session.execute(table.insert().values(**values))


@pytest.fixture(scope="module")
async def universe():
    async with _sqlite_repo() as (db_adapter, repo, user_id):
        await _seed_universe(db_adapter, user_id)
        yield repo, user_id


def test_edge_table_lists_every_traversal_branch():
    assert len(EDGE_TYPE_PAIRS) == 19
    assert len(DIRECTED_EDGES) == 36
    assert {t for pair in EDGE_TYPE_PAIRS for t in pair} == set(NODE_TYPES)


@pytest.mark.asyncio
@pytest.mark.parametrize(("source", "target"), DIRECTED_EDGES)
async def test_requested_neighbour_type_is_returned_whether_or_not_center_type_is_requested(
    universe, source, target,
):
    """node_types=[target] around a source center returns the target neighbour.

    The center is always part of the result; its own type does not have to be in
    node_types for the neighbours of a requested type to be reachable.
    """
    repo, user_id = universe
    neighbour_id = 2 if source == target else 1

    nodes, _ = await _traverse(repo, user_id, source, 1, depth=1, include=(target,))

    assert nodes == {(source, 1): 0, (target, neighbour_id): 1}


@pytest.mark.asyncio
async def test_excluded_center_does_not_leak_neighbours_of_unrequested_types(universe):
    repo, user_id = universe

    nodes, _ = await _traverse(repo, user_id, "entity", 1, depth=3, include=("project", "memory"))

    assert {t for t, _ in nodes} <= {"entity", "project", "memory"}
    assert ("entity", 1) in nodes
    assert ("entity", 2) not in nodes
    assert nodes[("memory", 1)] == 1
    assert nodes[("project", 1)] == 1


@pytest.mark.asyncio
async def test_no_requested_types_returns_only_the_center(universe):
    repo, user_id = universe

    nodes, truncated = await _traverse(repo, user_id, "memory", 1, depth=3, include=())

    assert nodes == {("memory", 1): 0}
    assert truncated is False


# ---------------------------------------------------------------------------
# Work is bounded by distinct nodes, not by the number of simple paths
# ---------------------------------------------------------------------------


async def _hub_traversal_vm_steps(memory_count: int) -> tuple[int, int, bool]:
    """Count SQLite VM instructions (in thousands) to traverse a hub of memories.

    Every memory is linked to the same three entities and the same project, so the
    number of simple paths at depth 3 grows with the square of memory_count while
    the number of distinct nodes grows linearly.
    """
    async with _sqlite_repo() as (db_adapter, repo, user_id):
        async with db_adapter.system_session() as session:
            session.add_all(_projects(user_id, [1]))
            session.add_all(_entities(user_id, [1, 2, 3]))
            session.add_all(_memories(user_id, range(1, memory_count + 1)))
            await session.flush()
            await session.execute(memory_project_association.insert(), [
                {"memory_id": m, "project_id": 1} for m in range(1, memory_count + 1)
            ])
            await session.execute(memory_entity_association.insert(), [
                {"memory_id": m, "entity_id": e}
                for m in range(1, memory_count + 1)
                for e in (1, 2, 3)
            ])

        ticks = {"count": 0}

        def _tick():
            ticks["count"] += 1
            return 0

        def _install_progress_handler(dbapi_conn, connection_record, connection_proxy):
            dbapi_conn._connection._conn.set_progress_handler(_tick, 1000)

        # Connections are not pooled, so every traversal checks out a new one.
        event.listen(db_adapter._engine.sync_engine, "checkout", _install_progress_handler)

        nodes, truncated = await _traverse(
            repo, user_id, "entity", 1, depth=3, max_nodes=50,
        )
        return ticks["count"], len(nodes), truncated


@pytest.mark.asyncio
async def test_traversal_work_grows_linearly_with_hub_size():
    small_steps, small_nodes, small_truncated = await _hub_traversal_vm_steps(120)
    large_steps, large_nodes, large_truncated = await _hub_traversal_vm_steps(240)

    assert small_steps > 0 and large_steps > 0, "progress handler observed no VM work"
    assert small_nodes == large_nodes == 50
    assert small_truncated and large_truncated
    # Enumerating simple paths multiplies the work by about 4 when the hub doubles.
    assert large_steps / small_steps < 3.0, (
        f"doubling the hub multiplied the work by {large_steps / small_steps:.2f}x"
    )


@pytest.mark.asyncio
async def test_hub_traversal_returns_every_distinct_node_once():
    async with _sqlite_repo() as (db_adapter, repo, user_id):
        async with db_adapter.system_session() as session:
            session.add_all(_projects(user_id, [1]))
            session.add_all(_entities(user_id, [1, 2]))
            session.add_all(_memories(user_id, range(1, 41)))
            await session.flush()
            await session.execute(memory_project_association.insert(), [
                {"memory_id": m, "project_id": 1} for m in range(1, 41)
            ])
            await session.execute(memory_entity_association.insert(), [
                {"memory_id": m, "entity_id": e} for m in range(1, 41) for e in (1, 2)
            ])

        nodes, truncated = await _traverse(repo, user_id, "project", 1, depth=3)

        assert truncated is False
        assert len(nodes) == 1 + 40 + 2
        assert nodes[("project", 1)] == 0
        assert {d for (t, _), d in nodes.items() if t == "memory"} == {1}
        assert {d for (t, _), d in nodes.items() if t == "entity"} == {2}
