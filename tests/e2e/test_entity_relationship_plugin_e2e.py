"""Identical Entity Relationship Plugin contracts on native PostgreSQL."""

import pytest

from tests.entity_relationship_plugin_cases import (
    TestEntityRelationshipPluginPersistence as TestEntityRelationshipPluginPersistence,
)
from tests.entity_relationship_plugin_cases import (
    relationship_store as relationship_store,
)

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio(loop_scope="session")]


@pytest.fixture
def reference_db(db_adapter):
    return db_adapter
