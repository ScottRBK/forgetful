"""Plan external reference contracts against PostgreSQL."""

import pytest

from tests.plan_external_ref_cases import (
    TestPlanExternalRefAPI as TestPlanExternalRefAPI,
)
from tests.plan_external_ref_cases import (
    TestPlanExternalRefMCP as TestPlanExternalRefMCP,
)
from tests.plan_external_ref_cases import (
    TestPlanExternalRefStorage as TestPlanExternalRefStorage,
)
from tests.plan_external_ref_cases import reference_store as reference_store

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio(loop_scope="session")]


@pytest.fixture
def reference_db(db_adapter):
    return db_adapter
