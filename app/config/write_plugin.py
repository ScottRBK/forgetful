"""Startup-only loading of trusted administrator Python; no sandbox or file uploads."""

import importlib
import inspect

from app.config.settings import Settings
from app.protocols.write_plugin_protocol import WritePlugin


def load_write_plugin(config: Settings) -> WritePlugin | None:
    reference = config.MEMORY_WRITE_PLUGIN.strip()
    if not reference:
        return None
    module_name, separator, function_name = reference.partition(":")
    if (not separator or not function_name.isidentifier()
            or not all(part.isidentifier() for part in module_name.split("."))):
        raise ValueError("MEMORY_WRITE_PLUGIN must be an importable module:function reference")
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        raise ValueError(
            f"MEMORY_WRITE_PLUGIN import failed for {module_name}: {type(exc).__name__}",
        ) from None
    try:
        handler = getattr(module, function_name)
    except Exception as exc:
        raise ValueError(
            f"MEMORY_WRITE_PLUGIN attribute lookup failed for {reference}: {type(exc).__name__}",
        ) from None
    if not inspect.iscoroutinefunction(handler):
        raise ValueError("MEMORY_WRITE_PLUGIN must reference an async function")
    return handler
