"""Integration tests for MCP tool-surface argument handling (stubbed I/O)
"""
from uuid import uuid4

import pytest

from app.models.entity_models import EntityCreate, EntityRelationshipCreate, EntityType


async def _entity_with_one_edge_each_way(service, user_id):
    """Entity 2 has one incoming (1 -> 2) and one outgoing (2 -> 3) relationship."""
    ids = []
    for name in ("First", "Middle", "Last"):
        entity = await service.create_entity(
            user_id, EntityCreate(name=name, entity_type=EntityType.ORGANIZATION, tags=[]),
        )
        ids.append(entity.id)
    first, middle, last = ids
    for source, target in ((first, middle), (middle, last)):
        await service.create_entity_relationship(
            user_id,
            EntityRelationshipCreate(
                source_entity_id=source, target_entity_id=target, relationship_type="manages",
            ),
        )
    return middle


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("direction", "expected"),
    [
        ("outgoing", 1),
        ("incoming", 1),
        ("Incoming", 1),
        ("OUTGOING", 1),
        ("  incoming  ", 1),
        ("both", 2),
        ("BOTH", 2),
        ("", 2),
        (None, 2),
    ],
)
async def test_get_entity_relationships_normalises_direction(
    test_entity_service, direction, expected,
):
    """Case and whitespace variants select one direction, 'both'/empty/None select both."""
    user_id = uuid4()
    middle = await _entity_with_one_edge_each_way(test_entity_service, user_id)

    relationships = await test_entity_service.get_entity_relationships(
        user_id, middle, direction=direction,
    )

    assert len(relationships) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("direction", ["sideways", "in", "out", 1, True])
async def test_get_entity_relationships_rejects_unknown_direction(
    test_entity_service, direction,
):
    """An unrecognised direction is an error instead of silently widening to both."""
    user_id = uuid4()
    middle = await _entity_with_one_edge_each_way(test_entity_service, user_id)

    with pytest.raises(ValueError, match="direction"):
        await test_entity_service.get_entity_relationships(
            user_id, middle, direction=direction,
        )
