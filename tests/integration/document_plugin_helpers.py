"""Shared builders for Document Plugin integration tests (not a test module)."""

from app.models.document_models import DocumentCreate


def candidate(**changes):
    base = {
        "title": "API Guide",
        "description": "Test document",
        "content": "Body text for the document.",
        "tags": [],
    }
    return DocumentCreate(**(base | changes))
