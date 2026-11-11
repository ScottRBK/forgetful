"""Portable skill package contracts; source IDs and provenance are never portable."""
import base64
import binascii
import re
import unicodedata
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.config.settings import settings
from app.models.code_artifact_models import CodeArtifact, CodeArtifactCreate
from app.models.document_models import Document, DocumentCreate
from app.models.file_models import File, FileCreate
from app.models.skill_models import Skill

BundleKind = Literal["document", "code_artifact", "file"]
_WINDOWS_DEVICE = re.compile(r"^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)", re.I)


def validate_bundle_path(value: str) -> str:
    """Require a portable relative path, never normalise an unsafe spelling."""
    if not value or len(value) > 500 or unicodedata.normalize("NFC", value) != value:
        raise ValueError("Bundle path must be NFC and contain 1 to 500 characters")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise ValueError("Bundle path must be valid UTF-8") from exc
    if any(ord(c) < 32 or ord(c) == 127 or c in '\\:*?"<>|' for c in value):
        raise ValueError("Bundle path contains a non-portable character")
    parts = value.split("/")
    if len(parts) > 32 or any(
        not part or part in {".", ".."} or part.endswith((".", " "))
        or len(part.encode("utf-8")) > 255 or _WINDOWS_DEVICE.match(part)
        for part in parts
    ):
        raise ValueError("Bundle path must contain portable relative file segments")
    if parts[0].casefold() == "skill.md":
        raise ValueError("SKILL.md is reserved for the skill entry point")
    return value


def validate_bundle_paths(paths: list[str]) -> None:
    """Reject duplicate and file/directory prefix collisions across all kinds."""
    keys = [validate_bundle_path(path).casefold() for path in paths]
    if len(set(keys)) != len(keys):
        raise ValueError("Bundle paths collide")
    directories = {key.rsplit("/", index)[0]
                   for key in keys for index in range(1, key.count("/") + 1)}
    if directories & set(keys):
        raise ValueError("Bundle paths collide")


def bundle_text_bytes(value) -> int:
    if isinstance(value, str):
        if "\x00" in value:
            raise ValueError("Bundle text cannot contain NUL")
        try:
            return len(value.encode("utf-8", errors="strict"))
        except UnicodeEncodeError as exc:
            raise ValueError("Bundle text must be valid UTF-8") from exc
    if isinstance(value, dict):
        for key in value:
            bundle_text_bytes(key)  # Validate keys without charging their schema spelling.
        return sum(bundle_text_bytes(item) for item in value.values())
    if isinstance(value, list):
        return sum(bundle_text_bytes(item) for item in value)
    return 0


def bundle_resource_bytes(resource: dict, *, decode_binary: bool = True) -> int:
    """Count UTF-8 string values plus decoded binary, never schema key names."""
    fields = dict(resource)
    data = fields.pop("data", None)
    if fields.get("kind") == "document":
        fields.setdefault("document_type", "text")
    total = bundle_text_bytes(fields)
    if data is not None and decode_binary:
        try:
            total += len(base64.b64decode(data, validate=True))
        except (binascii.Error, ValueError) as exc:
            raise ValueError("Bundle file data must be strict base64") from exc
    return total


class _Resource(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    path: str
    title: str
    description: str
    tags: list[str] = Field(default_factory=list)

    @field_validator("path")
    @classmethod
    def portable_path(cls, value):
        return validate_bundle_path(value)


class BundleDocument(_Resource):
    kind: Literal["document"] = "document"
    content: str
    document_type: str | None = "text"

    def to_create(self, project_id: int | None) -> DocumentCreate:
        return DocumentCreate(
            **self.model_dump(exclude={"path", "kind"}),
            filename=self.path.rsplit("/", 1)[-1], project_id=project_id,
        )


class BundleCodeArtifact(_Resource):
    kind: Literal["code_artifact"] = "code_artifact"
    code: str
    language: str

    def to_create(self, project_id: int | None) -> CodeArtifactCreate:
        return CodeArtifactCreate(
            **self.model_dump(exclude={"path", "kind"}), project_id=project_id,
        )


class BundleFile(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    path: str
    kind: Literal["file"] = "file"
    description: str
    data: str
    mime_type: str
    tags: list[str] = Field(default_factory=list)

    @field_validator("path")
    @classmethod
    def portable_path(cls, value):
        return validate_bundle_path(value)

    def to_create(self, project_id: int | None) -> FileCreate:
        try:
            decoded = base64.b64decode(self.data, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("Bundle file data must be strict base64") from exc
        if not decoded:
            raise ValueError("Empty bundle files are not supported")
        return FileCreate(
            filename=self.path.rsplit("/", 1)[-1], description=self.description,
            data=self.data, mime_type=self.mime_type, tags=self.tags, project_id=project_id,
        )


BundleResource = Annotated[
    BundleDocument | BundleCodeArtifact | BundleFile, Field(discriminator="kind"),
]


class SkillBundle(BaseModel):
    """A SKILL.md entry point and only the resources forming its package."""
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    schema_version: Literal[1] = 1
    skill_md: str = Field(min_length=1)
    resources: list[BundleResource] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def bound_payload_before_decoding(cls, value):
        if isinstance(value, cls):
            return value
        if not isinstance(value, dict):
            raise ValueError("Bundle must be an object")
        resources = value.get("resources", [])
        if not isinstance(resources, list) or len(resources) > settings.SKILL_BUNDLE_MAX_RESOURCES:
            raise ValueError("Bundle resource count exceeds SKILL_BUNDLE_MAX_RESOURCES")
        text_bytes = bundle_text_bytes(value.get("skill_md"))
        encoded_bytes = 0
        data_fields = 0
        for item in resources:
            if isinstance(item, BaseModel):
                item = item.model_dump()
            if not isinstance(item, dict):
                raise ValueError("Bundle resources must be objects")
            if "data" in item:
                data = item["data"]
                if not isinstance(data, str):
                    raise ValueError("Bundle binary data must be base64 text")
                encoded_bytes += len(data)
                data_fields += 1
            text_bytes += bundle_resource_bytes(item, decode_binary=False)
        remaining = settings.SKILL_BUNDLE_MAX_BYTES - text_bytes
        if remaining < 0 or encoded_bytes > 4 * ((remaining + 2) // 3) + 4 * data_fields:
            raise ValueError("Bundle exceeds SKILL_BUNDLE_MAX_BYTES")
        return value

    @model_validator(mode="after")
    def validate_resources(self):
        validate_bundle_paths([resource.path for resource in self.resources])
        total = bundle_text_bytes(self.skill_md)
        for resource in self.resources:
            resource.to_create(None)  # Apply the unchanged domain model constraints.
            total += bundle_resource_bytes(resource.model_dump())
        if total > settings.SKILL_BUNDLE_MAX_BYTES:
            raise ValueError("Bundle exceeds SKILL_BUNDLE_MAX_BYTES")
        return self


class SkillBundleMember(BaseModel):
    """Native owned-resource binding; never included in the portable package."""
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    path: str
    kind: BundleKind
    resource_id: int = Field(gt=0)

    @field_validator("path")
    @classmethod
    def portable_path(cls, value):
        return validate_bundle_path(value)


class SkillBundleImportResult(BaseModel):
    skill: Skill
    members: list[SkillBundleMember]


class PreparedBundleResource(BaseModel):
    """Validated native create payload, including destination provenance defaults."""
    path: str
    kind: BundleKind
    data: DocumentCreate | CodeArtifactCreate | FileCreate


class CreatedBundleResource(BaseModel):
    kind: BundleKind
    resource: Document | CodeArtifact | File


class CreatedSkillBundle(BaseModel):
    skill: Skill
    members: list[SkillBundleMember]
    resources: list[CreatedBundleResource]


class SkillBundleSnapshot(BaseModel):
    skill: Skill
    resources: list[BundleResource]


def project_bundle_resource(path: str, kind: BundleKind, row) -> BundleResource:
    """Project native rows with exactly the same fields on import and export."""
    if kind == "file":
        return BundleFile(path=path, description=row.description,
                          data=base64.b64encode(row.data).decode("ascii"),
                          mime_type=row.mime_type, tags=row.tags)
    common = {"path": path, "title": row.title, "description": row.description, "tags": row.tags}
    if kind == "document":
        return BundleDocument(**common, content=row.content, document_type=row.document_type)
    return BundleCodeArtifact(**common, code=row.code, language=row.language)


# Existing model tests and callers retain the original helper spelling.
_bundle_bytes = bundle_resource_bytes
