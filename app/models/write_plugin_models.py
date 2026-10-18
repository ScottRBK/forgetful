"""Contracts for the trusted, decision-only memory Write Plugin."""

from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.memory_models import Memory, MemoryCreate, MemorySummary, MemoryUpdate


class MemoryWriteRequest(BaseModel):
    """Detached domain snapshots; operation distinguishes create from update."""

    operation: Literal["create", "update"]
    user_id: UUID
    submitted: MemoryCreate | MemoryUpdate
    previous: Memory | None
    proposed: MemoryCreate


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


class MemoryCreateResult(BaseModel):
    memory: Memory
    similar_memories: list[MemorySummary] = Field(default_factory=list)
    plugin_warnings: list[WriteDecision] = Field(default_factory=list)


class MemoryUpdateResult(BaseModel):
    memory: Memory | None
    plugin_warnings: list[WriteDecision] = Field(default_factory=list)
