"""Regression tests for user provisioning on login.

Covers two defects in the identity upsert path:

* An IdP name/email change used to overwrite ``notes`` and ``idp_metadata``
  with NULL because the whole ``UserCreate`` was re-sent as a ``UserUpdate``.
* ``external_id``/``name``/``email`` are VARCHAR(255) columns but the models
  accepted any length, so oversize values failed on PostgreSQL and were
  silently stored on SQLite.
"""
import pytest
from pydantic import ValidationError

from app.models.user_models import User, UserCreate, UserUpdate

IDENTITY_FIELDS = ("external_id", "name", "email")


@pytest.mark.asyncio
async def test_name_change_on_login_keeps_notes(test_user_service):
    """The auth middleware sends only external_id/name/email, so notes must survive."""
    await test_user_service.get_or_create_user(
        UserCreate(external_id="sub-notes", name="Old Name", email="a@example.com"),
    )
    await test_user_service.update_user(
        UserUpdate(external_id="sub-notes", notes="I prefer tabs"),
    )

    after = await test_user_service.get_or_create_user(
        UserCreate(external_id="sub-notes", name="New Name", email="a@example.com"),
    )

    assert after.name == "New Name"
    assert after.notes == "I prefer tabs"


@pytest.mark.asyncio
async def test_email_change_on_login_keeps_idp_metadata(test_user_service):
    """Changing only the email claim must not clear stored IdP metadata."""
    await test_user_service.get_or_create_user(
        UserCreate(
            external_id="sub-meta",
            name="Name",
            email="a@example.com",
            idp_metadata={"groups": ["admin"]},
        ),
    )

    after = await test_user_service.get_or_create_user(
        UserCreate(external_id="sub-meta", name="Name", email="b@example.com"),
    )

    assert after.email == "b@example.com"
    assert after.idp_metadata == {"groups": ["admin"]}


@pytest.mark.asyncio
async def test_login_update_only_sends_fields_the_caller_set(test_user_service):
    """The update handed to the repository must not carry fields the caller never set."""
    repo = test_user_service.user_repo
    await test_user_service.get_or_create_user(
        UserCreate(external_id="sub-fields", name="Old", email="a@example.com"),
    )
    sent: list[UserUpdate] = []
    original_update = repo.update_user

    async def recording_update(user_id, updated_user):
        sent.append(updated_user)
        return await original_update(user_id=user_id, updated_user=updated_user)

    repo.update_user = recording_update

    await test_user_service.get_or_create_user(
        UserCreate(external_id="sub-fields", name="New", email="a@example.com"),
    )

    assert len(sent) == 1
    assert sent[0].model_fields_set <= {"external_id", "name", "email"}
    assert sent[0].name == "New"


@pytest.mark.asyncio
async def test_explicit_notes_in_login_are_still_applied(test_user_service):
    """A caller that does set notes/idp_metadata keeps the ability to change them."""
    await test_user_service.get_or_create_user(
        UserCreate(external_id="sub-explicit", name="Name", email="a@example.com"),
    )

    after = await test_user_service.get_or_create_user(
        UserCreate(
            external_id="sub-explicit",
            name="Name",
            email="a@example.com",
            notes="set by caller",
            idp_metadata={"tier": "pro"},
        ),
    )

    assert after.notes == "set by caller"
    assert after.idp_metadata == {"tier": "pro"}


@pytest.mark.parametrize("field", IDENTITY_FIELDS)
@pytest.mark.parametrize("model", [UserCreate, UserUpdate])
def test_identity_fields_reject_values_longer_than_the_column(model, field):
    """Values beyond VARCHAR(255) are rejected up front with a clear validation error."""
    values = {"external_id": "sub", "name": "Name", "email": "a@example.com"}
    values[field] = "x" * 256

    with pytest.raises(ValidationError) as exc_info:
        model(**values)

    assert field in str(exc_info.value)


@pytest.mark.parametrize("field", IDENTITY_FIELDS)
@pytest.mark.parametrize("model", [UserCreate, UserUpdate])
def test_identity_fields_accept_values_exactly_at_the_column_limit(model, field):
    values = {"external_id": "sub", "name": "Name", "email": "a@example.com"}
    values[field] = "x" * 255

    assert getattr(model(**values), field) == "x" * 255


@pytest.mark.asyncio
async def test_oversize_identity_is_rejected_before_reaching_the_repository(
    test_user_service,
):
    """Provisioning never reaches the database with a value that cannot fit."""
    with pytest.raises(ValueError):
        await test_user_service.get_or_create_user(
            UserCreate(external_id="sub-long", name="n" * 300, email="a@example.com"),
        )

    assert await test_user_service.user_repo.get_user_by_external_id("sub-long") is None


def test_user_read_model_still_loads_legacy_oversize_rows():
    """SQLite ignores VARCHAR(255), so rows written earlier may be longer than that.

    Reading them back must keep working; only new input is bounded.
    """
    legacy = User(external_id="s" * 300, name="n" * 300, email="e" * 300)

    assert len(legacy.external_id) == 300
    assert len(legacy.name) == 300
    assert len(legacy.email) == 300
