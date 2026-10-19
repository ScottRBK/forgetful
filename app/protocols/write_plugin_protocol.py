"""One administrator registration with explicit per-phase, per-operation handlers."""

import inspect
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Protocol, get_args

from app.models.write_plugin_models import (
    MemoryLifecycleRequest,
    MemoryOperation,
    MemorySavedRequest,
    MemoryWriteRequest,
    PluginWarning,
    WriteDecision,
)


class BeforeSave(Protocol):
    async def __call__(self, request: MemoryWriteRequest | MemoryLifecycleRequest) -> WriteDecision:
        ...


class AfterSave(Protocol):
    async def __call__(self, request: MemorySavedRequest) -> PluginWarning | None:
        ...


@dataclass(frozen=True)
class MemoryPlugin:
    before_save: Mapping[MemoryOperation, BeforeSave] = field(default_factory=dict)
    after_save: Mapping[MemoryOperation, AfterSave] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for phase in ("before_save", "after_save"):
            handlers = getattr(self, phase)
            if not isinstance(handlers, Mapping):
                raise ValueError(f"{phase} must be an operation-to-handler mapping")
            handlers = dict(handlers)
            for operation, handler in handlers.items():
                if operation not in get_args(MemoryOperation):
                    raise ValueError(f"{phase} contains an unsupported memory operation")
                if not inspect.iscoroutinefunction(handler):
                    raise ValueError(f"{phase} handlers must be async functions")
                try:
                    inspect.signature(handler).bind(object())
                except (TypeError, ValueError):
                    raise ValueError(f"{phase} handlers must accept one context argument") from None
            # Freeze a copy: changing the administrator's original dict cannot alter dispatch.
            object.__setattr__(self, phase, MappingProxyType(handlers))
