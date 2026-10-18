"""Request models whose values must be storable on every supported database.

PostgreSQL text, varchar and jsonb columns cannot hold the NUL character (U+0000), and
jsonb cannot hold NaN or Infinity. SQLite accepts both, which hides the problem in tests
and then persists values that break later reads: a NaN stored in a JSON column makes every
response that carries it fail to serialise. Both backends therefore refuse these values
where the request is validated, so the REST routes answer 400 instead of surfacing a
driver error as a 500.
"""

import math
from typing import Any, ClassVar

from pydantic import BaseModel, ValidationError, model_validator
from pydantic_core import InitErrorDetails, PydanticCustomError

NUL = "\x00"

_MESSAGES = {
    "nul_character": "must not contain the NUL character (U+0000), which PostgreSQL cannot store",
    "non_finite_number": "must be a finite number, NaN and Infinity cannot be stored",
}


def find_unstorable(value: Any) -> tuple[tuple[str | int, ...], str] | None:
    """Find the first NaN, Infinity or NUL character inside a value

    Walks nested dicts and lists without recursion, so a deeply nested value cannot
    exhaust the stack.

    Returns:
        (location inside the value, error type), or None when the value is storable.
        A NUL in a dict key is reported at the location of the dict itself.
    """
    stack: list[tuple[tuple[str | int, ...], Any]] = [((), value)]
    while stack:
        loc, item = stack.pop()
        if isinstance(item, str):
            if NUL in item:
                return loc, "nul_character"
        elif isinstance(item, float):
            if not math.isfinite(item):
                return loc, "non_finite_number"
        elif isinstance(item, dict):
            if any(isinstance(key, str) and NUL in key for key in item):
                return loc, "nul_character"
            # Reversed, so the first entry is popped first and errors follow document order
            stack.extend((loc + (key,), child) for key, child in reversed(item.items()))
        elif isinstance(item, list | tuple):
            stack.extend((loc + (index,), child) for index, child in reversed(list(enumerate(item))))
    return None


class StorableInput(BaseModel):
    """Base class for request models that are written to the database

    Rejects NaN, Infinity and NUL characters in any field. The error never echoes the
    offending value: NaN cannot be written by a strict JSON encoder, which is what the
    REST routes use to return validation errors.

    A model that also serves as a response model (Plan extends PlanCreate) sets
    ``enforce_storage_limits = False``, so rows stored before a rule existed stay readable.
    """

    enforce_storage_limits: ClassVar[bool] = True

    @model_validator(mode="after")
    def reject_unstorable_values(self):
        """Refuse values that PostgreSQL cannot store, whichever backend is configured"""
        if not self.enforce_storage_limits:
            return self

        errors = []
        for name in type(self).model_fields:
            found = find_unstorable(getattr(self, name))
            if found is not None:
                loc, error_type = found
                errors.append(InitErrorDetails(
                    type=PydanticCustomError(error_type, _MESSAGES[error_type]),
                    loc=(name, *loc),
                    input=None,
                ))

        if errors:
            raise ValidationError.from_exception_data(type(self).__name__, errors)

        return self
