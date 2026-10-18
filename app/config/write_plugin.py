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
        handler = getattr(importlib.import_module(module_name), function_name)
    except Exception:
        raise ValueError("MEMORY_WRITE_PLUGIN could not be imported") from None
    if not inspect.iscoroutinefunction(handler):
        raise ValueError("MEMORY_WRITE_PLUGIN must reference an async function")
    return handler
