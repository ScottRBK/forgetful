"""Startup-only loading of trusted administrator Python; no sandbox or file uploads."""

import importlib

from app.config.settings import Settings
from app.protocols.write_plugin_protocol import EntityPlugin, MemoryPlugin


def load_write_plugin(config: Settings) -> MemoryPlugin | None:
    reference = config.MEMORY_WRITE_PLUGIN.strip()
    if not reference:
        return None
    module_name, separator, object_name = reference.partition(":")
    if (not separator or not object_name.isidentifier()
            or not all(part.isidentifier() for part in module_name.split("."))):
        raise ValueError("MEMORY_WRITE_PLUGIN must be an importable module:object reference")
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        raise ValueError(
            f"MEMORY_WRITE_PLUGIN import failed for {module_name}: {type(exc).__name__}",
        ) from None
    try:
        plugin = getattr(module, object_name)
    except Exception as exc:
        raise ValueError(
            f"MEMORY_WRITE_PLUGIN attribute lookup failed for {reference}: {type(exc).__name__}",
        ) from None
    if not isinstance(plugin, MemoryPlugin):
        raise ValueError("MEMORY_WRITE_PLUGIN must reference a MemoryPlugin registration")
    return plugin


def load_entity_plugin(config: Settings) -> EntityPlugin | None:
    reference = config.ENTITY_WRITE_PLUGIN.strip()
    if not reference:
        return None
    module_name, separator, object_name = reference.partition(":")
    if (not separator or not object_name.isidentifier()
            or not all(part.isidentifier() for part in module_name.split("."))):
        raise ValueError("ENTITY_WRITE_PLUGIN must be an importable module:object reference")
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        raise ValueError(
            f"ENTITY_WRITE_PLUGIN import failed for {module_name}: {type(exc).__name__}",
        ) from None
    try:
        plugin = getattr(module, object_name)
    except Exception as exc:
        raise ValueError(
            f"ENTITY_WRITE_PLUGIN attribute lookup failed for {reference}: {type(exc).__name__}",
        ) from None
    if not isinstance(plugin, EntityPlugin):
        raise ValueError("ENTITY_WRITE_PLUGIN must reference an EntityPlugin registration")
    return plugin
