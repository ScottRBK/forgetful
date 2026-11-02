"""Detached contexts and results for the trusted Memory and Entity write plugins."""

from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.entity_models import Entity, EntityCreate, EntityUpdate
from app.models.memory_models import Memory, MemoryCreate, MemorySummary, MemoryUpdate

MemoryOperation = Literal["create", "update", "obsolete", "restore"]


class MemoryWriteRequest(BaseModel):
    """Detached domain snapshots; operation distinguishes create from update."""

    operation: Literal["create", "update"]
    user_id: UUID
    submitted: MemoryCreate | MemoryUpdate
    previous: Memory | None
    proposed: MemoryCreate


class MemoryLifecycleSubmission(BaseModel):
    """Parsed lifecycle input; restore supplies only the memory ID."""

    memory_id: int
    reason: str | None = None
    superseded_by: int | None = None


class MemoryLifecycleState(BaseModel):
    """Proposed lifecycle fields. Persistence assigns the obsolescence timestamp."""

    is_obsolete: bool
    obsolete_reason: str | None
    superseded_by: int | None


class MemoryLifecycleRequest(BaseModel):
    operation: Literal["obsolete", "restore"]
    user_id: UUID
    submitted: MemoryLifecycleSubmission
    previous: Memory
    proposed: MemoryLifecycleState


class WriteDecision(BaseModel):
    """A client-safe decision. No replacement payload or persistence capability."""

    model_config = ConfigDict(extra="forbid", revalidate_instances="always")

    outcome: Literal["allow", "warn", "reject"]
    message: str | None = None
    code: str | None = None

    @model_validator(mode="after")
    def require_message(self) -> Self:
        if self.outcome != "allow" and (not self.message or not self.message.strip()):
            raise ValueError("warn and reject decisions require a nonblank message")
        return self


class PluginWarning(BaseModel):
    """Advisory result: a saved write cannot be rejected."""

    model_config = ConfigDict(extra="forbid", revalidate_instances="always")

    outcome: Literal["warn"] = "warn"
    message: str
    code: str | None = None

    @model_validator(mode="after")
    def require_message(self) -> Self:
        if not self.message.strip():
            raise ValueError("warnings require a nonblank message")
        return self


class MemorySavedRequest(BaseModel):
    """Persisted snapshots; similarity is unavailable except on auto-linked creates."""

    operation: MemoryOperation
    user_id: UUID
    previous: Memory | None
    saved: Memory
    similar_memories: list[MemorySummary] | None = None


class MemoryCreateResult(BaseModel):
    memory: Memory
    similar_memories: list[MemorySummary] = Field(default_factory=list)
    plugin_warnings: list[PluginWarning] = Field(default_factory=list)


class MemoryUpdateResult(BaseModel):
    memory: Memory | None
    plugin_warnings: list[PluginWarning] = Field(default_factory=list)


class MemoryLifecycleResult(BaseModel):
    success: bool
    plugin_warnings: list[PluginWarning] = Field(default_factory=list)


EntityOperation = Literal["create", "update", "delete"]


class EntityDeleteSubmission(BaseModel):
    entity_id: int


class EntityWriteRequest(BaseModel):
    """Detached domain snapshots; operation distinguishes create, update, and delete."""

    operation: EntityOperation
    user_id: UUID
    submitted: EntityCreate | EntityUpdate | EntityDeleteSubmission
    previous: Entity | None
    proposed: EntityCreate | None


class EntitySavedRequest(BaseModel):
    operation: Literal["create", "update"]
    user_id: UUID
    saved: Entity
    previous: Entity | None


class EntityDeletedRequest(BaseModel):
    operation: Literal["delete"] = "delete"
    user_id: UUID
    deleted_entity_id: int
    previous: Entity


class EntityWriteResult(BaseModel):
    entity: Entity
    plugin_warnings: list[PluginWarning] = Field(default_factory=list)


class EntityDeleteResult(BaseModel):
    deleted: bool
    plugin_warnings: list[PluginWarning] = Field(default_factory=list)
