"""Shared request validation helpers for the REST API routes.

Keeps the way routes report invalid input (400 responses) in one place.
"""
from pydantic import ValidationError
from starlette.responses import JSONResponse


def validation_error_response(error: ValidationError) -> JSONResponse:
    """Build the 400 response for a pydantic ``ValidationError``.

    ``ValidationError.errors()`` is not safe to hand to ``JSONResponse`` as is:
    errors raised by custom validators carry the exception object in ``ctx`` and
    non-finite floats (``NaN``/``Infinity``, accepted by ``json.loads``) are echoed in
    ``input``; both make JSON rendering raise and the client get a 500 instead.
    Only the documented ``type``, ``loc`` and ``msg`` keys are returned.
    """
    return JSONResponse(
        {
            "error": error.errors(
                include_url=False,
                include_context=False,
                include_input=False,
            ),
        },
        status_code=400,
    )
