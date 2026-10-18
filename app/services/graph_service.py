"""Graph Service - Business logic for graph traversal and visualization

This service implements functionality for efficient graph visualization:
    - Subgraph traversal using recursive CTEs
    - Fetching full node data for memory, entity, project, document, and code_artifact nodes
    - Building edges between nodes in the subgraph
"""
import re
from typing import Any, Protocol
from uuid import UUID

from app.config.logging_config import logging
from app.config.settings import settings
from app.exceptions import NotFoundError
from app.models.graph_models import (
    SubgraphEdge,
    SubgraphMeta,
    SubgraphNode,
    SubgraphResponse,
)
from app.models.memory_models import Memory
from app.protocols.entity_protocol import EntityRepository
from app.protocols.memory_protocol import MemoryRepository

logger = logging.getLogger(__name__)

# Regex pattern for parsing node IDs. Matched with fullmatch(): ASCII digits only, so a
# trailing newline or non-ASCII decimal digits are not valid ids.
NODE_ID_PATTERN = re.compile(r"(memory|entity|project|document|code_artifact|file|skill|plan|task)_([0-9]+)")

# Largest id a node_id may carry: object ids are signed 32-bit INTEGER columns on PostgreSQL,
# and drivers raise on a larger value instead of matching no row.
MAX_NODE_ID = 2**31 - 1


# Protocol for project service (to avoid circular imports)
class ProjectServiceProtocol(Protocol):
    async def get_project(self, user_id: UUID, project_id: int) -> Any: ...


# Protocol for document service (to avoid circular imports)
class DocumentServiceProtocol(Protocol):
    async def get_document(self, user_id: UUID, document_id: int) -> Any: ...


# Protocol for code artifact service (to avoid circular imports)
class CodeArtifactServiceProtocol(Protocol):
    async def get_code_artifact(self, user_id: UUID, artifact_id: int) -> Any: ...


# Protocol for file service (to avoid circular imports)
class FileServiceProtocol(Protocol):
    async def get_file(self, user_id: UUID, file_id: int) -> Any: ...
    async def list_files(self, user_id: UUID, **kwargs) -> Any: ...


# Protocol for skill service (to avoid circular imports)
class SkillServiceProtocol(Protocol):
    async def get_skill(self, user_id: UUID, skill_id: int) -> Any: ...
    async def get_all_skill_file_links(self, user_id: UUID) -> list[tuple[int, int]]: ...
    async def get_all_skill_code_artifact_links(self, user_id: UUID) -> list[tuple[int, int]]: ...
    async def get_all_skill_document_links(self, user_id: UUID) -> list[tuple[int, int]]: ...


# Protocol for plan service (to avoid circular imports)
class PlanServiceProtocol(Protocol):
    async def get_plan(self, user_id: UUID, plan_id: int) -> Any: ...
    async def list_plans(self, user_id: UUID, **kwargs) -> Any: ...


# Protocol for task service (to avoid circular imports)
class TaskServiceProtocol(Protocol):
    async def get_task(self, user_id: UUID, task_id: int) -> Any: ...
    async def list_tasks_for_user(
        self, user_id: UUID, plan_ids: list[int] | None = None,
    ) -> Any: ...


class GraphService:
    """Service layer for graph traversal operations.

    Handles business logic for efficient subgraph extraction using
    recursive CTE queries. Coordinates between memory, entity, project,
    document, and code_artifact repositories to build complete subgraph responses.
    """

    def __init__(
        self,
        memory_repo: MemoryRepository,
        entity_repo: EntityRepository,
        project_service: ProjectServiceProtocol | None = None,
        document_service: DocumentServiceProtocol | None = None,
        code_artifact_service: CodeArtifactServiceProtocol | None = None,
        file_service: FileServiceProtocol | None = None,
        skill_service: SkillServiceProtocol | None = None,
        plan_service: PlanServiceProtocol | None = None,
        task_service: TaskServiceProtocol | None = None,
    ):
        """Initialize with repository protocols and optional services."""
        self.memory_repo = memory_repo
        self.entity_repo = entity_repo
        self.project_service = project_service
        self.document_service = document_service
        self.code_artifact_service = code_artifact_service
        self.file_service = file_service
        self.skill_service = skill_service
        self.plan_service = plan_service
        self.task_service = task_service
        logger.info("Graph service initialized")

    @staticmethod
    def parse_node_id(node_id: str) -> tuple[str, int]:
        """Parse node_id string into type and numeric ID.

        Args:
            node_id: Format 'memory_123', 'entity_456', 'project_789',
                     'document_123', 'code_artifact_456', or 'skill_789'

        Returns:
            Tuple of (node_type, numeric_id)

        Raises:
            ValueError: If node_id format is invalid or the id is out of range
        """
        match = NODE_ID_PATTERN.fullmatch(node_id)
        if not match:
            raise ValueError(
                f"Invalid node_id format: '{node_id}'. "
                "Expected 'memory_{id}', 'entity_{id}', 'project_{id}', "
                "'document_{id}', 'code_artifact_{id}', 'file_{id}', 'skill_{id}', "
                "'plan_{id}', or 'task_{id}'.",
            )
        numeric_id = int(match.group(2))
        if numeric_id > MAX_NODE_ID:
            raise ValueError(
                f"Invalid node_id: '{node_id}' is out of range (maximum id is {MAX_NODE_ID}).",
            )
        return match.group(1), numeric_id

    async def get_linked_memory_ids_outside(
        self,
        user_id: UUID,
        memories: list[Memory],
        project_ids: list[int] | None = None,
    ) -> set[int]:
        """Return the ids of memories that ``memories`` link to but that are not part of it.

        The full graph lists memories page by page, so a link between memories on different
        pages has its second endpoint on another page. Only memories that the listing itself
        would return are kept: obsolete memories, and memories outside ``project_ids`` when a
        project filter is given, are left out.

        Args:
            user_id: User ID for ownership filtering
            memories: The memories of the current page
            project_ids: Project filter used for the listing, if any

        Returns:
            Ids of linked memories that are listed on some other page
        """
        listed_ids = {memory.id for memory in memories}
        outside_ids = sorted({
            linked_id
            for memory in memories
            for linked_id in memory.linked_memory_ids
            if linked_id not in listed_ids
        })
        return await self.memory_repo.get_listed_memory_ids(
            user_id=user_id,
            memory_ids=outside_ids,
            project_ids=project_ids,
        )

    async def get_subgraph(
        self,
        user_id: UUID,
        center_node_id: str,
        depth: int = 2,
        node_types: list[str] | None = None,
        max_nodes: int = 200,
    ) -> SubgraphResponse:
        """Get subgraph centered on a node using recursive CTE traversal.

        Performs efficient graph traversal in a single database query,
        then fetches full node data and builds edges between nodes.

        Args:
            user_id: User ID for ownership filtering
            center_node_id: Format 'memory_123', 'entity_456', 'project_789',
                           'document_123', or 'code_artifact_456'
            depth: Traversal depth 1-3 (default 2, clamped)
            node_types: Filter to any combination of ['memory', 'entity', 'project',
                       'document', 'code_artifact'] (default: all 5 types)
            max_nodes: Safety limit (default 200, max configurable via
                       MAX_GRAPH_LIMIT setting / env var, defaults to 2000)

        Returns:
            SubgraphResponse with nodes, edges, and metadata

        Raises:
            ValueError: If center_node_id format is invalid
            NotFoundError: If center node doesn't exist
        """
        # Parse and validate center node; report the canonical id (e.g. 'memory_001' -> 'memory_1')
        # so meta.center_node_id always matches a node id in the response
        center_type, center_id = self.parse_node_id(center_node_id)
        center_node_id = f"{center_type}_{center_id}"

        # Validate center node exists
        await self._validate_center_node(user_id, center_type, center_id)

        # Clamp parameters (max_nodes cap is configurable via MAX_GRAPH_LIMIT, see issue #23)
        depth = max(1, min(depth, 3))
        max_nodes = max(1, min(max_nodes, settings.MAX_GRAPH_LIMIT))

        # Determine which node types to include (default: all types)
        if node_types is None:
            node_types = ["memory", "entity", "project", "document", "code_artifact", "file", "skill", "plan", "task"]
        include_memories = "memory" in node_types
        include_entities = "entity" in node_types
        include_projects = "project" in node_types
        include_documents = "document" in node_types
        include_code_artifacts = "code_artifact" in node_types
        include_files = "file" in node_types
        include_skills = "skill" in node_types
        include_plans = "plan" in node_types
        include_tasks = "task" in node_types

        logger.info(
            "Starting subgraph traversal",
            extra={
                "user_id": str(user_id),
                "center_node_id": center_node_id,
                "depth": depth,
                "node_types": node_types,
                "max_nodes": max_nodes,
            },
        )

        # Execute CTE query to get node IDs with depths
        raw_nodes, truncated = await self.memory_repo.get_subgraph_nodes(
            user_id=user_id,
            center_type=center_type,
            center_id=center_id,
            depth=depth,
            include_memories=include_memories,
            include_entities=include_entities,
            include_projects=include_projects,
            include_documents=include_documents,
            include_code_artifacts=include_code_artifacts,
            include_files=include_files,
            include_skills=include_skills,
            include_plans=include_plans,
            include_tasks=include_tasks,
            max_nodes=max_nodes,
        )

        # Separate node IDs by type
        memory_ids = [n["node_id"] for n in raw_nodes if n["node_type"] == "memory"]
        entity_ids = [n["node_id"] for n in raw_nodes if n["node_type"] == "entity"]
        project_ids = [n["node_id"] for n in raw_nodes if n["node_type"] == "project"]
        document_ids = [n["node_id"] for n in raw_nodes if n["node_type"] == "document"]
        code_artifact_ids = [n["node_id"] for n in raw_nodes if n["node_type"] == "code_artifact"]
        file_ids = [n["node_id"] for n in raw_nodes if n["node_type"] == "file"]
        skill_ids = [n["node_id"] for n in raw_nodes if n["node_type"] == "skill"]
        plan_ids = [n["node_id"] for n in raw_nodes if n["node_type"] == "plan"]
        task_ids = [n["node_id"] for n in raw_nodes if n["node_type"] == "task"]

        # Build depth lookup
        depth_lookup = {
            (n["node_type"], n["node_id"]): n["depth"]
            for n in raw_nodes
        }

        # Fetch tasks once (used by both _fetch_node_data and _fetch_edges)
        # When subgraph contains tasks but no plans, fall back to plan_ids=None.
        task_summaries: list = []
        if task_ids and self.task_service:
            try:
                task_filter = plan_ids if plan_ids else None
                task_summaries = await self.task_service.list_tasks_for_user(
                    user_id=user_id, plan_ids=task_filter,
                )
            except Exception:
                logger.warning("Failed to fetch task summaries for graph nodes")
                task_summaries = []

        # Fetch full node data
        nodes = await self._fetch_node_data(
            user_id, memory_ids, entity_ids, project_ids, document_ids, code_artifact_ids,
            file_ids, skill_ids, depth_lookup,
            plan_ids=plan_ids, task_ids=task_ids, task_summaries=task_summaries,
        )

        # Fetch edges between nodes in the subgraph
        edges = await self._fetch_edges(
            user_id, memory_ids, entity_ids, project_ids, document_ids, code_artifact_ids,
            file_ids, skill_ids,
            plan_ids=plan_ids, task_ids=task_ids, task_summaries=task_summaries,
        )

        # Build metadata
        memory_count = len([n for n in nodes if n.type == "memory"])
        entity_count = len([n for n in nodes if n.type == "entity"])
        project_count = len([n for n in nodes if n.type == "project"])
        document_count = len([n for n in nodes if n.type == "document"])
        code_artifact_count = len([n for n in nodes if n.type == "code_artifact"])
        file_count = len([n for n in nodes if n.type == "file"])
        skill_count = len([n for n in nodes if n.type == "skill"])
        plan_count = len([n for n in nodes if n.type == "plan"])
        task_count = len([n for n in nodes if n.type == "task"])
        memory_link_count = len([e for e in edges if e.type == "memory_link"])
        entity_relationship_count = len([e for e in edges if e.type == "entity_relationship"])
        entity_memory_count = len([e for e in edges if e.type == "entity_memory"])
        entity_project_count = len([e for e in edges if e.type == "entity_project"])
        memory_project_count = len([e for e in edges if e.type == "memory_project"])
        document_project_count = len([e for e in edges if e.type == "document_project"])
        code_artifact_project_count = len([e for e in edges if e.type == "code_artifact_project"])
        memory_document_count = len([e for e in edges if e.type == "memory_document"])
        memory_code_artifact_count = len([e for e in edges if e.type == "memory_code_artifact"])
        memory_file_count = len([e for e in edges if e.type == "memory_file"])
        file_project_count = len([e for e in edges if e.type == "file_project"])
        entity_file_count = len([e for e in edges if e.type == "entity_file"])
        memory_skill_count = len([e for e in edges if e.type == "memory_skill"])
        skill_project_count = len([e for e in edges if e.type == "skill_project"])
        skill_file_count = len([e for e in edges if e.type == "skill_file"])
        skill_code_artifact_count = len([e for e in edges if e.type == "skill_code_artifact"])
        skill_document_count = len([e for e in edges if e.type == "skill_document"])
        plan_project_count = len([e for e in edges if e.type == "plan_project"])
        plan_task_count = len([e for e in edges if e.type == "plan_task"])

        meta = SubgraphMeta(
            center_node_id=center_node_id,
            depth=depth,
            node_types=node_types,
            max_nodes=max_nodes,
            memory_count=memory_count,
            entity_count=entity_count,
            project_count=project_count,
            document_count=document_count,
            code_artifact_count=code_artifact_count,
            file_count=file_count,
            edge_count=len(edges),
            memory_link_count=memory_link_count,
            entity_relationship_count=entity_relationship_count,
            entity_memory_count=entity_memory_count,
            entity_project_count=entity_project_count,
            memory_project_count=memory_project_count,
            document_project_count=document_project_count,
            code_artifact_project_count=code_artifact_project_count,
            memory_document_count=memory_document_count,
            memory_code_artifact_count=memory_code_artifact_count,
            memory_file_count=memory_file_count,
            file_project_count=file_project_count,
            entity_file_count=entity_file_count,
            skill_count=skill_count,
            memory_skill_count=memory_skill_count,
            skill_project_count=skill_project_count,
            skill_file_count=skill_file_count,
            skill_code_artifact_count=skill_code_artifact_count,
            skill_document_count=skill_document_count,
            plan_count=plan_count,
            task_count=task_count,
            plan_project_count=plan_project_count,
            plan_task_count=plan_task_count,
            truncated=truncated,
        )

        logger.info(
            "Subgraph traversal completed",
            extra={
                "user_id": str(user_id),
                "center_node_id": center_node_id,
                "nodes_count": len(nodes),
                "edges_count": len(edges),
                "truncated": truncated,
            },
        )

        return SubgraphResponse(nodes=nodes, edges=edges, meta=meta)

    async def _validate_center_node(
        self,
        user_id: UUID,
        center_type: str,
        center_id: int,
    ) -> None:
        """Validate that the center node exists.

        Raises:
            NotFoundError: If center node doesn't exist
        """
        if center_type == "memory":
            await self.memory_repo.get_memory_by_id(
                user_id=user_id,
                memory_id=center_id,
            )
        elif center_type == "entity":
            entity = await self.entity_repo.get_entity_by_id(
                user_id=user_id,
                entity_id=center_id,
            )
            if entity is None:
                raise NotFoundError(f"Entity {center_id} not found")
        elif center_type == "project":
            if self.project_service is None:
                raise NotFoundError("Project service not available")
            project = await self.project_service.get_project(
                user_id=user_id,
                project_id=center_id,
            )
            if project is None:
                raise NotFoundError(f"Project {center_id} not found")
        elif center_type == "document":
            if self.document_service is None:
                raise NotFoundError("Document service not available")
            document = await self.document_service.get_document(
                user_id=user_id,
                document_id=center_id,
            )
            if document is None:
                raise NotFoundError(f"Document {center_id} not found")
        elif center_type == "code_artifact":
            if self.code_artifact_service is None:
                raise NotFoundError("Code artifact service not available")
            artifact = await self.code_artifact_service.get_code_artifact(
                user_id=user_id,
                artifact_id=center_id,
            )
            if artifact is None:
                raise NotFoundError(f"Code artifact {center_id} not found")
        elif center_type == "file":
            if self.file_service is None:
                raise NotFoundError("File service not available")
            file = await self.file_service.get_file(
                user_id=user_id,
                file_id=center_id,
            )
            if file is None:
                raise NotFoundError(f"File {center_id} not found")
        elif center_type == "skill":
            if self.skill_service is None:
                raise NotFoundError("Skill service not available")
            skill = await self.skill_service.get_skill(
                user_id=user_id,
                skill_id=center_id,
            )
            if skill is None:
                raise NotFoundError(f"Skill {center_id} not found")
        elif center_type == "plan":
            if self.plan_service is None:
                raise NotFoundError("Plan service not available")
            plan = await self.plan_service.get_plan(
                user_id=user_id,
                plan_id=center_id,
            )
            if plan is None:
                raise NotFoundError(f"Plan {center_id} not found")
        elif center_type == "task":
            if self.task_service is None:
                raise NotFoundError("Task service not available")
            task = await self.task_service.get_task(
                user_id=user_id,
                task_id=center_id,
            )
            if task is None:
                raise NotFoundError(f"Task {center_id} not found")
        else:
            raise ValueError(f"Unknown center_type: {center_type}")

    async def _fetch_node_data(
        self,
        user_id: UUID,
        memory_ids: list[int],
        entity_ids: list[int],
        project_ids: list[int],
        document_ids: list[int],
        code_artifact_ids: list[int],
        file_ids: list[int],
        skill_ids: list[int],
        depth_lookup: dict,
        plan_ids: list[int] | None = None,
        task_ids: list[int] | None = None,
        task_summaries: list | None = None,
    ) -> list[SubgraphNode]:
        """Fetch full data for all node types.

        Args:
            user_id: User ID for ownership
            memory_ids: List of memory IDs to fetch
            entity_ids: List of entity IDs to fetch
            project_ids: List of project IDs to fetch
            document_ids: List of document IDs to fetch
            code_artifact_ids: List of code artifact IDs to fetch
            file_ids: List of file IDs to fetch
            skill_ids: List of skill IDs to fetch
            depth_lookup: Dict mapping (type, id) to depth

        Returns:
            List of SubgraphNode with full data
        """
        nodes: list[SubgraphNode] = []

        # Fetch memories
        for memory_id in memory_ids:
            try:
                memory = await self.memory_repo.get_memory_by_id(
                    user_id=user_id,
                    memory_id=memory_id,
                )
                nodes.append(SubgraphNode(
                    id=f"memory_{memory.id}",
                    type="memory",
                    depth=depth_lookup.get(("memory", memory_id), 0),
                    label=memory.title,
                    data={
                        "id": memory.id,
                        "title": memory.title,
                        "importance": memory.importance,
                        "tags": memory.tags,
                        "created_at": memory.created_at.isoformat() if memory.created_at else None,
                    },
                ))
            except NotFoundError:
                # Skip if memory was deleted during traversal
                logger.warning(f"Memory {memory_id} not found during fetch")
                continue

        # Fetch entities
        for entity_id in entity_ids:
            entity = await self.entity_repo.get_entity_by_id(
                user_id=user_id,
                entity_id=entity_id,
            )
            if entity is None:
                # Skip if entity was deleted during traversal
                logger.warning(f"Entity {entity_id} not found during fetch")
                continue
            nodes.append(SubgraphNode(
                id=f"entity_{entity.id}",
                type="entity",
                depth=depth_lookup.get(("entity", entity_id), 0),
                label=entity.name,
                data={
                    "id": entity.id,
                    "name": entity.name,
                    "entity_type": entity.entity_type.value if hasattr(entity.entity_type, "value") else entity.entity_type,
                    "created_at": entity.created_at.isoformat() if entity.created_at else None,
                },
            ))

        # Fetch projects
        if self.project_service and project_ids:
            for project_id in project_ids:
                try:
                    project = await self.project_service.get_project(
                        user_id=user_id,
                        project_id=project_id,
                    )
                    if project is None:
                        logger.warning(f"Project {project_id} not found during fetch")
                        continue
                    nodes.append(SubgraphNode(
                        id=f"project_{project.id}",
                        type="project",
                        depth=depth_lookup.get(("project", project_id), 0),
                        label=project.name,
                        data={
                            "id": project.id,
                            "name": project.name,
                            "description": project.description,
                            "project_type": project.project_type.value if hasattr(project.project_type, "value") else project.project_type,
                            "status": project.status.value if hasattr(project.status, "value") else project.status,
                            "created_at": project.created_at.isoformat() if project.created_at else None,
                        },
                    ))
                except NotFoundError:
                    logger.warning(f"Project {project_id} not found during fetch")
                    continue

        # Fetch documents
        if self.document_service and document_ids:
            for document_id in document_ids:
                try:
                    document = await self.document_service.get_document(
                        user_id=user_id,
                        document_id=document_id,
                    )
                    if document is None:
                        logger.warning(f"Document {document_id} not found during fetch")
                        continue
                    nodes.append(SubgraphNode(
                        id=f"document_{document.id}",
                        type="document",
                        depth=depth_lookup.get(("document", document_id), 0),
                        label=document.title,
                        data={
                            "id": document.id,
                            "title": document.title,
                            "description": document.description,
                            "document_type": document.document_type.value if hasattr(document.document_type, "value") else document.document_type,
                            "project_id": document.project_id,
                            "created_at": document.created_at.isoformat() if document.created_at else None,
                        },
                    ))
                except NotFoundError:
                    logger.warning(f"Document {document_id} not found during fetch")
                    continue

        # Fetch code artifacts
        if self.code_artifact_service and code_artifact_ids:
            for artifact_id in code_artifact_ids:
                try:
                    artifact = await self.code_artifact_service.get_code_artifact(
                        user_id=user_id,
                        artifact_id=artifact_id,
                    )
                    if artifact is None:
                        logger.warning(f"Code artifact {artifact_id} not found during fetch")
                        continue
                    nodes.append(SubgraphNode(
                        id=f"code_artifact_{artifact.id}",
                        type="code_artifact",
                        depth=depth_lookup.get(("code_artifact", artifact_id), 0),
                        label=artifact.title,
                        data={
                            "id": artifact.id,
                            "title": artifact.title,
                            "description": artifact.description,
                            "language": artifact.language,
                            "project_id": artifact.project_id,
                            "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
                        },
                    ))
                except NotFoundError:
                    logger.warning(f"Code artifact {artifact_id} not found during fetch")
                    continue

        # Fetch files (use list_files once to get summaries, avoids loading binary data)
        if self.file_service and file_ids:
            try:
                file_summaries = await self.file_service.list_files(user_id=user_id)
                file_summary_map = {f.id: f for f in file_summaries}
                for file_id in file_ids:
                    file_summary = file_summary_map.get(file_id)
                    if file_summary is None:
                        logger.warning(f"File {file_id} not found during fetch")
                        continue
                    nodes.append(SubgraphNode(
                        id=f"file_{file_summary.id}",
                        type="file",
                        depth=depth_lookup.get(("file", file_id), 0),
                        label=file_summary.filename,
                        data={
                            "id": file_summary.id,
                            "filename": file_summary.filename,
                            "description": file_summary.description,
                            "mime_type": file_summary.mime_type,
                            "size_bytes": file_summary.size_bytes,
                            "project_id": file_summary.project_id,
                            "created_at": file_summary.created_at.isoformat() if file_summary.created_at else None,
                        },
                    ))
            except Exception:
                logger.warning("Failed to fetch file summaries for graph nodes")

        # Fetch skills
        if self.skill_service and skill_ids:
            for skill_id in skill_ids:
                try:
                    skill = await self.skill_service.get_skill(
                        user_id=user_id,
                        skill_id=skill_id,
                    )
                    if skill is None:
                        logger.warning(f"Skill {skill_id} not found during fetch")
                        continue
                    nodes.append(SubgraphNode(
                        id=f"skill_{skill.id}",
                        type="skill",
                        depth=depth_lookup.get(("skill", skill_id), 0),
                        label=skill.name,
                        data={
                            "id": skill.id,
                            "name": skill.name,
                            "description": skill.description,
                            "created_at": skill.created_at.isoformat() if skill.created_at else None,
                        },
                    ))
                except NotFoundError:
                    logger.warning(f"Skill {skill_id} not found during fetch")
                    continue

        # Fetch plans
        if self.plan_service and plan_ids:
            for plan_id in plan_ids:
                try:
                    plan = await self.plan_service.get_plan(
                        user_id=user_id,
                        plan_id=plan_id,
                    )
                    if plan is None:
                        logger.warning(f"Plan {plan_id} not found during fetch")
                        continue
                    nodes.append(SubgraphNode(
                        id=f"plan_{plan.id}",
                        type="plan",
                        depth=depth_lookup.get(("plan", plan_id), 0),
                        label=plan.title,
                        data={
                            "id": plan.id,
                            "title": plan.title,
                            "status": plan.status.value if hasattr(plan.status, "value") else plan.status,
                            "project_id": plan.project_id,
                            "created_at": plan.created_at.isoformat() if plan.created_at else None,
                        },
                    ))
                except NotFoundError:
                    logger.warning(f"Plan {plan_id} not found during fetch")
                    continue

        # Fetch tasks (use pre-fetched task_summaries if provided to avoid re-fetching)
        if task_ids:
            task_id_set = set(task_ids)
            task_map = {t.id: t for t in (task_summaries or []) if t.id in task_id_set}
            for task_id in task_ids:
                t = task_map.get(task_id)
                if t is None:
                    logger.warning(f"Task {task_id} not found during fetch")
                    continue
                nodes.append(SubgraphNode(
                    id=f"task_{t.id}",
                    type="task",
                    depth=depth_lookup.get(("task", task_id), 0),
                    label=t.title,
                    data={
                        "id": t.id,
                        "title": t.title,
                        "plan_id": t.plan_id,
                        "state": t.state.value if hasattr(t.state, "value") else t.state,
                        "priority": t.priority.value if hasattr(t.priority, "value") else t.priority,
                        "assigned_agent": t.assigned_agent,
                        "criteria_met": t.criteria_met,
                        "criteria_total": t.criteria_total,
                        "blocked": t.blocked,
                        "created_at": t.created_at.isoformat() if t.created_at else None,
                    },
                ))

        return nodes

    async def _fetch_edges(
        self,
        user_id: UUID,
        memory_ids: list[int],
        entity_ids: list[int],
        project_ids: list[int],
        document_ids: list[int],
        code_artifact_ids: list[int],
        file_ids: list[int] | None = None,
        skill_ids: list[int] | None = None,
        plan_ids: list[int] | None = None,
        task_ids: list[int] | None = None,
        task_summaries: list | None = None,
    ) -> list[SubgraphEdge]:
        """Fetch all edges between nodes in the subgraph.

        Retrieves:
        - Memory-to-memory links
        - Entity-to-memory links
        - Entity-to-entity relationships
        - Memory-to-project links
        - Document-to-project links
        - CodeArtifact-to-project links
        - Memory-to-document links
        - Memory-to-code_artifact links
        - Memory-to-skill links
        - Skill-to-project links
        - Skill-to-file links
        - Skill-to-code_artifact links
        - Skill-to-document links

        Args:
            user_id: User ID for ownership
            memory_ids: List of memory IDs in subgraph
            entity_ids: List of entity IDs in subgraph
            project_ids: List of project IDs in subgraph
            document_ids: List of document IDs in subgraph
            code_artifact_ids: List of code artifact IDs in subgraph
            file_ids: List of file IDs in subgraph
            skill_ids: List of skill IDs in subgraph

        Returns:
            List of SubgraphEdge
        """
        edges: list[SubgraphEdge] = []
        seen_edge_ids: set[str] = set()

        memory_id_set = set(memory_ids)
        entity_id_set = set(entity_ids)
        project_id_set = set(project_ids)
        document_id_set = set(document_ids)
        code_artifact_id_set = set(code_artifact_ids)
        file_id_set = set(file_ids or [])
        skill_id_set = set(skill_ids or [])

        # Fetch memory-to-memory edges
        if memory_ids:
            for memory_id in memory_ids:
                try:
                    memory = await self.memory_repo.get_memory_by_id(
                        user_id=user_id,
                        memory_id=memory_id,
                    )
                    # Memory -> Memory links
                    for linked_id in memory.linked_memory_ids:
                        if linked_id in memory_id_set:
                            # Canonical edge ID for deduplication
                            min_id = min(memory_id, linked_id)
                            max_id = max(memory_id, linked_id)
                            edge_id = f"memory_{min_id}_memory_{max_id}"

                            if edge_id not in seen_edge_ids:
                                seen_edge_ids.add(edge_id)
                                edges.append(SubgraphEdge(
                                    id=edge_id,
                                    source=f"memory_{memory_id}",
                                    target=f"memory_{linked_id}",
                                    type="memory_link",
                                ))

                    # Memory -> Project links
                    for proj_id in memory.project_ids:
                        if proj_id in project_id_set:
                            edge_id = f"memory_{memory_id}_project_{proj_id}"
                            if edge_id not in seen_edge_ids:
                                seen_edge_ids.add(edge_id)
                                edges.append(SubgraphEdge(
                                    id=edge_id,
                                    source=f"memory_{memory_id}",
                                    target=f"project_{proj_id}",
                                    type="memory_project",
                                ))

                    # Memory -> Document links
                    for doc_id in memory.document_ids:
                        if doc_id in document_id_set:
                            edge_id = f"memory_{memory_id}_document_{doc_id}"
                            if edge_id not in seen_edge_ids:
                                seen_edge_ids.add(edge_id)
                                edges.append(SubgraphEdge(
                                    id=edge_id,
                                    source=f"memory_{memory_id}",
                                    target=f"document_{doc_id}",
                                    type="memory_document",
                                ))

                    # Memory -> Code Artifact links
                    for artifact_id in memory.code_artifact_ids:
                        if artifact_id in code_artifact_id_set:
                            edge_id = f"memory_{memory_id}_code_artifact_{artifact_id}"
                            if edge_id not in seen_edge_ids:
                                seen_edge_ids.add(edge_id)
                                edges.append(SubgraphEdge(
                                    id=edge_id,
                                    source=f"memory_{memory_id}",
                                    target=f"code_artifact_{artifact_id}",
                                    type="memory_code_artifact",
                                ))

                    # Memory -> File links
                    for fid in memory.file_ids:
                        if fid in file_id_set:
                            edge_id = f"memory_{memory_id}_file_{fid}"
                            if edge_id not in seen_edge_ids:
                                seen_edge_ids.add(edge_id)
                                edges.append(SubgraphEdge(
                                    id=edge_id,
                                    source=f"memory_{memory_id}",
                                    target=f"file_{fid}",
                                    type="memory_file",
                                ))

                    # Memory -> Skill links
                    for sid in memory.skill_ids:
                        if sid in skill_id_set:
                            edge_id = f"memory_{memory_id}_skill_{sid}"
                            if edge_id not in seen_edge_ids:
                                seen_edge_ids.add(edge_id)
                                edges.append(SubgraphEdge(
                                    id=edge_id,
                                    source=f"memory_{memory_id}",
                                    target=f"skill_{sid}",
                                    type="memory_skill",
                                ))

                except NotFoundError:
                    continue

        # Fetch entity-to-memory edges
        if entity_ids and memory_ids:
            entity_memory_links = await self.entity_repo.get_all_entity_memory_links(
                user_id=user_id,
            )
            for entity_id, mem_id in entity_memory_links:
                if entity_id in entity_id_set and mem_id in memory_id_set:
                    edge_id = f"entity_{entity_id}_memory_{mem_id}"
                    if edge_id not in seen_edge_ids:
                        seen_edge_ids.add(edge_id)
                        edges.append(SubgraphEdge(
                            id=edge_id,
                            source=f"entity_{entity_id}",
                            target=f"memory_{mem_id}",
                            type="entity_memory",
                        ))

        # Fetch entity-to-entity edges
        if entity_ids:
            entity_relationships = await self.entity_repo.get_all_entity_relationships(
                user_id=user_id,
            )
            for rel in entity_relationships:
                if rel.source_entity_id in entity_id_set and rel.target_entity_id in entity_id_set:
                    # Canonical edge ID for deduplication: a pair may hold several relationship
                    # types, so only the same type in the opposite direction is a duplicate
                    min_id = min(rel.source_entity_id, rel.target_entity_id)
                    max_id = max(rel.source_entity_id, rel.target_entity_id)
                    edge_id = f"entity_{min_id}_entity_{max_id}_{rel.relationship_type}"

                    if edge_id not in seen_edge_ids:
                        seen_edge_ids.add(edge_id)
                        edges.append(SubgraphEdge(
                            id=edge_id,
                            source=f"entity_{rel.source_entity_id}",
                            target=f"entity_{rel.target_entity_id}",
                            type="entity_relationship",
                            data={
                                "relationship_type": rel.relationship_type,
                                "strength": rel.strength,
                                "confidence": rel.confidence,
                                "metadata": rel.metadata,
                            },
                        ))

        # Fetch entity-to-project edges
        if entity_ids and project_ids:
            entity_project_links = await self.entity_repo.get_all_entity_project_links(
                user_id=user_id,
            )
            for entity_id, proj_id in entity_project_links:
                if entity_id in entity_id_set and proj_id in project_id_set:
                    edge_id = f"entity_{entity_id}_project_{proj_id}"
                    if edge_id not in seen_edge_ids:
                        seen_edge_ids.add(edge_id)
                        edges.append(SubgraphEdge(
                            id=edge_id,
                            source=f"entity_{entity_id}",
                            target=f"project_{proj_id}",
                            type="entity_project",
                        ))

        # Fetch document-to-project edges
        if self.document_service and document_ids and project_ids:
            for document_id in document_ids:
                try:
                    document = await self.document_service.get_document(
                        user_id=user_id,
                        document_id=document_id,
                    )
                    if document and document.project_id and document.project_id in project_id_set:
                        edge_id = f"document_{document_id}_project_{document.project_id}"
                        if edge_id not in seen_edge_ids:
                            seen_edge_ids.add(edge_id)
                            edges.append(SubgraphEdge(
                                id=edge_id,
                                source=f"document_{document_id}",
                                target=f"project_{document.project_id}",
                                type="document_project",
                            ))
                except NotFoundError:
                    continue

        # Fetch code_artifact-to-project edges
        if self.code_artifact_service and code_artifact_ids and project_ids:
            for artifact_id in code_artifact_ids:
                try:
                    artifact = await self.code_artifact_service.get_code_artifact(
                        user_id=user_id,
                        artifact_id=artifact_id,
                    )
                    if artifact and artifact.project_id and artifact.project_id in project_id_set:
                        edge_id = f"code_artifact_{artifact_id}_project_{artifact.project_id}"
                        if edge_id not in seen_edge_ids:
                            seen_edge_ids.add(edge_id)
                            edges.append(SubgraphEdge(
                                id=edge_id,
                                source=f"code_artifact_{artifact_id}",
                                target=f"project_{artifact.project_id}",
                                type="code_artifact_project",
                            ))
                except NotFoundError:
                    continue

        # Fetch file-to-project edges
        if self.file_service and file_ids and project_ids:
            try:
                file_summaries = await self.file_service.list_files(user_id=user_id)
                for fs in file_summaries:
                    if fs.id in file_id_set and fs.project_id and fs.project_id in project_id_set:
                        edge_id = f"file_{fs.id}_project_{fs.project_id}"
                        if edge_id not in seen_edge_ids:
                            seen_edge_ids.add(edge_id)
                            edges.append(SubgraphEdge(
                                id=edge_id,
                                source=f"file_{fs.id}",
                                target=f"project_{fs.project_id}",
                                type="file_project",
                            ))
            except Exception:
                logger.warning("Failed to fetch file-project edges")

        # Fetch entity-to-file edges
        if entity_ids and file_ids:
            entity_file_links = await self.entity_repo.get_all_entity_file_links(
                user_id=user_id,
            )
            for entity_id, fid in entity_file_links:
                if entity_id in entity_id_set and fid in file_id_set:
                    edge_id = f"entity_{entity_id}_file_{fid}"
                    if edge_id not in seen_edge_ids:
                        seen_edge_ids.add(edge_id)
                        edges.append(SubgraphEdge(
                            id=edge_id,
                            source=f"entity_{entity_id}",
                            target=f"file_{fid}",
                            type="entity_file",
                        ))

        # Fetch skill-to-project edges
        if self.skill_service and skill_ids and project_ids:
            for sid in skill_ids:
                try:
                    skill = await self.skill_service.get_skill(
                        user_id=user_id,
                        skill_id=sid,
                    )
                    if skill and skill.project_id and skill.project_id in project_id_set:
                        edge_id = f"skill_{sid}_project_{skill.project_id}"
                        if edge_id not in seen_edge_ids:
                            seen_edge_ids.add(edge_id)
                            edges.append(SubgraphEdge(
                                id=edge_id,
                                source=f"skill_{sid}",
                                target=f"project_{skill.project_id}",
                                type="skill_project",
                            ))
                except NotFoundError:
                    continue

        # Fetch skill-to-file edges
        if self.skill_service and skill_ids and file_ids:
            skill_file_links = await self.skill_service.get_all_skill_file_links(
                user_id=user_id,
            )
            skill_id_set = set(skill_ids)
            for sid, fid in skill_file_links:
                if sid in skill_id_set and fid in file_id_set:
                    edge_id = f"skill_{sid}_file_{fid}"
                    if edge_id not in seen_edge_ids:
                        seen_edge_ids.add(edge_id)
                        edges.append(SubgraphEdge(
                            id=edge_id,
                            source=f"skill_{sid}",
                            target=f"file_{fid}",
                            type="skill_file",
                        ))

        # Fetch skill-to-code_artifact edges
        if self.skill_service and skill_ids and code_artifact_ids:
            skill_artifact_links = await self.skill_service.get_all_skill_code_artifact_links(
                user_id=user_id,
            )
            skill_id_set = set(skill_ids)
            code_artifact_id_set = set(code_artifact_ids)
            for sid, aid in skill_artifact_links:
                if sid in skill_id_set and aid in code_artifact_id_set:
                    edge_id = f"skill_{sid}_code_artifact_{aid}"
                    if edge_id not in seen_edge_ids:
                        seen_edge_ids.add(edge_id)
                        edges.append(SubgraphEdge(
                            id=edge_id,
                            source=f"skill_{sid}",
                            target=f"code_artifact_{aid}",
                            type="skill_code_artifact",
                        ))

        # Fetch skill-to-document edges
        if self.skill_service and skill_ids and document_ids:
            skill_doc_links = await self.skill_service.get_all_skill_document_links(
                user_id=user_id,
            )
            skill_id_set = set(skill_ids)
            document_id_set = set(document_ids)
            for sid, did in skill_doc_links:
                if sid in skill_id_set and did in document_id_set:
                    edge_id = f"skill_{sid}_document_{did}"
                    if edge_id not in seen_edge_ids:
                        seen_edge_ids.add(edge_id)
                        edges.append(SubgraphEdge(
                            id=edge_id,
                            source=f"skill_{sid}",
                            target=f"document_{did}",
                            type="skill_document",
                        ))

        plan_id_set = set(plan_ids or [])
        task_id_set = set(task_ids or [])

        # Fetch plan-to-project edges
        if self.plan_service and plan_ids and project_ids:
            for pid in plan_ids:
                try:
                    plan = await self.plan_service.get_plan(
                        user_id=user_id,
                        plan_id=pid,
                    )
                    if plan and plan.project_id and plan.project_id in project_id_set:
                        edge_id = f"plan_{pid}_project_{plan.project_id}"
                        if edge_id not in seen_edge_ids:
                            seen_edge_ids.add(edge_id)
                            edges.append(SubgraphEdge(
                                id=edge_id,
                                source=f"plan_{pid}",
                                target=f"project_{plan.project_id}",
                                type="plan_project",
                            ))
                except NotFoundError:
                    continue

        # Fetch plan-to-task edges (using pre-fetched task_summaries)
        if plan_ids and task_ids and task_summaries:
            for t in task_summaries:
                if t.id in task_id_set and t.plan_id in plan_id_set:
                    edge_id = f"plan_{t.plan_id}_task_{t.id}"
                    if edge_id not in seen_edge_ids:
                        seen_edge_ids.add(edge_id)
                        edges.append(SubgraphEdge(
                            id=edge_id,
                            source=f"plan_{t.plan_id}",
                            target=f"task_{t.id}",
                            type="plan_task",
                        ))

        return edges
