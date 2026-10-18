"""Pydantic models for Code Artifact entities

Code artifacts store reusable code snippets, patterns, and implementations
that can be referenced by memories for documentation and knowledge sharing.
"""
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config.settings import settings
from app.models.patch_models import PatchModel


class CodeArtifactCreate(BaseModel):
    """Request model for creating a code artifact

    Code artifacts store code implementations, snippets, patterns, and examples
    with metadata for organization and retrieval. They can be linked to memories
    and projects for context.

    Examples:
        JWT middleware: title="FastAPI JWT Middleware", language="python", code="@app.middleware..."
        SQL query: title="User Activity Report Query", language="sql", code="SELECT..."
        React hook: title="useDebounce Hook", language="typescript", code="export function useDebounce..."
    """
    title: str = Field(
        ...,
        min_length=1,
        max_length=settings.CODE_ARTIFACT_TITLE_MAX_LENGTH,
        description="Artifact title - searchable identifier (e.g., 'FastAPI JWT middleware', 'useDebounce hook')",
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=settings.CODE_ARTIFACT_DESCRIPTION_MAX_LENGTH,
        description="Purpose and use case. What does this code do? When should it be used?",
    )
    code: str = Field(
        ...,
        min_length=1,
        max_length=settings.CODE_ARTIFACT_CODE_MAX_LENGTH,
        description="Complete code snippet or implementation",
    )
    language: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Programming language. Use full names not abbreviations (e.g., 'python' not 'py', 'javascript' not 'js', 'typescript' not 'ts'). Will be stored as lowercase.",
    )
    tags: list[str] = Field(
        default_factory=list,
        max_length=settings.CODE_ARTIFACT_TAGS_MAX_COUNT,
        description="Tags for categorization and discovery (e.g., ['auth', 'fastapi', 'middleware'])",
    )
    project_id: int | None = Field(
        default=None,
        description="Optional project ID for immediate association with a project",
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

    @field_validator("title", "description", "code", "language")
    @classmethod
    def strip_whitespace(cls, v, info):
        """Strip whitespace from string fields"""
        if v is None:
            return v

        stripped = v.strip()

        # Ensure required fields are not empty after stripping
        if not stripped:
            raise ValueError(f"{info.field_name} cannot be empty or whitespace only")

        return stripped

    @field_validator("language")
    @classmethod
    def lowercase_language(cls, v):
        """Convert language to lowercase for consistency"""
        if v is None or not v:
            return v
        return v.lower()

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        """Validate and clean tags"""
        if not v:
            return []

        # Strip whitespace and remove empty strings
        cleaned = [tag.strip() for tag in v if tag and tag.strip()]

        if len(cleaned) > settings.CODE_ARTIFACT_TAGS_MAX_COUNT:
            raise ValueError(f"Maximum {settings.CODE_ARTIFACT_TAGS_MAX_COUNT} tags allowed")

        return cleaned


class CodeArtifactUpdate(PatchModel):
    """Request model for updating a code artifact

    Follows PATCH semantics: only provided fields are updated.
    None/omitted values mean "don't change this field".

    Examples:
        Update code only: CodeArtifactUpdate(code="new implementation...")
        Add tags: CodeArtifactUpdate(tags=["tag1", "tag2", "tag3"])
        Change language: CodeArtifactUpdate(language="typescript")
    """
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=settings.CODE_ARTIFACT_TITLE_MAX_LENGTH,
        description="New title. Unchanged if null.",
    )
    description: str | None = Field(
        default=None,
        min_length=1,
        max_length=settings.CODE_ARTIFACT_DESCRIPTION_MAX_LENGTH,
        description="New description. Unchanged if null.",
    )
    code: str | None = Field(
        default=None,
        min_length=1,
        max_length=settings.CODE_ARTIFACT_CODE_MAX_LENGTH,
        description="New code content. Unchanged if null.",
    )
    language: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="New language. Use full names (e.g., 'python' not 'py'). Unchanged if null.",
    )
    tags: list[str] | None = Field(
        default=None,
        max_length=settings.CODE_ARTIFACT_TAGS_MAX_COUNT,
        description="New tags (replaces existing). Unchanged if null. Empty list [] clears tags.",
    )
    project_id: int | None = Field(
        default=None,
        description="New project association. Unchanged if null.",
    )

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

    @field_validator("title", "description", "code", "language")
    @classmethod
    def strip_whitespace(cls, v, info):
        """Strip whitespace from string fields"""
        if v is None:
            return v

        stripped = v.strip()

        # Don't allow empty after stripping (if provided)
        if not stripped:
            raise ValueError(f"{info.field_name} cannot be empty or whitespace only")

        return stripped

    @field_validator("language")
    @classmethod
    def lowercase_language(cls, v):
        """Convert language to lowercase for consistency"""
        if v is None or not v:
            return v
        return v.lower()

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        """Validate and clean tags"""
        if v is None:
            return None

        # Empty list is valid (clears tags)
        if not v:
            return []

        # Strip whitespace and remove empty strings
        cleaned = [tag.strip() for tag in v if tag and tag.strip()]

        if len(cleaned) > settings.CODE_ARTIFACT_TAGS_MAX_COUNT:
            raise ValueError(f"Maximum {settings.CODE_ARTIFACT_TAGS_MAX_COUNT} tags allowed")

        return cleaned


class CodeArtifact(CodeArtifactCreate):
    """Complete code artifact model with generated fields

    Extends CodeArtifactCreate with system-generated fields (id, timestamps, project_id).
    Used for responses that include full artifact details.

    Returned by:
    - create_code_artifact: After successfully creating an artifact
    - get_code_artifact: When retrieving a specific artifact by ID
    - update_code_artifact: After successfully updating an artifact
    """
    id: int = Field(
        ...,
        description="Unique artifact identifier (auto-generated)",
    )
    project_id: int | None = Field(
        default=None,
        description="Associated project ID. Null if not linked to a project.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=UTC),
        description="When the artifact was created (UTC)",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=UTC),
        description="When the artifact was last updated (UTC)",
    )

    model_config = ConfigDict(from_attributes=True)


class CodeArtifactSummary(BaseModel):
    """Lightweight code artifact summary for list operations

    Excludes heavy code content to minimize token usage when listing
    multiple artifacts. Contains just enough info to identify and filter.

    Used by:
    - list_code_artifacts: When listing all artifacts or filtering by project/language/tags
    """
    id: int = Field(
        ...,
        description="Unique artifact identifier",
    )
    title: str = Field(
        ...,
        description="Artifact title",
    )
    description: str = Field(
        ...,
        description="Artifact description",
    )
    language: str = Field(
        ...,
        description="Programming language",
    )
    tags: list[str] = Field(
        ...,
        description="Tags for categorization",
    )
    project_id: int | None = Field(
        default=None,
        description="Associated project ID",
    )
    created_at: datetime = Field(
        ...,
        description="When the artifact was created (UTC)",
    )
    updated_at: datetime = Field(
        ...,
        description="When the artifact was last updated (UTC)",
    )

    model_config = ConfigDict(from_attributes=True)
