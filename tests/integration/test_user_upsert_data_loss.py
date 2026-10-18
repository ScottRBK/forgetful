"""Regression tests for user provisioning on login.

An IdP name/email change used to overwrite ``notes`` and ``idp_metadata``
with NULL because the whole ``UserCreate`` was re-sent as a ``UserUpdate``.
"""
import pytest

from app.models.user_models import UserCreate, UserUpdate


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
