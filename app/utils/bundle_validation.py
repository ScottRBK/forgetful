"""Client-safe errors for portable bundle validation."""
from functools import wraps

from pydantic import ValidationError


def bundle_validation_message(error: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(part) for part in item['loc']) or 'bundle'}: {item['msg']}"
        for item in error.errors(include_input=False, include_url=False, include_context=False)
    )


def safe_bundle_validation(function):
    """Strip stored input values before errors cross a service/transport boundary."""
    @wraps(function)
    async def wrapped(*args, **kwargs):
        try:
            return await function(*args, **kwargs)
        except ValidationError as error:
            raise ValueError(bundle_validation_message(error)) from None
    return wrapped
