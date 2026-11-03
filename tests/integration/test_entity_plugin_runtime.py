"""Entity Plugin bootstrap loading."""


import pytest

from app.bootstrap import build_runtime, dispose_runtime
from app.config.settings import settings
from app.models.entity_models import EntityCreate, EntityType
from app.models.user_models import UserCreate


async def test_entity_plugin_rejects_blocked_tag(entity_plugin_runtime):
    from app.exceptions import WritePluginRejectedError

    runtime = await build_runtime()
    try:
        user = await runtime.services.user.get_or_create_user(UserCreate(
            external_id=settings.DEFAULT_USER_ID, name=settings.DEFAULT_USER_NAME,
            email=settings.DEFAULT_USER_EMAIL,
        ))
        await runtime.services.entity.create_entity(user.id, EntityCreate(
            name="Allowed", entity_type=EntityType.ORGANIZATION, tags=[],
        ))
        with pytest.raises(WritePluginRejectedError, match="Remove the blocked tag"):
            await runtime.services.entity.create_entity(user.id, EntityCreate(
                name="Blocked", entity_type=EntityType.ORGANIZATION, tags=["blocked"],
            ))
    finally:
        await dispose_runtime(runtime)


@pytest.mark.parametrize("reference", ["missing_plugin:plugin", "runtime_entity_checks:decide"])
async def test_invalid_entity_reference_fails_startup(entity_plugin_runtime, monkeypatch, reference):
    monkeypatch.setattr(settings, "ENTITY_WRITE_PLUGIN", reference)
    with pytest.raises(ValueError, match="ENTITY_WRITE_PLUGIN"):
        await build_runtime()


def test_registration_validates_the_mapping_it_keeps():
    from app.protocols.write_plugin_protocol import EntityPlugin

    async def after(request):
        return None

    class StaleItems(dict):
        def items(self):
            return {"create": after}.items()

    handlers = StaleItems(create=lambda request: None)

    with pytest.raises(ValueError, match="after_save handlers must be async functions"):
        EntityPlugin(after_save=handlers)
