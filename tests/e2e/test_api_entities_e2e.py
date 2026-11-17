"""PostgreSQL E2E coverage for the entity REST API list contract."""

import pytest

from tests.entity_list_cases import TestEntityListContract as TestEntityListContract

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio(loop_scope="session")]
