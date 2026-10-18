"""Write-only response extensions; stored/read memories never carry plugin warnings."""

from pydantic import Field

from app.models.memory_models import Memory, MemoryCreateResponse
from app.models.write_plugin_models import WriteDecision


class MemoryCreateWriteResponse(MemoryCreateResponse):
    plugin_warnings: list[WriteDecision] = Field(default_factory=list, exclude_if=lambda v: not v)


class MemoryUpdateResponse(Memory):
    plugin_warnings: list[WriteDecision] = Field(default_factory=list, exclude_if=lambda v: not v)
