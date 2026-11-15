"""Write-only response extensions; stored/read memories never carry plugin warnings."""

from pydantic import BaseModel, Field

from app.models.entity_models import Entity
from app.models.memory_models import Memory, MemoryCreateResponse
from app.models.write_plugin_models import MemoryLinkOutcome, PluginWarning


class MemoryCreateWriteResponse(MemoryCreateResponse):
    link_outcomes: list[MemoryLinkOutcome] | None = Field(default=None, exclude_if=lambda v: v is None)
    plugin_warnings: list[PluginWarning] = Field(default_factory=list, exclude_if=lambda v: not v)


class MemoryUpdateResponse(Memory):
    plugin_warnings: list[PluginWarning] = Field(default_factory=list, exclude_if=lambda v: not v)


class MemoryLifecycleResponse(BaseModel):
    success: bool
    plugin_warnings: list[PluginWarning] = Field(default_factory=list, exclude_if=lambda v: not v)


class EntityWriteResponse(Entity):
    plugin_warnings: list[PluginWarning] = Field(default_factory=list, exclude_if=lambda v: not v)


class EntityDeleteResponse(BaseModel):
    success: bool
    plugin_warnings: list[PluginWarning] = Field(default_factory=list, exclude_if=lambda v: not v)
