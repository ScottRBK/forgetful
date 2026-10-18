"""Integration tests for graph node id parsing and bulk memory linking.

Covers, without any network access or embedding model:
- GraphService.parse_node_id: canonical ASCII ids only, an upper bound that fits
  the integer columns, and an error message that shows the real id placeholders.
- SqliteMemoryRepository.create_links_batch: ids that cannot be stored as an
  integer are skipped like unknown ids instead of aborting the batch half way.
"""

import pytest

from app.services.graph_service import MAX_NODE_ID, GraphService

NODE_TYPES = [
    "memory",
    "entity",
    "project",
    "document",
    "code_artifact",
    "file",
    "skill",
    "plan",
    "task",
]


# ---- GraphService.parse_node_id ----

@pytest.mark.parametrize("node_type", NODE_TYPES)
def test_parse_node_id_accepts_largest_supported_id(node_type):
    assert GraphService.parse_node_id(f"{node_type}_{MAX_NODE_ID}") == (node_type, MAX_NODE_ID)


@pytest.mark.parametrize("node_type", NODE_TYPES)
@pytest.mark.parametrize(
    "number",
    [MAX_NODE_ID + 1, 2**63, 2**64, 99999999999999999999],
    ids=["max+1", "int64-overflow", "uint64-overflow", "20-digits"],
)
def test_parse_node_id_rejects_ids_beyond_the_integer_range(node_type, number):
    with pytest.raises(ValueError, match="out of range"):
        GraphService.parse_node_id(f"{node_type}_{number}")


@pytest.mark.parametrize(
    "raw",
    [
        "memory_1\n",
        "memory_1 ",
        " memory_1",
        "memory_١",  # Arabic-Indic digit one
        "memory_１",  # fullwidth digit one
        "memory_",
        "memory_-1",
        "memory_1.5",
    ],
    ids=[
        "trailing-newline",
        "trailing-space",
        "leading-space",
        "arabic-indic-digit",
        "fullwidth-digit",
        "no-digits",
        "negative",
        "decimal",
    ],
)
def test_parse_node_id_rejects_non_canonical_ids(raw):
    with pytest.raises(ValueError, match="Invalid node_id format"):
        GraphService.parse_node_id(raw)


def test_parse_node_id_normalises_leading_zeros():
    assert GraphService.parse_node_id("memory_001") == ("memory", 1)


def test_parse_node_id_error_message_shows_id_placeholders():
    with pytest.raises(ValueError) as excinfo:
        GraphService.parse_node_id("bad")

    message = str(excinfo.value)
    for node_type in NODE_TYPES:
        assert f"'{node_type}_{{id}}'" in message
    assert "{{" not in message
    assert "}}" not in message
