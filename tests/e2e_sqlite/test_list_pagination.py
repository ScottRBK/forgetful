"""Complete pagination and full-client regressions using real SQLite fixtures."""
import pytest

from tests.list_pagination_cases import (
    FixedPaginationEmbeddings,
    PaginationCases,
    PaginationEnvironment,
)
from tests.list_pagination_compatibility_cases import PaginationCompatibilityCases


@pytest.fixture(scope="module")
def embedding_adapter():
    return FixedPaginationEmbeddings()


@pytest.fixture(scope="module")
def reranker_adapter():
    return None


@pytest.fixture
def pagination_environment(http_client, sqlite_app):
    return PaginationEnvironment(http_client, sqlite_app, "SQLite")


class TestSQLiteListPagination(PaginationCases, PaginationCompatibilityCases):
    pass
