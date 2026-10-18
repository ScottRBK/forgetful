from datetime import UTC, datetime
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationInfo,
    field_validator,
)
from pydantic_core import PydanticCustomError

from app.config.settings import settings

# Write-time rules for request models (MemoryCreate, MemoryUpdate).
#
# They are attached to the *types* of the request fields rather than to validators so
# that the Memory response model, which re-declares those fields as plain types, never
# enforces them: rows stored under an older or looser rule must stay readable.
#
# Violations raise PydanticCustomError instead of ValueError: the message stays clean
# ("title cannot be empty ...", no "Value error, " prefix) and the error context holds
# plain values, whereas a ValueError puts the exception object there, which cannot be
# serialised by anything that returns ``e.errors()`` to a client.


def _reject_blank(value: str, info: ValidationInfo) -> str:
    """Reject text that is empty after trimming; the value itself is kept verbatim"""
    if not value.strip():
        raise PydanticCustomError(
            "blank_text",
            "{field} cannot be empty or whitespace only",
            {"field": info.field_name},
        )
    return value


# Text that must carry content: blank values pass min_length=1 but are meaningless. The
# length constraints live in the type, ahead of the validators, so pydantic applies them
# to the str schema itself and keeps its usual "String should have at most N characters"
# errors even when the field is Optional.
_Title = Annotated[
    str,
    StringConstraints(min_length=1, max_length=settings.MEMORY_TITLE_MAX_LENGTH),
    AfterValidator(_reject_blank),
]
_Content = Annotated[
    str,
    StringConstraints(min_length=1, max_length=settings.MEMORY_CONTENT_MAX_LENGTH),
    AfterValidator(_reject_blank),
]
_Context = Annotated[
    str,
    StringConstraints(min_length=1, max_length=settings.MEMORY_CONTEXT_MAX_LENGTH),
    AfterValidator(_reject_blank),
]

# List items are trimmed before the cap is checked so that padding does not count towards
# it. The cap also bounds the text that query_memory token-counts for every search hit.
_Keyword = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=settings.MEMORY_KEYWORD_MAX_LENGTH),
]
_Tag = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=settings.MEMORY_TAG_MAX_LENGTH),
]
_SourceFile = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=settings.MEMORY_SOURCE_FILE_MAX_LENGTH),
]


class MemoryCreate(BaseModel):
    """Request model for creating a memory
    
    Follows atomic memory principles (Zettlekasten)
    - ONE concept per memory (easily titled, understood at first glance)
    - for detailed analysis > 300 words, use create_document instead and
    create a smaller memory linking to the document

    Examples:
        Good (atomic): "TTS engine preferences: XTTS-v2"
        Bad (mega): "Complete TTS evaluation with all pros/cons/results" 
    """
    title: _Title = Field(
        ...,
        description="Concise, scannable title (5-50 words). Examples: 'Python QueueHandler prevents asyncio blocking', 'TTS preference: XTTS-v2'",
    )
    content: _Content = Field(
        ...,
        description="ONE concept, self-contained (max ~400 words). If >300 words, use create_document and extract atomic memories instead.",
    )
    context: str = Field(
        ...,
        max_length=settings.MEMORY_CONTEXT_MAX_LENGTH,
        description="WHY this matters, HOW it relates to other concepts, WHAT implications. Enables intelligent auto-linking and semantic retrieval.",
    )
    keywords: list[_Keyword] = Field(
        ...,
        max_length=settings.MEMORY_KEYWORDS_MAX_COUNT,
        description="Search terms for semantic discovery (e.g., 'python', 'asyncio', 'logging'). Max 10.",
    )
    tags: list[_Tag] = Field(
        ...,
        max_length=settings.MEMORY_TAGS_MAX_COUNT,
        description="Categories for grouping memories (e.g., 'pattern', 'decision', 'bug-fix'). Max 10.",
    )
    importance: int = Field(
        7,
        ge=1,
        le=10,
        description="Importance 1-10 (default 7): 9-10=personal facts/foundational patterns, 8-9=critical solutions/decisions, 7-8=useful patterns/preferences, 6-7=milestones/solutions, <6=discourage.",
    )
    project_ids: list[int] | None = Field(
        default=None,
        description="Link to project(s) for scoped queries. Enables 'show memories for Project X' filtering.",
    )
    code_artifact_ids: list[int] | None = Field(
        default=None,
        description="Code artifact IDs to link (create artifacts first). Links implementation examples to this memory.",
    )
    document_ids: list[int] | None = Field(
        default=None,
        description="Document IDs to link (create documents first). Links detailed analysis/narrative to this atomic memory.",
    )
    file_ids: list[int] | None = Field(
        default=None,
        description="File IDs to link (create files first). Links binary assets (images, PDFs, etc.) to this memory.",
    )
    skill_ids: list[int] | None = Field(
        default=None,
        description="Skill IDs to link (create skills first). Links procedural knowledge to this memory.",
    )

    # Provenance tracking fields (optional) - for tracing AI-generated content
    source_repo: str | None = Field(
        default=None,
        max_length=200,
        description="Repository/project source (e.g., 'owner/repo')",
    )
    source_files: list[_SourceFile] | None = Field(
        default=None,
        description="Files that informed this memory (JSON list of paths)",
    )
    source_url: str | None = Field(
        default=None,
        max_length=2048,
        description="URL to original source material",
    )
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Encoding confidence score (0.0-1.0)",
    )
    encoding_agent: str | None = Field(
        default=None,
        max_length=100,
        description="Agent/process that created this memory",
    )
    encoding_version: str | None = Field(
        default=None,
        max_length=50,
        description="Version of encoding process/prompt",
    )
    agent_id: str | None = Field(
        default=None,
        max_length=100,
        description="Agent identity (e.g., 'CodeAgentUltra')",
    )
    agent_version: str | None = Field(
        default=None,
        max_length=50,
        description="Agent version (e.g., '1.0')",
    )
    agent_model: str | None = Field(
        default=None,
        max_length=100,
        description="LLM model used (e.g., 'claude-sonnet-4-6')",
    )

    @field_validator("keywords", "tags")
    @classmethod
    def validate_lists(cls, v):
        """Ensure the list doesn't contain empty strings

        The maximum count is enforced by the field's max_length, which is checked first.
        """
        return [item.strip() for item in v if item.strip()]

    @field_validator("source_files")
    @classmethod
    def validate_source_files(cls, v):
        """Clean empty strings from source_files list"""
        if v is None:
            return None
        return [item.strip() for item in v if item.strip()]

class MemoryUpdate(BaseModel):
    """Request model for updating a memory"""
    title: _Title | None = Field(
        None,
        description="New title (5-50 words, scannable). Unchanged if null.",
    )
    content: _Content | None = Field(
        None,
        description="New content (ONE concept, max ~400 words). Unchanged if null.",
    )
    context: _Context | None = Field(
        None,
        description="New context (WHY/HOW/WHAT for auto-linking). Unchanged if null.",
    )
    keywords: list[_Keyword] | None = Field(
        None,
        max_length=settings.MEMORY_KEYWORDS_MAX_COUNT,
        description="New search terms (max 10). Replaces existing if provided, unchanged if null.",
    )
    tags: list[_Tag] | None = Field(
        None,
        max_length=settings.MEMORY_TAGS_MAX_COUNT,
        description="New categories (max 10). Replaces existing if provided, unchanged if null.",
    )
    importance: int | None = Field(
        None,
        ge=1,
        le=10,
        description="New importance 1-10: 9-10=personal/foundational, 8-9=critical, 7-8=useful, 6-7=milestones, <6=discourage. Unchanged if null.",
    )
    project_ids: list[int] | None = Field(
        None,
        description="New project associations. Replaces existing if provided, unchanged if null.",
    )
    code_artifact_ids: list[int] | None = Field(
        None,
        description="New code artifact links. Replaces existing if provided, unchanged if null.",
    )
    document_ids: list[int] | None = Field(
        None,
        description="New document links. Replaces existing if provided, unchanged if null.",
    )
    file_ids: list[int] | None = Field(
        None,
        description="New file links. Replaces existing if provided, unchanged if null.",
    )
    skill_ids: list[int] |None = Field(
        None,
        description="New skill IDs to link (create sklls first) to this memory",
    )

    # Provenance tracking fields (optional) - for tracing AI-generated content
    source_repo: str | None = Field(
        None,
        max_length=200,
        description="New repository/project source. Unchanged if null.",
    )
    source_files: list[_SourceFile] | None = Field(
        None,
        description="New source files list. Replaces existing if provided, unchanged if null.",
    )
    source_url: str | None = Field(
        None,
        max_length=2048,
        description="New URL to source material. Unchanged if null.",
    )
    confidence: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="New encoding confidence score (0.0-1.0). Unchanged if null.",
    )
    encoding_agent: str | None = Field(
        None,
        max_length=100,
        description="New agent/process identifier. Unchanged if null.",
    )
    encoding_version: str | None = Field(
        None,
        max_length=50,
        description="New encoding process version. Unchanged if null.",
    )
    agent_id: str | None = Field(
        None,
        max_length=100,
        description="New agent identity. Unchanged if null.",
    )
    agent_version: str | None = Field(
        None,
        max_length=50,
        description="New agent version. Unchanged if null.",
    )
    agent_model: str | None = Field(
        None,
        max_length=100,
        description="New LLM model. Unchanged if null.",
    )

    @field_validator("keywords", "tags")
    @classmethod
    def validate_lists(cls, v):
        """Ensure the list doesn't contain empty strings

        The maximum count is enforced by the field's max_length, which is checked first.
        """
        if v is None:
            return None  # Keep None for optional fields in update model

        return [item.strip() for item in v if item.strip()]

    @field_validator("source_files")
    @classmethod
    def validate_source_files(cls, v):
        """Clean empty strings from source_files list"""
        if v is None:
            return None
        return [item.strip() for item in v if item.strip()]

class Memory(MemoryCreate):
    id: int
    # Limits apply when a memory is written, not when it is read: the settings behind them
    # can be lowered after data was stored, and older versions accepted blank text. The
    # request fields that carry a write-time rule are therefore re-declared as plain types.
    title: str = Field(..., description=MemoryCreate.model_fields["title"].description)
    content: str = Field(..., description=MemoryCreate.model_fields["content"].description)
    context: str = Field(..., description=MemoryCreate.model_fields["context"].description)
    keywords: list[str] = Field(..., description=MemoryCreate.model_fields["keywords"].description)
    tags: list[str] = Field(..., description=MemoryCreate.model_fields["tags"].description)
    source_files: list[str] | None = Field(
        default=None,
        description=MemoryCreate.model_fields["source_files"].description,
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC), frozen=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    project_ids: list[int] = Field(default_factory=list)
    linked_memory_ids: list[int] = Field(default_factory=list)
    code_artifact_ids: list[int] = Field(default_factory=list, description="Linked code artifact IDs")
    document_ids: list[int] = Field(default_factory=list, description="Linked document IDs")
    file_ids: list[int] = Field(default_factory=list, description="Linked file IDs")
    skill_ids: list[int] = Field(default_factory=list, description="Linked skill Ids")

    # Lifecycle management fields
    is_obsolete: bool = Field(default=False, description="Whether this memory has been marked obsolete")
    obsolete_reason: str | None = Field(default=None, description="Reason why this memory was marked obsolete")
    superseded_by: int | None = Field(default=None, description="ID of memory that supersedes this one")
    obsoleted_at: datetime | None = Field(default=None, description="When this memory was marked obsolete")

    # Usage tracking (read-only from the API surface; mutated only by the
    # internal `record_memory_access` repository method so `updated_at` is not
    # distorted and external callers cannot fake read counters).
    access_count: int = Field(default=0, description="Number of times this memory has been returned by a read path")
    last_accessed_at: datetime | None = Field(
        default=None,
        description="Last time this memory was returned by a read path (null = never accessed)",
    )

    model_config = ConfigDict(from_attributes=True)

class MemorySummary(BaseModel):
    """Lightweight memory summary for list views"""
    id: int
    title: str
    keywords: list[str]
    tags: list[str]
    importance: int
    created_at: datetime
    updated_at: datetime
    similarity: float | None = Field(
        default=None,
        description="Cosine similarity to the new memory when returned by create_memory",
    )

    model_config = ConfigDict(from_attributes=True)


class MemoryScore(BaseModel):
    """Retrieval score for one primary memory, aligned by index with primary_memories"""

    memory_id: int
    similarity: float = Field(..., description="1 - cosine distance to the query embedding")
    rerank_score: float | None = Field(
        default=None,
        description="Cross-encoder score when RERANKING_ENABLED, else null",
    )


class ObsoleteMatch(BaseModel):
    """Obsolete memory whose embedding is at or above OBSOLETE_WARNING_THRESHOLD"""

    id: int
    title: str
    similarity: float
    obsolete_reason: str | None = None
    superseded_by: int | None = None
    obsoleted_at: datetime | None = None
    project_ids: list[int] = Field(default_factory=list)


class MemoryCreateResponse(BaseModel):
    """Lightweight response information to confirm memory creation"""
    id: int
    title: str
    linked_memory_ids: list[int] = Field(default_factory=list)
    project_ids: list[int] = Field(default_factory=list)
    code_artifact_ids: list[int] = Field(default_factory=list)
    document_ids: list[int] = Field(default_factory=list)
    file_ids: list[int] = Field(default_factory=list)
    skill_ids: list[int] = Field(default_factory=list)
    similar_memories: list[MemorySummary] = Field(
        default_factory=list,
        description="Summaries of similar memories that were auto-linked for review",
    )
    obsolete_matches: list[ObsoleteMatch] = Field(
        default_factory=list,
        description=(
            "Obsolete memories at or above OBSOLETE_WARNING_THRESHOLD when OBSOLETE_WARNING_ENABLED; "
            "always [] when OBSOLETE_WARNING_ENABLED is false; check superseded_by before keeping this memory"
        ),
    )


class MemoryListResponse(BaseModel):
    """Paginated list of memories for REST API"""
    memories: list[Memory]
    total: int = Field(..., description="Total count of memories matching filters")
    limit: int = Field(..., description="Maximum results per page")
    offset: int = Field(..., description="Number of results skipped")

class MemoryQueryRequest(BaseModel):
    """Request model for querying memories"""
    query: str = Field(
        ...,
        min_length=1,
        description="Natural language query for semantic search (e.g., 'Python logging best practices')",
    )
    query_context: str = Field(
        ...,
        min_length=1,
        description="Contextual reasoning behind why you are searching for this information",
    )
    k: int = Field(
        3,
        ge=1,
        le=20,
        description="Number of top semantic matches to return (primary results)",
    )
    include_links: int = Field(
        1,
        ge=0,
        le=5,
        description="Graph traversal depth (0=no links, 1=direct neighbors, 2+=exponential context bloat). Recommended: 0-1.",
    )
    token_context_threshold: int = Field(
        8000,
        ge=4000,
        le=25000,
        description="Max tokens before truncating results (8K default fits most LLM contexts)",
    )
    max_links_per_primary: int = Field(
        5,
        ge=0,
        le=10,
        description="Max linked memories per primary result (controls context expansion)",
    )
    importance_threshold: int | None = Field(
        None,
        ge=1,
        le=10,
        description="Filter out memories below this importance (e.g., 7=only important memories)",
    )
    project_ids: list[int] | None = Field(
        None,
        description="Filter results to specific projects (scoped search within project context)",
    )
    strict_project_filter: bool = Field(
        False,
        description="Opt out flag to exclude memories from being retrieved from outside of the project",
    )

class LinkedMemory(BaseModel):
    """Memory with linked context"""
    memory: Memory
    link_source_id: int = Field(..., description="ID of memory this is linked from")

    model_config = ConfigDict(from_attributes=True)

class MemoryQueryResult(BaseModel):
    """Response Model for memory query"""
    query: str
    primary_memories: list[Memory]
    linked_memories: list[LinkedMemory] = Field(default_factory=list)
    scores: list[MemoryScore] = Field(
        default_factory=list,
        description="One entry per primary memory, same order",
    )
    total_count: int
    token_count: int
    truncated: bool = Field(False, description="Whether the results were truncated due to token budget")

class MemoryLinkRequest(BaseModel):
    """Request model for linking memories"""
    memory_id: int = Field(..., description="Source memory ID")
    related_ids: list[int] = Field(..., min_length=1, description="Target memory IDs to link")

    @field_validator("related_ids")
    @classmethod
    def validate_related_ids(cls, v, info):
        """Ensure memory is not linking to itself"""
        if "memory_id" in info.data and info.data["memory_id"] in v:
            raise ValueError("Cannot link memory to itself")
        return v



