"""User creation behaviour shared by the real SQLite and PostgreSQL tests."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.exceptions import ConflictError
from app.models.user_models import UserCreate, UserUpdate
from app.services.user_service import UserService


class UserCreationCases:
    async def test_other_insert_errors_are_not_reported_as_duplicates(self, user_repository):
        # Bypass model validation to reach a different real database constraint (NOT NULL).
        invalid = UserCreate.model_construct(
            external_id="invalid", name=None, email="a@example.com",
        )

        with pytest.raises(IntegrityError):
            await user_repository.create_user(invalid)

        assert await user_repository.get_user_by_external_id("invalid") is None

    async def test_duplicate_creation_preserves_existing_user(self, user_repository):
        user = UserCreate(external_id="duplicate", name="Original", email="original@example.com")
        existing = await user_repository.create_user(user)

        with pytest.raises(ConflictError):
            await user_repository.create_user(user.model_copy(update={"name": "Replacement"}))

        assert await user_repository.get_user_by_external_id(user.external_id) == existing
        # A failed insert must not leave the repository unusable.
        other = await user_repository.create_user(user.model_copy(update={"external_id": "other"}))
        assert other.id != existing.id

    @pytest.mark.parametrize("operation", ["get_or_create_user", "update_user"])
    async def test_creation_race_returns_existing_user(
        self, user_repository, monkeypatch, operation,
    ):
        user = UserCreate(external_id="racing", name="Winner", email="winner@example.com")
        service = UserService(user_repository)
        original_get = user_repository.get_user_by_external_id
        winner = None

        async def lookup_with_competing_insert(external_id):
            nonlocal winner
            result = await original_get(external_id)
            if winner is None:
                assert result is None
                # Another request commits after this lookup but before the service's insert.
                # The service's INSERT and the database's duplicate error are both real.
                winner = await user_repository.create_user(user)
            return result

        monkeypatch.setattr(
            user_repository, "get_user_by_external_id", lookup_with_competing_insert,
        )
        request = user if operation == "get_or_create_user" else UserUpdate(**user.model_dump())

        result = await getattr(service, operation)(request)

        assert winner is not None
        assert result == winner
        assert await original_get(user.external_id) == winner
