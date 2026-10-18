"""Models for Skills

Skills are what make up procedural memory and provide steps and examples
to allow an agent to perform a particular task. Implements a superset of
the Agent Skills open standard (agentskills.io).
"""

import re
from datetime import UTC, datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config.settings import settings
from app.models.storable import StorableInput


class SkillCreate(StorableInput):
    """Request model for creating a skill

    Skills are what make up procedural memory and provide steps and examples
    to allow an agent to perform a particular task.
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=settings.SKILL_NAME_MAX_LENGTH,
        description=(
            "Kebab-case skill name (e.g., 'pdf-processing')."
            " Must match ^[a-z0-9]+(-[a-z0-9]+)*$"
        ),
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=settings.SKILL_DESCRIPTION_MAX_LENGTH,
        description=(
            "What the skill does and when to use it."
            " Gets embedded for semantic search."
        ),
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=settings.SKILL_CONTENT_MAX_LENGTH,
        description="Full SKILL.md body (markdown instructions).",
    )
    license: str | None = Field(
        None,
        max_length=settings.SKILL_LICENSE_MAX_LENGTH,
        description="License identifier (e.g., 'MIT', 'Apache-2.0').",
    )
    compatibility: str | None = Field(
        None,
        max_length=settings.SKILL_COMPATIBILITY_MAX_LENGTH,
        description="Environment requirements (e.g., 'Requires Python 3.14+ and uv').",
    )
    allowed_tools: list[str] | None = Field(
        None,
        description="Tool restrictions (e.g., ['Bash(python:*)', 'Read', 'WebFetch']).",
    )
    metadata: dict | None = Field(
        None,
        description="Custom key-value pairs (author, version, mcp-server, etc.).",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Categorization tags.",
    )
    importance: int = Field(
        7,
        ge=1,
        le=10,
        description="Importance 1-10 (default 7).",
    )
    project_id: int | None = Field(
        None,
        description="Optional project association.",
    )

    # Provenance tracking fields (optional)
    source_repo: str | None = Field(default=None, max_length=200, description="Repository/project source (e.g., 'owner/repo')")
    source_files: list[str] | None = Field(default=None, description="Files that informed this (JSON list of paths)")
    source_url: str | None = Field(default=None, max_length=2048, description="URL to original source material")
    confidence: float | None = Field(default=None, ge=0.0, le=1.0, description="Encoding confidence score (0.0-1.0)")
    encoding_agent: str | None = Field(default=None, max_length=100, description="Software running the agent")
    encoding_version: str | None = Field(default=None, max_length=50, description="Version of encoding software")
    agent_id: str | None = Field(default=None, max_length=100, description="Agent identity")
    agent_version: str | None = Field(default=None, max_length=50, description="Agent version")
    agent_model: str | None = Field(default=None, max_length=100, description="LLM model used")

    @field_validator("source_files")
    @classmethod
    def validate_source_files(cls, v):
        if v is None:
            return None
        return [item.strip() for item in v if item.strip()]

    @field_validator("name")
    @classmethod
    def validate_name_kebab_case(cls, v):
        """Validate name follows kebab-case format per Agent Skills standard."""
        if v is None:
            return None

        stripped = v.strip()
        if not stripped:
            raise ValueError("name cannot be empty or whitespace only")

        pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
        if not re.match(pattern, stripped):
            raise ValueError(
                "name must be kebab-case (lowercase alphanumeric with hyphens, "
                "e.g., 'my-example-skill')",
            )

        return stripped

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        """Validate and clean tags."""
        if not v:
            return []

        cleaned = [tag.strip() for tag in v if tag and tag.strip()]

        if len(cleaned) > settings.SKILL_TAGS_MAX_COUNT:
            raise ValueError(f"Maximum {settings.SKILL_TAGS_MAX_COUNT} tags allowed")

        return cleaned


class SkillUpdate(StorableInput):
    """Request model for updating a skill.

    Follows PATCH semantics: only provided fields are updated.
    None/omitted values mean 'don't change this field'.
    """
    name: str | None = Field(None, min_length=1, max_length=settings.SKILL_NAME_MAX_LENGTH)
    description: str | None = Field(None, min_length=1, max_length=settings.SKILL_DESCRIPTION_MAX_LENGTH)
    content: str | None = Field(None, min_length=1, max_length=settings.SKILL_CONTENT_MAX_LENGTH)
    license: str | None = Field(None, max_length=settings.SKILL_LICENSE_MAX_LENGTH)
    compatibility: str | None = Field(None, max_length=settings.SKILL_COMPATIBILITY_MAX_LENGTH)
    allowed_tools: list[str] | None = Field(None)
    metadata: dict | None = Field(None)
    tags: list[str] | None = Field(None)
    importance: int | None = Field(None, ge=1, le=10)
    project_id: int | None = Field(None)

    # Provenance tracking fields (optional)
    source_repo: str | None = Field(default=None, max_length=200, description="New repository source. Unchanged if null.")
    source_files: list[str] | None = Field(default=None, description="New source files. Unchanged if null.")
    source_url: str | None = Field(default=None, max_length=2048, description="New source URL. Unchanged if null.")
    confidence: float | None = Field(default=None, ge=0.0, le=1.0, description="New confidence score. Unchanged if null.")
    encoding_agent: str | None = Field(default=None, max_length=100, description="New encoding agent. Unchanged if null.")
    encoding_version: str | None = Field(default=None, max_length=50, description="New encoding version. Unchanged if null.")
    agent_id: str | None = Field(default=None, max_length=100, description="New agent identity. Unchanged if null.")
    agent_version: str | None = Field(default=None, max_length=50, description="New agent version. Unchanged if null.")
    agent_model: str | None = Field(default=None, max_length=100, description="New LLM model. Unchanged if null.")

    @field_validator("source_files")
    @classmethod
    def validate_source_files(cls, v):
        if v is None:
            return None
        return [item.strip() for item in v if item.strip()]

    @field_validator("name")
    @classmethod
    def validate_name_kebab_case(cls, v):
        """Validate name follows kebab-case format per Agent Skills standard."""
        if v is None:
            return None

        stripped = v.strip()
        if not stripped:
            raise ValueError("name cannot be empty or whitespace only")

        pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
        if not re.match(pattern, stripped):
            raise ValueError(
                "name must be kebab-case (lowercase alphanumeric with hyphens, "
                "e.g., 'my-example-skill')",
            )

        return stripped

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        """Validate and clean tags."""
        if v is None:
            return None

        cleaned = [tag.strip() for tag in v if tag and tag.strip()]

        if len(cleaned) > settings.SKILL_TAGS_MAX_COUNT:
            raise ValueError(f"Maximum {settings.SKILL_TAGS_MAX_COUNT} tags allowed")

        return cleaned


class Skill(SkillCreate):
    """Complete Skill model with generated fields.

    Extends SkillCreate with system-generated fields (id and timestamps).
    Used for responses that include full Skill detail.
    """
    # Skills stored before NaN/NUL were refused (SQLite accepted them) stay readable
    enforce_storage_limits: ClassVar[bool] = False

    id: int = Field(..., description="Unique identifier (auto-generated)")
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC), frozen=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))

    model_config = ConfigDict(from_attributes=True)


class SkillSummary(BaseModel):
    """Lightweight skill summary for list views.

    Excludes content, allowed_tools, metadata, and compatibility
    to minimise context bloat.
    """
    id: int
    name: str
    description: str
    license: str | None
    tags: list[str]
    importance: int
    project_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SkillLinks(BaseModel):
    """IDs of all content linked to a skill (reverse lookup of the association tables)."""
    memory_ids: list[int] = Field(default_factory=list)
    file_ids: list[int] = Field(default_factory=list)
    code_artifact_ids: list[int] = Field(default_factory=list)
    document_ids: list[int] = Field(default_factory=list)
