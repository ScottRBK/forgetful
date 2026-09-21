"""REST API endpoints for Graph visualization.

Phase 4 of the Web UI foundation (Issue #3).
Provides graph data (nodes and edges) for visualization UI.
"""
import logging
from typing import Any

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config.settings import settings
from app.exceptions import NotFoundError
from app.middleware.auth import get_user_from_request

logger = logging.getLogger(__name__)


def register(mcp: FastMCP):
    """Register graph REST routes with FastMCP"""
    # Constants for valid node types
    ALL_NODE_TYPES = {"memory", "entity", "project", "document", "code_artifact", "file", "skill", "plan", "task"}

    # Map node type to (service attr, feature flag name) for feature-flag checks.
    # Types not listed here are always available (memory/entity/project/etc.).
    FLAG_GATED_TYPES = {
        "file": ("file_service", "FILES_ENABLED"),
        "skill": ("skill_service", "SKILLS_ENABLED"),
        "plan": ("plan_service", "PLANNING_ENABLED"),
        "task": ("task_service", "PLANNING_ENABLED"),
    }

    def _resolve_available_node_types() -> set[str]:
        """Return the set of node types available given current feature flags."""
        available = set(ALL_NODE_TYPES)
        for node_type, (service_attr, _flag_name) in FLAG_GATED_TYPES.items():
            if getattr(mcp, service_attr, None) is None:
                available.discard(node_type)
        return available

    @mcp.custom_route("/api/v1/graph", methods=["GET"])
    async def get_graph(request: Request) -> JSONResponse:
        """Get graph data for visualization.

        Returns nodes (memories, entities, projects, documents, code_artifacts) and edges.

        Query params:
            project_id: Filter memories to specific project (optional)
            node_types: Comma-separated list of node types to include
                       (default: memory,entity,project,document,code_artifact)
            include_entities: Legacy param, deprecated in favor of node_types
            limit: Max memories to include (default 100, max configurable via
                   MAX_GRAPH_LIMIT setting / env var, defaults to 2000)
            offset: Number of memories to skip for pagination (default 0)
            sort_by: Sort field - created_at, updated_at, importance (default created_at)
            sort_order: Sort direction - asc, desc (default desc)
        """
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        params = request.query_params
        project_id_str = params.get("project_id")
        limit_str = params.get("limit", "100")
        offset_str = params.get("offset", "0")
        sort_by = params.get("sort_by", "created_at")
        sort_order = params.get("sort_order", "desc")

        # Parse node_types parameter (new approach)
        available_types = _resolve_available_node_types()
        node_types_str = params.get("node_types")
        if node_types_str:
            # node_types takes precedence over include_entities
            requested_types = {t.strip() for t in node_types_str.split(",") if t.strip()}
            invalid_types = requested_types - ALL_NODE_TYPES
            if invalid_types:
                return JSONResponse(
                    {"error": f"Invalid node_types: {invalid_types}. Valid values: {', '.join(sorted(ALL_NODE_TYPES))}"},
                    status_code=400,
                )
            disabled_types = requested_types - available_types
            if disabled_types:
                disabled_flags = sorted({
                    FLAG_GATED_TYPES[t][1] for t in disabled_types if t in FLAG_GATED_TYPES
                })
                return JSONResponse(
                    {"error": f"Node type(s) {sorted(disabled_types)} are disabled. Enable {', '.join(disabled_flags)} to use."},
                    status_code=400,
                )
            include_memories = "memory" in requested_types
            include_entities = "entity" in requested_types
            include_projects = "project" in requested_types
            include_documents = "document" in requested_types
            include_code_artifacts = "code_artifact" in requested_types
            include_files = "file" in requested_types
            include_skills = "skill" in requested_types
            include_plans = "plan" in requested_types
            include_tasks = "task" in requested_types
        else:
            # Fallback to legacy include_entities param; default to ALL available types
            include_entities_str = params.get("include_entities", "true").lower()
            include_memories = True
            include_entities = include_entities_str == "true"
            include_projects = True
            include_documents = True
            include_code_artifacts = True
            include_files = "file" in available_types
            include_skills = "skill" in available_types
            include_plans = "plan" in available_types
            include_tasks = "task" in available_types

        # Validate limit parameter (cap at configurable MAX_GRAPH_LIMIT, see issue #23)
        try:
            limit = min(int(limit_str), settings.MAX_GRAPH_LIMIT)
        except ValueError:
            return JSONResponse(
                {"error": f"Invalid limit: {limit_str}. Must be an integer."},
                status_code=400,
            )

        # Validate offset parameter
        try:
            offset = int(offset_str)
            if offset < 0:
                return JSONResponse(
                    {"error": "offset must be non-negative"},
                    status_code=400,
                )
        except ValueError:
            return JSONResponse(
                {"error": f"Invalid offset: {offset_str}. Must be an integer."},
                status_code=400,
            )

        # Validate sort_by parameter
        VALID_SORT_BY = {"created_at", "updated_at", "importance"}
        if sort_by not in VALID_SORT_BY:
            return JSONResponse(
                {"error": f"sort_by must be one of: {', '.join(sorted(VALID_SORT_BY))}"},
                status_code=400,
            )

        # Validate sort_order parameter
        VALID_SORT_ORDER = {"asc", "desc"}
        if sort_order not in VALID_SORT_ORDER:
            return JSONResponse(
                {"error": f"sort_order must be one of: {', '.join(sorted(VALID_SORT_ORDER))}"},
                status_code=400,
            )

        # Validate project_id parameter
        project_ids = None
        if project_id_str:
            try:
                project_ids = [int(project_id_str)]
            except ValueError:
                return JSONResponse(
                    {"error": f"Invalid project_id: {project_id_str}. Must be an integer."},
                    status_code=400,
                )

        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        seen_memory_ids = set()
        seen_edge_ids = set()
        seen_project_ids = set()
        seen_document_ids = set()
        seen_code_artifact_ids = set()
        seen_file_ids = set()
        seen_skill_ids = set()
        seen_plan_ids = set()
        seen_task_ids = set()
        memories = []  # Store for edge building

        # Get memories with pagination
        total_memory_count = 0
        if include_memories:
            memories, total_memory_count = await mcp.memory_service.list_memories(
                user_id=user.id,
                limit=limit,
                offset=offset,
                project_ids=project_ids,
                sort_by=sort_by,
                sort_order=sort_order,
            )

            # Add memory nodes
            for memory in memories:
                seen_memory_ids.add(memory.id)
                nodes.append({
                    "id": f"memory_{memory.id}",
                    "type": "memory",
                    "label": memory.title,
                    "data": {
                        "id": memory.id,
                        "title": memory.title,
                        "importance": memory.importance,
                        "tags": memory.tags,
                        "created_at": memory.created_at.isoformat() if memory.created_at else None,
                    },
                })

            # Add edges for memory links
            for memory in memories:
                for linked_id in memory.linked_memory_ids:
                    if linked_id in seen_memory_ids:
                        edge_id = f"memory_{min(memory.id, linked_id)}_memory_{max(memory.id, linked_id)}"
                        if edge_id not in seen_edge_ids:
                            seen_edge_ids.add(edge_id)
                            edges.append({
                                "id": edge_id,
                                "source": f"memory_{memory.id}",
                                "target": f"memory_{linked_id}",
                                "type": "memory_link",
                            })

        # Add entity nodes and edges if requested
        seen_entity_ids = set()
        if include_entities:
            # Get all entities (no pagination limit for graph visualization)
            entities, _ = await mcp.entity_service.list_entities(
                user_id=user.id,
                limit=10000,  # High limit to get all entities for graph
            )

            for entity in entities:
                seen_entity_ids.add(entity.id)
                nodes.append({
                    "id": f"entity_{entity.id}",
                    "type": "entity",
                    "label": entity.name,
                    "data": {
                        "id": entity.id,
                        "name": entity.name,
                        "entity_type": entity.entity_type,
                        "created_at": entity.created_at.isoformat() if entity.created_at else None,
                    },
                })

            # Add entity-relationship edges (with deduplication for bidirectional display)
            entity_relationships = await mcp.entity_service.get_all_entity_relationships(
                user_id=user.id,
            )

            for rel in entity_relationships:
                # Only add edge if both entities are in result set
                if rel.source_entity_id in seen_entity_ids and rel.target_entity_id in seen_entity_ids:
                    # Canonical edge ID for deduplication (bidirectional visualization)
                    min_id = min(rel.source_entity_id, rel.target_entity_id)
                    max_id = max(rel.source_entity_id, rel.target_entity_id)
                    edge_id = f"entity_{min_id}_entity_{max_id}"

                    if edge_id not in seen_edge_ids:
                        seen_edge_ids.add(edge_id)
                        edges.append({
                            "id": edge_id,
                            "source": f"entity_{rel.source_entity_id}",
                            "target": f"entity_{rel.target_entity_id}",
                            "type": "entity_relationship",
                            "data": {
                                "relationship_type": rel.relationship_type,
                                "strength": rel.strength,
                                "confidence": rel.confidence,
                                "metadata": rel.metadata,
                            },
                        })

            # Add entity-memory edges
            entity_memory_links = await mcp.entity_service.get_all_entity_memory_links(
                user_id=user.id,
            )

            for entity_id, mem_id in entity_memory_links:
                # Only add edge if both entity and memory are in result set
                if entity_id in seen_entity_ids and mem_id in seen_memory_ids:
                    # Entity always first for consistent edge ID format
                    edge_id = f"entity_{entity_id}_memory_{mem_id}"

                    if edge_id not in seen_edge_ids:
                        seen_edge_ids.add(edge_id)
                        edges.append({
                            "id": edge_id,
                            "source": f"entity_{entity_id}",
                            "target": f"memory_{mem_id}",
                            "type": "entity_memory",
                        })

        # Add project nodes
        projects = []
        if include_projects:
            projects = await mcp.project_service.list_projects(
                user_id=user.id,
            )

            for project in projects:
                seen_project_ids.add(project.id)
                nodes.append({
                    "id": f"project_{project.id}",
                    "type": "project",
                    "label": project.name,
                    "data": {
                        "id": project.id,
                        "name": project.name,
                        "project_type": project.project_type.value if hasattr(project.project_type, "value") else project.project_type,
                        "status": project.status.value if hasattr(project.status, "value") else project.status,
                        "created_at": project.created_at.isoformat() if project.created_at else None,
                    },
                })

        # Add document nodes
        documents = []
        if include_documents:
            documents = await mcp.document_service.list_documents(
                user_id=user.id,
            )

            for document in documents:
                seen_document_ids.add(document.id)
                nodes.append({
                    "id": f"document_{document.id}",
                    "type": "document",
                    "label": document.title,
                    "data": {
                        "id": document.id,
                        "title": document.title,
                        "description": document.description,
                        "document_type": document.document_type,
                        "tags": document.tags,
                        "created_at": document.created_at.isoformat() if document.created_at else None,
                    },
                })

        # Add code artifact nodes
        code_artifacts = []
        if include_code_artifacts:
            code_artifacts = await mcp.code_artifact_service.list_code_artifacts(
                user_id=user.id,
            )

            for artifact in code_artifacts:
                seen_code_artifact_ids.add(artifact.id)
                nodes.append({
                    "id": f"code_artifact_{artifact.id}",
                    "type": "code_artifact",
                    "label": artifact.title,
                    "data": {
                        "id": artifact.id,
                        "title": artifact.title,
                        "description": artifact.description,
                        "language": artifact.language,
                        "tags": artifact.tags,
                        "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
                    },
                })

        # Add file nodes
        files = []
        if include_files and getattr(mcp, "file_service", None):
            files = await mcp.file_service.list_files(
                user_id=user.id,
            )

            for file_summary in files:
                seen_file_ids.add(file_summary.id)
                nodes.append({
                    "id": f"file_{file_summary.id}",
                    "type": "file",
                    "label": file_summary.filename,
                    "data": {
                        "id": file_summary.id,
                        "filename": file_summary.filename,
                        "description": file_summary.description,
                        "mime_type": file_summary.mime_type,
                        "size_bytes": file_summary.size_bytes,
                        "tags": file_summary.tags,
                        "project_id": file_summary.project_id,
                        "created_at": file_summary.created_at.isoformat() if file_summary.created_at else None,
                    },
                })

        # Add skill nodes
        skills = []
        if include_skills and getattr(mcp, "skill_service", None):
            skills = await mcp.skill_service.list_skills(
                user_id=user.id,
            )

            for skill_summary in skills:
                seen_skill_ids.add(skill_summary.id)
                nodes.append({
                    "id": f"skill_{skill_summary.id}",
                    "type": "skill",
                    "label": skill_summary.name,
                    "data": {
                        "id": skill_summary.id,
                        "name": skill_summary.name,
                        "description": skill_summary.description,
                        "tags": skill_summary.tags,
                        "importance": skill_summary.importance,
                        "project_id": skill_summary.project_id,
                        "created_at": skill_summary.created_at.isoformat() if skill_summary.created_at else None,
                    },
                })

        # Add plan nodes
        plans = []
        if include_plans and getattr(mcp, "plan_service", None):
            plans = await mcp.plan_service.list_plans(user_id=user.id)
            for plan_summary in plans:
                seen_plan_ids.add(plan_summary.id)
                nodes.append({
                    "id": f"plan_{plan_summary.id}",
                    "type": "plan",
                    "label": plan_summary.title,
                    "data": {
                        "id": plan_summary.id,
                        "title": plan_summary.title,
                        "status": plan_summary.status.value if hasattr(plan_summary.status, "value") else plan_summary.status,
                        "project_id": plan_summary.project_id,
                        "task_count": plan_summary.task_count,
                        "created_at": plan_summary.created_at.isoformat() if plan_summary.created_at else None,
                        "updated_at": plan_summary.updated_at.isoformat() if plan_summary.updated_at else None,
                    },
                })

        # Add task nodes
        tasks = []
        if include_tasks and getattr(mcp, "task_service", None):
            # When plans are also requested, scope tasks to those plans (one query). Otherwise fetch all.
            task_filter = sorted(seen_plan_ids) if include_plans else None
            tasks = await mcp.task_service.list_tasks_for_user(
                user_id=user.id, plan_ids=task_filter,
            )
            for task_summary in tasks:
                seen_task_ids.add(task_summary.id)
                nodes.append({
                    "id": f"task_{task_summary.id}",
                    "type": "task",
                    "label": task_summary.title,
                    "data": {
                        "id": task_summary.id,
                        "title": task_summary.title,
                        "plan_id": task_summary.plan_id,
                        "state": task_summary.state.value if hasattr(task_summary.state, "value") else task_summary.state,
                        "priority": task_summary.priority.value if hasattr(task_summary.priority, "value") else task_summary.priority,
                        "assigned_agent": task_summary.assigned_agent,
                        "criteria_met": task_summary.criteria_met,
                        "criteria_total": task_summary.criteria_total,
                        "blocked": task_summary.blocked,
                        "created_at": task_summary.created_at.isoformat() if task_summary.created_at else None,
                        "updated_at": task_summary.updated_at.isoformat() if task_summary.updated_at else None,
                    },
                })

        # Add memory-project edges (from memory.project_ids)
        if include_memories and include_projects:
            for memory in memories:
                for proj_id in (memory.project_ids or []):
                    if proj_id in seen_project_ids:
                        edge_id = f"memory_{memory.id}_project_{proj_id}"
                        if edge_id not in seen_edge_ids:
                            seen_edge_ids.add(edge_id)
                            edges.append({
                                "id": edge_id,
                                "source": f"memory_{memory.id}",
                                "target": f"project_{proj_id}",
                                "type": "memory_project",
                            })

        # Add document-project edges (from document.project_id)
        if include_documents and include_projects:
            for document in documents:
                if document.project_id and document.project_id in seen_project_ids:
                    edge_id = f"document_{document.id}_project_{document.project_id}"
                    if edge_id not in seen_edge_ids:
                        seen_edge_ids.add(edge_id)
                        edges.append({
                            "id": edge_id,
                            "source": f"document_{document.id}",
                            "target": f"project_{document.project_id}",
                            "type": "document_project",
                        })

        # Add code_artifact-project edges (from artifact.project_id)
        if include_code_artifacts and include_projects:
            for artifact in code_artifacts:
                if artifact.project_id and artifact.project_id in seen_project_ids:
                    edge_id = f"code_artifact_{artifact.id}_project_{artifact.project_id}"
                    if edge_id not in seen_edge_ids:
                        seen_edge_ids.add(edge_id)
                        edges.append({
                            "id": edge_id,
                            "source": f"code_artifact_{artifact.id}",
                            "target": f"project_{artifact.project_id}",
                            "type": "code_artifact_project",
                        })

        # Add entity-project edges (from entity_project_association)
        if include_entities and include_projects:
            entity_project_links = await mcp.entity_service.get_all_entity_project_links(
                user_id=user.id,
            )
            for entity_id, proj_id in entity_project_links:
                if entity_id in seen_entity_ids and proj_id in seen_project_ids:
                    edge_id = f"entity_{entity_id}_project_{proj_id}"
                    if edge_id not in seen_edge_ids:
                        seen_edge_ids.add(edge_id)
                        edges.append({
                            "id": edge_id,
                            "source": f"entity_{entity_id}",
                            "target": f"project_{proj_id}",
                            "type": "entity_project",
                        })

        # Add memory-document edges (from memory.document_ids)
        if include_memories and include_documents:
            for memory in memories:
                for doc_id in (memory.document_ids or []):
                    if doc_id in seen_document_ids:
                        edge_id = f"memory_{memory.id}_document_{doc_id}"
                        if edge_id not in seen_edge_ids:
                            seen_edge_ids.add(edge_id)
                            edges.append({
                                "id": edge_id,
                                "source": f"memory_{memory.id}",
                                "target": f"document_{doc_id}",
                                "type": "memory_document",
                            })

        # Add memory-code_artifact edges (from memory.code_artifact_ids)
        if include_memories and include_code_artifacts:
            for memory in memories:
                for artifact_id in (memory.code_artifact_ids or []):
                    if artifact_id in seen_code_artifact_ids:
                        edge_id = f"memory_{memory.id}_code_artifact_{artifact_id}"
                        if edge_id not in seen_edge_ids:
                            seen_edge_ids.add(edge_id)
                            edges.append({
                                "id": edge_id,
                                "source": f"memory_{memory.id}",
                                "target": f"code_artifact_{artifact_id}",
                                "type": "memory_code_artifact",
                            })

        # Add memory-file edges (from memory.file_ids)
        if include_memories and include_files:
            for memory in memories:
                for fid in (memory.file_ids or []):
                    if fid in seen_file_ids:
                        edge_id = f"memory_{memory.id}_file_{fid}"
                        if edge_id not in seen_edge_ids:
                            seen_edge_ids.add(edge_id)
                            edges.append({
                                "id": edge_id,
                                "source": f"memory_{memory.id}",
                                "target": f"file_{fid}",
                                "type": "memory_file",
                            })

        # Add file-project edges (from file.project_id)
        if include_files and include_projects:
            for file_summary in files:
                if file_summary.project_id and file_summary.project_id in seen_project_ids:
                    edge_id = f"file_{file_summary.id}_project_{file_summary.project_id}"
                    if edge_id not in seen_edge_ids:
                        seen_edge_ids.add(edge_id)
                        edges.append({
                            "id": edge_id,
                            "source": f"file_{file_summary.id}",
                            "target": f"project_{file_summary.project_id}",
                            "type": "file_project",
                        })

        # Add entity-file edges (from entity_file_association)
        if include_entities and include_files:
            entity_file_links = await mcp.entity_service.get_all_entity_file_links(
                user_id=user.id,
            )
            for entity_id, fid in entity_file_links:
                if entity_id in seen_entity_ids and fid in seen_file_ids:
                    edge_id = f"entity_{entity_id}_file_{fid}"
                    if edge_id not in seen_edge_ids:
                        seen_edge_ids.add(edge_id)
                        edges.append({
                            "id": edge_id,
                            "source": f"entity_{entity_id}",
                            "target": f"file_{fid}",
                            "type": "entity_file",
                        })

        # Add memory-skill edges (from memory.skill_ids)
        if include_memories and include_skills:
            for memory in memories:
                for sid in (memory.skill_ids or []):
                    if sid in seen_skill_ids:
                        edge_id = f"memory_{memory.id}_skill_{sid}"
                        if edge_id not in seen_edge_ids:
                            seen_edge_ids.add(edge_id)
                            edges.append({
                                "id": edge_id,
                                "source": f"memory_{memory.id}",
                                "target": f"skill_{sid}",
                                "type": "memory_skill",
                            })

        # Add skill-project edges (from skill.project_id)
        if include_skills and include_projects:
            for skill_summary in skills:
                if skill_summary.project_id and skill_summary.project_id in seen_project_ids:
                    edge_id = f"skill_{skill_summary.id}_project_{skill_summary.project_id}"
                    if edge_id not in seen_edge_ids:
                        seen_edge_ids.add(edge_id)
                        edges.append({
                            "id": edge_id,
                            "source": f"skill_{skill_summary.id}",
                            "target": f"project_{skill_summary.project_id}",
                            "type": "skill_project",
                        })

        # Add skill-file edges (from skill_file_association)
        if include_skills and include_files and getattr(mcp, "skill_service", None):
            skill_file_links = await mcp.skill_service.get_all_skill_file_links(
                user_id=user.id,
            )
            for skill_id, fid in skill_file_links:
                if skill_id in seen_skill_ids and fid in seen_file_ids:
                    edge_id = f"skill_{skill_id}_file_{fid}"
                    if edge_id not in seen_edge_ids:
                        seen_edge_ids.add(edge_id)
                        edges.append({
                            "id": edge_id,
                            "source": f"skill_{skill_id}",
                            "target": f"file_{fid}",
                            "type": "skill_file",
                        })

        # Add skill-code_artifact edges (from skill_code_artifact_association)
        if include_skills and include_code_artifacts and getattr(mcp, "skill_service", None):
            skill_artifact_links = await mcp.skill_service.get_all_skill_code_artifact_links(
                user_id=user.id,
            )
            for skill_id, artifact_id in skill_artifact_links:
                if skill_id in seen_skill_ids and artifact_id in seen_code_artifact_ids:
                    edge_id = f"skill_{skill_id}_code_artifact_{artifact_id}"
                    if edge_id not in seen_edge_ids:
                        seen_edge_ids.add(edge_id)
                        edges.append({
                            "id": edge_id,
                            "source": f"skill_{skill_id}",
                            "target": f"code_artifact_{artifact_id}",
                            "type": "skill_code_artifact",
                        })

        # Add skill-document edges (from skill_document_association)
        if include_skills and include_documents and getattr(mcp, "skill_service", None):
            skill_doc_links = await mcp.skill_service.get_all_skill_document_links(
                user_id=user.id,
            )
            for skill_id, doc_id in skill_doc_links:
                if skill_id in seen_skill_ids and doc_id in seen_document_ids:
                    edge_id = f"skill_{skill_id}_document_{doc_id}"
                    if edge_id not in seen_edge_ids:
                        seen_edge_ids.add(edge_id)
                        edges.append({
                            "id": edge_id,
                            "source": f"skill_{skill_id}",
                            "target": f"document_{doc_id}",
                            "type": "skill_document",
                        })

        # Add plan-project edges (from plan.project_id)
        if include_plans and include_projects:
            for plan_summary in plans:
                if plan_summary.project_id and plan_summary.project_id in seen_project_ids:
                    edge_id = f"plan_{plan_summary.id}_project_{plan_summary.project_id}"
                    if edge_id not in seen_edge_ids:
                        seen_edge_ids.add(edge_id)
                        edges.append({
                            "id": edge_id,
                            "source": f"plan_{plan_summary.id}",
                            "target": f"project_{plan_summary.project_id}",
                            "type": "plan_project",
                        })

        # Add plan-task edges (from task.plan_id)
        if include_plans and include_tasks:
            for task_summary in tasks:
                if task_summary.plan_id in seen_plan_ids and task_summary.id in seen_task_ids:
                    edge_id = f"plan_{task_summary.plan_id}_task_{task_summary.id}"
                    if edge_id not in seen_edge_ids:
                        seen_edge_ids.add(edge_id)
                        edges.append({
                            "id": edge_id,
                            "source": f"plan_{task_summary.plan_id}",
                            "target": f"task_{task_summary.id}",
                            "type": "plan_task",
                        })

        # Count edges by type for meta
        memory_link_count = len([e for e in edges if e["type"] == "memory_link"])
        entity_relationship_count = len([e for e in edges if e["type"] == "entity_relationship"])
        entity_memory_count = len([e for e in edges if e["type"] == "entity_memory"])
        entity_project_count = len([e for e in edges if e["type"] == "entity_project"])
        memory_project_count = len([e for e in edges if e["type"] == "memory_project"])
        document_project_count = len([e for e in edges if e["type"] == "document_project"])
        code_artifact_project_count = len([e for e in edges if e["type"] == "code_artifact_project"])
        memory_document_count = len([e for e in edges if e["type"] == "memory_document"])
        memory_code_artifact_count = len([e for e in edges if e["type"] == "memory_code_artifact"])
        memory_file_count = len([e for e in edges if e["type"] == "memory_file"])
        file_project_count = len([e for e in edges if e["type"] == "file_project"])
        entity_file_count = len([e for e in edges if e["type"] == "entity_file"])
        memory_skill_count = len([e for e in edges if e["type"] == "memory_skill"])
        skill_project_count = len([e for e in edges if e["type"] == "skill_project"])
        skill_file_count = len([e for e in edges if e["type"] == "skill_file"])
        skill_code_artifact_count = len([e for e in edges if e["type"] == "skill_code_artifact"])
        skill_document_count = len([e for e in edges if e["type"] == "skill_document"])
        plan_project_count = len([e for e in edges if e["type"] == "plan_project"])
        plan_task_count = len([e for e in edges if e["type"] == "plan_task"])

        # Calculate memory count for pagination metadata
        memory_count = len([n for n in nodes if n["type"] == "memory"])

        return JSONResponse({
            "nodes": nodes,
            "edges": edges,
            "meta": {
                "memory_count": memory_count,
                "total_memory_count": total_memory_count,
                "offset": offset,
                "limit": limit,
                "has_more": offset + memory_count < total_memory_count,
                "entity_count": len([n for n in nodes if n["type"] == "entity"]),
                "project_count": len([n for n in nodes if n["type"] == "project"]),
                "document_count": len([n for n in nodes if n["type"] == "document"]),
                "code_artifact_count": len([n for n in nodes if n["type"] == "code_artifact"]),
                "file_count": len([n for n in nodes if n["type"] == "file"]),
                "skill_count": len([n for n in nodes if n["type"] == "skill"]),
                "edge_count": len(edges),
                "memory_link_count": memory_link_count,
                "entity_relationship_count": entity_relationship_count,
                "entity_memory_count": entity_memory_count,
                "entity_project_count": entity_project_count,
                "memory_project_count": memory_project_count,
                "document_project_count": document_project_count,
                "code_artifact_project_count": code_artifact_project_count,
                "memory_document_count": memory_document_count,
                "memory_code_artifact_count": memory_code_artifact_count,
                "memory_file_count": memory_file_count,
                "file_project_count": file_project_count,
                "entity_file_count": entity_file_count,
                "memory_skill_count": memory_skill_count,
                "skill_project_count": skill_project_count,
                "skill_file_count": skill_file_count,
                "skill_code_artifact_count": skill_code_artifact_count,
                "skill_document_count": skill_document_count,
                "plan_count": len([n for n in nodes if n["type"] == "plan"]),
                "task_count": len([n for n in nodes if n["type"] == "task"]),
                "plan_project_count": plan_project_count,
                "plan_task_count": plan_task_count,
            },
        })

    @mcp.custom_route("/api/v1/graph/memory/{memory_id}", methods=["GET"])
    async def get_memory_subgraph(request: Request) -> JSONResponse:
        """Get subgraph centered on a specific memory.

        Returns the memory, its linked memories, and related entities.

        Query params:
            depth: Link traversal depth (1-3, default 1)
        """
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        # Validate memory_id path parameter
        try:
            memory_id = int(request.path_params["memory_id"])
        except ValueError:
            return JSONResponse(
                {"error": f"Invalid memory_id: {request.path_params['memory_id']}. Must be an integer."},
                status_code=400,
            )

        params = request.query_params
        depth_str = params.get("depth", "1")

        # Validate depth parameter
        try:
            depth = min(int(depth_str), 3)
        except ValueError:
            return JSONResponse(
                {"error": f"Invalid depth: {depth_str}. Must be an integer."},
                status_code=400,
            )

        # Get center memory
        try:
            center_memory = await mcp.memory_service.get_memory(
                user_id=user.id,
                memory_id=memory_id,
            )
        except NotFoundError:
            return JSONResponse({"error": "Memory not found"}, status_code=404)

        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        seen_memory_ids = set()

        async def add_memory_node(memory, level: int):
            if memory.id in seen_memory_ids:
                return
            seen_memory_ids.add(memory.id)

            nodes.append({
                "id": f"memory_{memory.id}",
                "type": "memory",
                "label": memory.title,
                "level": level,
                "data": {
                    "id": memory.id,
                    "title": memory.title,
                    "importance": memory.importance,
                    "tags": memory.tags,
                    "created_at": memory.created_at.isoformat() if memory.created_at else None,
                },
            })

            # Recurse for linked memories if within depth
            if level < depth:
                for linked_id in memory.linked_memory_ids:
                    if linked_id not in seen_memory_ids:
                        linked_memory = await mcp.memory_service.get_memory(
                            user_id=user.id,
                            memory_id=linked_id,
                        )
                        if linked_memory:
                            await add_memory_node(linked_memory, level + 1)

                            # Add edge
                            edge_id = f"memory_{min(memory.id, linked_id)}_memory_{max(memory.id, linked_id)}"
                            edges.append({
                                "id": edge_id,
                                "source": f"memory_{memory.id}",
                                "target": f"memory_{linked_id}",
                                "type": "memory_link",
                            })

        # Build subgraph starting from center
        await add_memory_node(center_memory, 0)

        # Add edges between already-seen memories
        seen_edge_ids = set()
        for memory_id_val in seen_memory_ids:
            memory = await mcp.memory_service.get_memory(
                user_id=user.id,
                memory_id=memory_id_val,
            )
            if memory:
                for linked_id in memory.linked_memory_ids:
                    if linked_id in seen_memory_ids:
                        edge_id = f"memory_{min(memory_id_val, linked_id)}_memory_{max(memory_id_val, linked_id)}"
                        if edge_id not in seen_edge_ids:
                            seen_edge_ids.add(edge_id)
                            edges.append({
                                "id": edge_id,
                                "source": f"memory_{memory_id_val}",
                                "target": f"memory_{linked_id}",
                                "type": "memory_link",
                            })

        # Add entities linked to memories in subgraph
        seen_entity_ids = set()
        entity_memory_links = await mcp.entity_service.get_all_entity_memory_links(
            user_id=user.id,
        )

        # Identify entities linked to subgraph memories
        relevant_entity_ids = set()
        for entity_id, mem_id in entity_memory_links:
            if mem_id in seen_memory_ids:
                relevant_entity_ids.add(entity_id)

        # Add entity nodes for relevant entities
        for entity_id in relevant_entity_ids:
            entity = await mcp.entity_service.get_entity(
                user_id=user.id,
                entity_id=entity_id,
            )
            if entity:
                seen_entity_ids.add(entity.id)
                nodes.append({
                    "id": f"entity_{entity.id}",
                    "type": "entity",
                    "label": entity.name,
                    "data": {
                        "id": entity.id,
                        "name": entity.name,
                        "entity_type": entity.entity_type.value if hasattr(entity.entity_type, "value") else entity.entity_type,
                        "created_at": entity.created_at.isoformat() if entity.created_at else None,
                    },
                })

        # Add entity-memory edges
        for entity_id, mem_id in entity_memory_links:
            if entity_id in seen_entity_ids and mem_id in seen_memory_ids:
                edge_id = f"entity_{entity_id}_memory_{mem_id}"
                if edge_id not in seen_edge_ids:
                    seen_edge_ids.add(edge_id)
                    edges.append({
                        "id": edge_id,
                        "source": f"entity_{entity_id}",
                        "target": f"memory_{mem_id}",
                        "type": "entity_memory",
                    })

        # Add entity-entity relationships for entities in subgraph
        entity_relationships = await mcp.entity_service.get_all_entity_relationships(
            user_id=user.id,
        )

        for rel in entity_relationships:
            if rel.source_entity_id in seen_entity_ids and rel.target_entity_id in seen_entity_ids:
                min_id = min(rel.source_entity_id, rel.target_entity_id)
                max_id = max(rel.source_entity_id, rel.target_entity_id)
                edge_id = f"entity_{min_id}_entity_{max_id}"

                if edge_id not in seen_edge_ids:
                    seen_edge_ids.add(edge_id)
                    edges.append({
                        "id": edge_id,
                        "source": f"entity_{rel.source_entity_id}",
                        "target": f"entity_{rel.target_entity_id}",
                        "type": "entity_relationship",
                        "data": {
                            "relationship_type": rel.relationship_type,
                            "strength": rel.strength,
                            "confidence": rel.confidence,
                            "metadata": rel.metadata,
                        },
                    })

        # Count by type
        memory_count = len([n for n in nodes if n["type"] == "memory"])
        entity_count = len([n for n in nodes if n["type"] == "entity"])
        memory_link_count = len([e for e in edges if e["type"] == "memory_link"])
        entity_relationship_count = len([e for e in edges if e["type"] == "entity_relationship"])
        entity_memory_count = len([e for e in edges if e["type"] == "entity_memory"])

        return JSONResponse({
            "nodes": nodes,
            "edges": edges,
            "center_memory_id": memory_id,
            "meta": {
                "memory_count": memory_count,
                "entity_count": entity_count,
                "edge_count": len(edges),
                "memory_link_count": memory_link_count,
                "entity_relationship_count": entity_relationship_count,
                "entity_memory_count": entity_memory_count,
                "depth": depth,
            },
        })

    @mcp.custom_route("/api/v1/graph/subgraph", methods=["GET"])
    async def get_subgraph(request: Request) -> JSONResponse:
        """Get subgraph centered on any node (memory or entity).

        Uses recursive CTE for efficient multi-hop traversal across all edge types.
        This is the recommended endpoint for graph visualization - replaces the
        older /graph/memory/{id} endpoint with better performance and entity support.

        Query params:
            node_id: Center node in format "memory_{id}", "entity_{id}", "project_{id}", "document_{id}", "code_artifact_{id}", "file_{id}", "skill_{id}", "plan_{id}", or "task_{id}" (required)
            depth: Traversal depth 1-3 (default 2)
            node_types: Comma-separated list of types to include (default: "memory,entity,project,document,code_artifact,file,skill,plan,task")
            max_nodes: Safety limit (default 200, max configurable via
                       MAX_GRAPH_LIMIT setting / env var, defaults to 2000)

        Returns:
            nodes: List with depth field on each node
            edges: All edges between returned nodes
            meta: Includes center_node_id and truncated flag
        """
        try:
            user = await get_user_from_request(request, mcp)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=401)

        params = request.query_params

        # Validate required node_id parameter
        node_id = params.get("node_id")
        if not node_id:
            return JSONResponse(
                {"error": "Missing required parameter: node_id. Format: 'memory_{id}', 'entity_{id}', 'project_{id}', 'document_{id}', 'code_artifact_{id}', 'file_{id}', 'skill_{id}', 'plan_{id}', or 'task_{id}'"},
                status_code=400,
            )

        # Validate depth parameter
        depth_str = params.get("depth", "2")
        try:
            depth = int(depth_str)
            if depth < 1:
                return JSONResponse(
                    {"error": f"Invalid depth: {depth}. Must be at least 1."},
                    status_code=400,
                )
        except ValueError:
            return JSONResponse(
                {"error": f"Invalid depth: {depth_str}. Must be an integer."},
                status_code=400,
            )

        # Parse node_types parameter — gated by feature flags
        available_types = _resolve_available_node_types()
        node_types_param = params.get("node_types")
        if node_types_param is None:
            # Default: every available type (silently omit disabled types)
            node_types = sorted(available_types)
        else:
            node_types = [t.strip() for t in node_types_param.split(",") if t.strip()]
            invalid_types = set(node_types) - ALL_NODE_TYPES
            if invalid_types:
                return JSONResponse(
                    {"error": f"Invalid node_types: {invalid_types}. Valid values: {', '.join(sorted(ALL_NODE_TYPES))}"},
                    status_code=400,
                )
            disabled_types = set(node_types) - available_types
            if disabled_types:
                disabled_flags = sorted({
                    FLAG_GATED_TYPES[t][1] for t in disabled_types if t in FLAG_GATED_TYPES
                })
                return JSONResponse(
                    {"error": f"Node type(s) {sorted(disabled_types)} are disabled. Enable {', '.join(disabled_flags)} to use."},
                    status_code=400,
                )
            if not node_types:
                node_types = sorted(available_types)

        # Validate max_nodes parameter
        max_nodes_str = params.get("max_nodes", "200")
        try:
            max_nodes = int(max_nodes_str)
        except ValueError:
            return JSONResponse(
                {"error": f"Invalid max_nodes: {max_nodes_str}. Must be an integer."},
                status_code=400,
            )

        # Call graph service
        try:
            result = await mcp.graph_service.get_subgraph(
                user_id=user.id,
                center_node_id=node_id,
                depth=depth,
                node_types=node_types,
                max_nodes=max_nodes,
            )
        except ValueError as e:
            # Invalid node_id format
            return JSONResponse({"error": str(e)}, status_code=400)
        except NotFoundError as e:
            return JSONResponse({"error": str(e)}, status_code=404)
        except Exception as e:
            # Log and return detailed error for debugging
            logger.exception(f"Subgraph query failed: {e}")
            return JSONResponse({"error": f"Internal error: {e!s}"}, status_code=500)

        # Convert Pydantic models to dicts for JSON response
        return JSONResponse({
            "nodes": [node.model_dump() for node in result.nodes],
            "edges": [edge.model_dump() for edge in result.edges],
            "meta": result.meta.model_dump(),
        })
