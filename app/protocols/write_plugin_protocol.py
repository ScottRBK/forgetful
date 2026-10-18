"""The single async callable supplied by a trusted administrator."""

from typing import Protocol

from app.models.write_plugin_models import MemoryWriteRequest, WriteDecision


class WritePlugin(Protocol):
    async def __call__(self, request: MemoryWriteRequest) -> WriteDecision:
        ...
