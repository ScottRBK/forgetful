"""Base class for PATCH-style update request models"""

from typing import Any

from pydantic import BaseModel, model_validator


class PatchModel(BaseModel):
    """Base for update models where null means "leave this field unchanged".

    Update models are applied with ``model_dump(exclude_unset=True)``, so a field
    that is explicitly passed as ``None`` counts as set and would be written to
    the database: NOT NULL columns fail and JSON list columns end up holding a
    JSON null, which makes the record unreadable. The MCP adapters avoid this by
    filtering ``None`` before building the model; this base class gives every
    other caller (REST bodies, services, scripts) the same behaviour.

    Nulls are dropped before field validation, so a validator that turns a
    value into ``None`` on purpose still marks the field as set. That is how an
    empty string clears an optional field (for example ``notes=""``).
    """

    @model_validator(mode="before")
    @classmethod
    def _drop_explicit_nulls(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return {name: value for name, value in data.items() if value is not None}
        return data
