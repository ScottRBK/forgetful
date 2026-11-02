"""Identical Plan policy contracts on native PostgreSQL."""

import pytest

from tests.plan_plugin_cases import (
    TestPlanPluginPersistence as TestPlanPluginPersistence,
)
from tests.plan_plugin_cases import plan_store as plan_store

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio(loop_scope="session")]


@pytest.fixture
def reference_db(db_adapter):
    return db_adapter
