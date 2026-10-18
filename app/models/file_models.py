"""Pydantic models for File entities

Files store binary content (images, PDFs, fonts, etc.) as base64-encoded data.
They can be linked to memories and entities for multi-modal knowledge management.
"""
import base64
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import PydanticCustomError

from app.config.settings import settings

# Whitespace that MIME style encoders insert between base64 lines
_BASE64_WHITESPACE = str.maketrans("", "", " \t\r\n")


def _decode_base64(value: str) -> bytes:
    """Strictly decode base64 file content, rejecting anything that is not real content

    Characters outside the base64 alphabet are an error, not silently dropped, and the
    decoded content must not be empty. PydanticCustomError keeps the error context JSON
    serialisable for the REST routes that return ``ValidationError.errors()``.
    """
    try:
        decoded = base64.b64decode(value.translate(_BASE64_WHITESPACE), validate=True)
    except Exception:
        raise PydanticCustomError(
            "invalid_base64", "data must be valid base64-encoded content",
        ) from None

    if not decoded:
        raise PydanticCustomError(
            "empty_base64", "data must decode to non-empty content",
        )

    return decoded


class FileCreate(BaseModel):
    """Request model for creating a file

    Files store binary content encoded as base64 strings. The data is decoded
    and stored as raw bytes in the database (BYTEA/BLOB).

    Examples:
        Image: filename="screenshot.png", mime_type="image/png", data="iVBOR..."
        PDF: filename="spec.pdf", mime_type="application/pdf", data="JVBER..."
    """
    filename: str = Field(
        ...,
        min_length=1,
        max_length=settings.FILE_FILENAME_MAX_LENGTH,
        description="Original filename with extension (e.g., 'screenshot.png', 'report.pdf')",
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=settings.FILE_DESCRIPTION_MAX_LENGTH,
        description="Purpose and content description. What is this file? When should it be used?",
    )
    data: str = Field(
        ...,
        min_length=1,
        description="Base64-encoded file content. Decoded size must not exceed FILE_MAX_SIZE_BYTES.",
    )
    mime_type: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="MIME type (e.g., 'image/png', 'application/pdf', 'font/woff2')",
    )
    tags: list[str] = Field(
        default_factory=list,
        max_length=settings.FILE_TAGS_MAX_COUNT,
        description="Tags for categorization and discovery (e.g., ['screenshot', 'ui', 'v2'])",
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

    @field_validator("filename", "description", "mime_type")
    @classmethod
    def strip_whitespace(cls, v, info):
        """Strip whitespace from string fields"""
        if v is None:
            return v

        stripped = v.strip()

        if not stripped:
            raise ValueError(f"{info.field_name} cannot be empty or whitespace only")

        return stripped

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        """Validate and clean tags"""
        if not v:
            return []

        cleaned = [tag.strip() for tag in v if tag and tag.strip()]

        if len(cleaned) > settings.FILE_TAGS_MAX_COUNT:
            raise ValueError(f"Maximum {settings.FILE_TAGS_MAX_COUNT} tags allowed")

        return cleaned

    @field_validator("data")
    @classmethod
    def validate_base64_data(cls, v):
        """Validate that data is valid base64 and decoded size is within limits"""
        if not v:
            return v

        decoded = _decode_base64(v)

        if len(decoded) > settings.FILE_MAX_SIZE_BYTES:
            raise ValueError(
                f"Decoded file size ({len(decoded)} bytes) exceeds maximum "
                f"({settings.FILE_MAX_SIZE_BYTES} bytes)",
            )

        return v


class FileUpdate(BaseModel):
    """Request model for updating a file

    Follows PATCH semantics: only provided fields are updated.
    None/omitted values mean "don't change this field".
    """
    filename: str | None = Field(
        default=None,
        min_length=1,
        max_length=settings.FILE_FILENAME_MAX_LENGTH,
        description="New filename. Unchanged if null.",
    )
    description: str | None = Field(
        default=None,
        min_length=1,
        max_length=settings.FILE_DESCRIPTION_MAX_LENGTH,
        description="New description. Unchanged if null.",
    )
    data: str | None = Field(
        default=None,
        min_length=1,
        description="New base64-encoded content (replaces file). Unchanged if null.",
    )
    mime_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="New MIME type. Unchanged if null.",
    )
    tags: list[str] | None = Field(
        default=None,
        max_length=settings.FILE_TAGS_MAX_COUNT,
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

    @field_validator("filename", "description", "mime_type")
    @classmethod
    def strip_whitespace(cls, v, info):
        """Strip whitespace from string fields"""
        if v is None:
            return v

        stripped = v.strip()

        if not stripped:
            raise ValueError(f"{info.field_name} cannot be empty or whitespace only")

        return stripped

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        """Validate and clean tags"""
        if v is None:
            return None

        if not v:
            return []

        cleaned = [tag.strip() for tag in v if tag and tag.strip()]

        if len(cleaned) > settings.FILE_TAGS_MAX_COUNT:
            raise ValueError(f"Maximum {settings.FILE_TAGS_MAX_COUNT} tags allowed")

        return cleaned

    @field_validator("data")
    @classmethod
    def validate_base64_data(cls, v):
        """Validate that data is valid base64 and decoded size is within limits"""
        if v is None:
            return v

        decoded = _decode_base64(v)

        if len(decoded) > settings.FILE_MAX_SIZE_BYTES:
            raise ValueError(
                f"Decoded file size ({len(decoded)} bytes) exceeds maximum "
                f"({settings.FILE_MAX_SIZE_BYTES} bytes)",
            )

        return v


class File(FileCreate):
    """Complete file model with generated fields

    Extends FileCreate with system-generated fields (id, size_bytes, timestamps).
    Used for responses that include full file details including base64 data.
    """
    # Overrides FileCreate.data without min_length: zero-byte files stored before empty
    # content was rejected must stay readable and deletable.
    data: str = Field(
        ...,
        description="Base64-encoded file content.",
    )
    id: int = Field(
        ...,
        description="Unique file identifier (auto-generated)",
    )
    size_bytes: int = Field(
        ...,
        description="Size of decoded binary content in bytes",
    )
    project_id: int | None = Field(
        default=None,
        description="Associated project ID. Null if not linked to a project.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=UTC),
        description="When the file was created (UTC)",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=UTC),
        description="When the file was last updated (UTC)",
    )

    model_config = ConfigDict(from_attributes=True)


class FileSummary(BaseModel):
    """Lightweight file summary for list operations

    Excludes heavy base64 data to minimize token usage when listing
    multiple files. Contains just enough info to identify and filter.
    """
    id: int = Field(
        ...,
        description="Unique file identifier",
    )
    filename: str = Field(
        ...,
        description="Original filename",
    )
    description: str = Field(
        ...,
        description="File description",
    )
    mime_type: str = Field(
        ...,
        description="MIME type",
    )
    size_bytes: int = Field(
        ...,
        description="Size of decoded binary content in bytes",
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
        description="When the file was created (UTC)",
    )
    updated_at: datetime = Field(
        ...,
        description="When the file was last updated (UTC)",
    )

    model_config = ConfigDict(from_attributes=True)
