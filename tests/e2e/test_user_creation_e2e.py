"""User creation and duplicate recovery against real PostgreSQL."""

import pytest

from app.repositories.postgres.user_repository import PostgresUserRepository
from tests.user_creation_cases import UserCreationCases

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio(loop_scope="session")]


@pytest.fixture
def user_repository(db_adapter, clean_database):
    return PostgresUserRepository(db_adapter)


class TestPostgresUserCreation(UserCreationCases):
    pass
