"""Document Plugin bootstrap loading."""


import pytest

from app.bootstrap import build_runtime, dispose_runtime
from app.config.settings import settings
from app.models.document_models import DocumentCreate
from app.models.user_models import UserCreate


async def test_document_plugin_rejects_blocked_tag(document_plugin_runtime):
    from app.exceptions import WritePluginRejectedError

    runtime = await build_runtime()
    try:
        user = await runtime.services.user.get_or_create_user(UserCreate(
            external_id=settings.DEFAULT_USER_ID, name=settings.DEFAULT_USER_NAME,
            email=settings.DEFAULT_USER_EMAIL,
        ))
        await runtime.services.document.create_document(user.id, DocumentCreate(
            title="Allowed", description="d", content="c", tags=[],
        ))
        with pytest.raises(WritePluginRejectedError, match="Remove the blocked tag"):
            await runtime.services.document.create_document(user.id, DocumentCreate(
                title="Blocked", description="d", content="c", tags=["blocked"],
            ))
    finally:
        await dispose_runtime(runtime)


@pytest.mark.parametrize("reference", ["missing_plugin:plugin", "runtime_document_checks:decide"])
async def test_invalid_document_reference_fails_startup(document_plugin_runtime, monkeypatch, reference):
    monkeypatch.setattr(settings, "DOCUMENT_WRITE_PLUGIN", reference)
    with pytest.raises(ValueError, match="DOCUMENT_WRITE_PLUGIN"):
        await build_runtime()


def test_registration_validates_the_mapping_it_keeps():
    from app.protocols.write_plugin_protocol import DocumentPlugin

    async def after(request):
        return None

    class StaleItems(dict):
        def items(self):
            return {"create": after}.items()

    handlers = StaleItems(create=lambda request: None)

    with pytest.raises(ValueError, match="after_save handlers must be async functions"):
        DocumentPlugin(after_save=handlers)
