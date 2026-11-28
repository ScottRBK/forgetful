"""The identical seven-resource contract on the isolated native PostgreSQL fixture."""
import pytest

from tests.list_pagination_cases import (
    FixedPaginationEmbeddings,
    PaginationCases,
    PaginationEnvironment,
)
from tests.list_pagination_compatibility_cases import PaginationCompatibilityCases

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio(loop_scope="session")]


@pytest.fixture(scope="module")
def embedding_adapter():
    return FixedPaginationEmbeddings()


@pytest.fixture(scope="module")
def reranker_adapter():
    return None


@pytest.fixture
def pagination_environment(http_client, postgres_app):
    return PaginationEnvironment(http_client, postgres_app, "Postgres")


class TestPostgresListPagination(PaginationCases, PaginationCompatibilityCases):
    pass
