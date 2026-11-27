"""One administrator registration with explicit per-phase, per-operation handlers."""

import inspect
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Protocol, get_args

from app.models.write_plugin_models import (
    EntityDeletedRequest,
    EntityOperation,
    EntityRelationshipDeletedRequest,
    EntityRelationshipOperation,
    EntityRelationshipSavedRequest,
    EntityRelationshipWriteRequest,
    EntitySavedRequest,
    EntityWriteRequest,
    FileDeletedRequest,
    FileOperation,
    FileSavedRequest,
    FileWriteRequest,
    MemoryLifecycleRequest,
    MemoryLinkOperation,
    MemoryLinkRequest,
    MemoryLinkSavedRequest,
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


class EntityBeforeSave(Protocol):
    async def __call__(self, request: EntityWriteRequest) -> WriteDecision:
        ...


class EntityAfterSave(Protocol):
    async def __call__(
        self, request: EntitySavedRequest | EntityDeletedRequest,
    ) -> PluginWarning | None:
        ...


@dataclass(frozen=True)
class EntityPlugin:
    before_save: Mapping[EntityOperation, EntityBeforeSave] = field(default_factory=dict)
    after_save: Mapping[EntityOperation, EntityAfterSave] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for phase in ("before_save", "after_save"):
            handlers = getattr(self, phase)
            if not isinstance(handlers, Mapping):
                raise ValueError(f"{phase} must be an operation-to-handler mapping")
            handlers = dict(handlers)
            for operation, handler in handlers.items():
                if operation not in get_args(EntityOperation):
                    raise ValueError(f"{phase} contains an unsupported entity operation")
                if not inspect.iscoroutinefunction(handler):
                    raise ValueError(f"{phase} handlers must be async functions")
                try:
                    inspect.signature(handler).bind(object())
                except (TypeError, ValueError):
                    raise ValueError(f"{phase} handlers must accept one context argument") from None
            object.__setattr__(self, phase, MappingProxyType(handlers))


class EntityRelationshipBeforeSave(Protocol):
    async def __call__(self, request: EntityRelationshipWriteRequest) -> WriteDecision:
        ...


class EntityRelationshipAfterSave(Protocol):
    async def __call__(
        self, request: EntityRelationshipSavedRequest | EntityRelationshipDeletedRequest,
    ) -> PluginWarning | None:
        ...


@dataclass(frozen=True)
class EntityRelationshipPlugin:
    before_save: Mapping[EntityRelationshipOperation, EntityRelationshipBeforeSave] = field(
        default_factory=dict,
    )
    after_save: Mapping[EntityRelationshipOperation, EntityRelationshipAfterSave] = field(
        default_factory=dict,
    )

    def __post_init__(self) -> None:
        for phase in ("before_save", "after_save"):
            handlers = getattr(self, phase)
            if not isinstance(handlers, Mapping):
                raise ValueError(f"{phase} must be an operation-to-handler mapping")
            handlers = dict(handlers)
            for operation, handler in handlers.items():
                if operation not in get_args(EntityRelationshipOperation):
                    raise ValueError(
                        f"{phase} contains an unsupported entity-relationship operation",
                    )
                if not inspect.iscoroutinefunction(handler):
                    raise ValueError(f"{phase} handlers must be async functions")
                try:
                    inspect.signature(handler).bind(object())
                except (TypeError, ValueError):
                    raise ValueError(f"{phase} handlers must accept one context argument") from None
            object.__setattr__(self, phase, MappingProxyType(handlers))


class MemoryLinkBeforeSave(Protocol):
    async def __call__(self, request: MemoryLinkRequest) -> WriteDecision:
        ...


class MemoryLinkAfterSave(Protocol):
    async def __call__(self, request: MemoryLinkSavedRequest) -> PluginWarning | None:
        ...


@dataclass(frozen=True)
class MemoryLinkPlugin:
    before_save: Mapping[MemoryLinkOperation, MemoryLinkBeforeSave] = field(default_factory=dict)
    after_save: Mapping[MemoryLinkOperation, MemoryLinkAfterSave] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for phase in ("before_save", "after_save"):
            handlers = getattr(self, phase)
            if not isinstance(handlers, Mapping):
                raise ValueError(f"{phase} must be an operation-to-handler mapping")
            handlers = dict(handlers)
            for operation, handler in handlers.items():
                if operation not in get_args(MemoryLinkOperation):
                    raise ValueError(f"{phase} contains an unsupported memory-link operation")
                if not inspect.iscoroutinefunction(handler):
                    raise ValueError(f"{phase} handlers must be async functions")
                try:
                    inspect.signature(handler).bind(object())
                except (TypeError, ValueError):
                    raise ValueError(f"{phase} handlers must accept one context argument") from None
            object.__setattr__(self, phase, MappingProxyType(handlers))


class FileBeforeSave(Protocol):
    async def __call__(self, request: FileWriteRequest) -> WriteDecision:
        ...


class FileAfterSave(Protocol):
    async def __call__(
        self, request: FileSavedRequest | FileDeletedRequest,
    ) -> PluginWarning | None:
        ...


@dataclass(frozen=True)
class FilePlugin:
    """One administrator registration for file create, update and delete.

    The contract (phases, decisions, warning shape, registration rules) is the
    Memory Plugin introduced in PR #164. The implementation precedent, which this
    mirrors function for function, is the Entity Plugin in PR #184. Keep those two
    in step: a change to the contract belongs to #164's shape, and a change to how
    a phase is dispatched belongs to #184's shape.
    """

    before_save: Mapping[FileOperation, FileBeforeSave] = field(default_factory=dict)
    after_save: Mapping[FileOperation, FileAfterSave] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for phase in ("before_save", "after_save"):
            handlers = getattr(self, phase)
            if not isinstance(handlers, Mapping):
                raise ValueError(f"{phase} must be an operation-to-handler mapping")
            handlers = dict(handlers)
            for operation, handler in handlers.items():
                if operation not in get_args(FileOperation):
                    raise ValueError(f"{phase} contains an unsupported file operation")
                if not inspect.iscoroutinefunction(handler):
                    raise ValueError(f"{phase} handlers must be async functions")
                try:
                    inspect.signature(handler).bind(object())
                except (TypeError, ValueError):
                    raise ValueError(f"{phase} handlers must accept one context argument") from None
            object.__setattr__(self, phase, MappingProxyType(handlers))
