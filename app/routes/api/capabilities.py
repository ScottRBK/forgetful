"""Public discovery of the instance's enabled optional features and field limits."""

from functools import cache

from fastmcp import FastMCP
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config.settings import settings
from app.models.code_artifact_models import CodeArtifactCreate
from app.models.document_models import DocumentCreate
from app.models.entity_models import EntityCreate, EntityRelationshipCreate
from app.models.file_models import FileCreate
from app.models.memory_models import MemoryCreate
from app.models.plan_models import CriterionCreate, PlanCreate, TaskCreate
from app.models.project_models import ProjectCreate
from app.models.skill_models import SkillCreate

CORE_MODELS: dict[str, type[BaseModel]] = {
    "memory": MemoryCreate,
    "entity": EntityCreate,
    "entity_relationship": EntityRelationshipCreate,
    "document": DocumentCreate,
    "code_artifact": CodeArtifactCreate,
    "project": ProjectCreate,
}
PLANNING_MODELS: dict[str, type[BaseModel]] = {
    "plan": PlanCreate,
    "task": TaskCreate,
    "criterion": CriterionCreate,
}
SCHEMA_BOUNDS = (("maxLength", "max_length"), ("maxItems", "max_items"))


@cache
def field_limits(model: type[BaseModel]) -> dict[str, dict[str, int]]:
    """Length and count bounds that the model enforces; nothing else from its schema.

    Bounds are fixed when the model is imported, so a configured limit is published as soon
    as the server starts. Optional fields keep their bounds inside ``anyOf``.
    """
    limits: dict[str, dict[str, int]] = {}
    properties = model.model_json_schema(mode="validation").get("properties", {})
    for name, schema in properties.items():
        for option in (schema, *schema.get("anyOf", [])):
            bound = {key: option[source] for source, key in SCHEMA_BOUNDS if source in option}
            if bound:
                limits[name] = bound
                break
    return limits


def published_limits() -> dict[str, dict[str, dict[str, int]]]:
    """Field limits for the core types and each enabled optional feature."""
    limits = {group: field_limits(model) for group, model in CORE_MODELS.items()}
    if settings.PLANNING_ENABLED:
        limits.update({group: field_limits(model) for group, model in PLANNING_MODELS.items()})
    if settings.FILES_ENABLED:
        limits["file"] = {
            **field_limits(FileCreate),
            "data": {"max_decoded_bytes": settings.FILE_MAX_SIZE_BYTES},
        }
    if settings.SKILLS_ENABLED:
        limits["skill"] = field_limits(SkillCreate)
        limits["skill_bundle"] = {
            "resources": {"max_items": settings.SKILL_BUNDLE_MAX_RESOURCES},
            "content": {"max_decoded_bytes": settings.SKILL_BUNDLE_MAX_BYTES},
        }
    return limits


def register(mcp: FastMCP):
    """Register capability discovery independently of feature flags and authentication."""

    @mcp.custom_route("/.well-known", methods=["GET"])
    async def get_capabilities(request: Request) -> JSONResponse:
        """Report settings and field limits; do not resolve a user or access domain services."""
        return JSONResponse({
            "schema_version": 1,
            "capabilities": {
                "planning": settings.PLANNING_ENABLED,
                "skills": settings.SKILLS_ENABLED,
                "files": settings.FILES_ENABLED,
                "ui": settings.UI_ENABLED,
                "activity_stream": settings.ACTIVITY_ENABLED,
            },
            "limits": published_limits(),
        })
