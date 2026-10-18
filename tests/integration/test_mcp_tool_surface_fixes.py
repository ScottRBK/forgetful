"""Integration tests for MCP tool-surface argument handling (stubbed I/O)
"""
from uuid import uuid4

import pytest

from app.models.entity_models import EntityCreate, EntityRelationshipCreate, EntityType
from app.routes.mcp.tool_adapters import (
    _coerce_optional_int_id,
    _coerce_optional_int_ids,
    _coerce_str_list,
)


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


@pytest.mark.parametrize(
    ("value", "expected"),
    [(None, None), (7, 7), ("7", 7), (" 7 ", 7), (7.0, 7)],
)
def test_coerce_optional_int_id_accepts_valid_ids(value, expected):
    assert _coerce_optional_int_id(value, "project_id") == expected


@pytest.mark.parametrize("value", [True, False, 1.9, float("nan"), "abc", "", [1], {"a": 1}])
def test_coerce_optional_int_id_rejects_invalid_ids(value):
    with pytest.raises(ValueError, match="project_id"):
        _coerce_optional_int_id(value, "project_id")


@pytest.mark.parametrize(
    ("value", "expected"),
    [(None, None), ([], []), ([1, "2", 3.0], [1, 2, 3]), ("12", [12]), (5, [5])],
)
def test_coerce_optional_int_ids(value, expected):
    assert _coerce_optional_int_ids(value, "project_ids") == expected


@pytest.mark.parametrize("value", [[True], [1.5], ["x"], [[1]]])
def test_coerce_optional_int_ids_rejects_invalid_items(value):
    with pytest.raises(ValueError, match="project_ids"):
        _coerce_optional_int_ids(value, "project_ids")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ("adr", ["adr"]),
        (["adr", "api"], ["adr", "api"]),
        (("adr",), ["adr"]),
        ([], []),
    ],
)
def test_coerce_str_list(value, expected):
    assert _coerce_str_list(value, "tags") == expected


@pytest.mark.parametrize("value", [5, {"adr": 1}, [1], ["adr", None], True])
def test_coerce_str_list_rejects_non_string_values(value):
    with pytest.raises(ValueError, match="tags"):
        _coerce_str_list(value, "tags")
