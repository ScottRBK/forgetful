"""Shared builders for Entity Plugin integration tests (not a test module)."""

from app.models.entity_models import EntityCreate, EntityType


def candidate(**changes):
    base = {"name": "Acme Corp", "entity_type": EntityType.ORGANIZATION, "tags": []}
    return EntityCreate(**(base | changes))
