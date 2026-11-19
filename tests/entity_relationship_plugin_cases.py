"""The same Entity Relationship Plugin persistence contracts run on native SQLite and PostgreSQL."""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.bootstrap import create_repositories
from app.exceptions import NotFoundError, WritePluginRejectedError
from app.models.entity_models import (
    EntityCreate,
    EntityRelationshipCreate,
    EntityRelationshipUpdate,
    EntityType,
)
from app.models.user_models import UserCreate
from app.models.write_plugin_models import PluginWarning, WriteDecision
from app.protocols.write_plugin_protocol import EntityRelationshipPlugin
from app.services.entity_relationship_plugin_service import (
    EntityRelationshipPluginService,
)
from app.services.entity_service import EntityService


@pytest.fixture
async def relationship_store(reference_db):
    repos = create_repositories(reference_db, None, None)
    users = []
    for label in ("owner", "other"):
        key = uuid4().hex
        users.append(await repos["user"].create_user(UserCreate(
            external_id=f"relationship-policy-{label}-{key}", name=f"Synthetic {label}",
            email=f"{key}@example.test",
        )))
    state = SimpleNamespace(before=[], after=[], decision="allow")

    async def before(context):
        state.before.append(context.model_copy(deep=True))
        return WriteDecision(
            outcome=state.decision, message="Synthetic relationship policy", code="REL_TEST",
        )

    async def after(context):
        state.after.append(context.model_copy(deep=True))
        return PluginWarning(message="Synthetic after warning", code="REL_AFTER")

    plugin = EntityRelationshipPlugin(
        before_save=dict.fromkeys(("create", "update", "delete"), before),
        after_save=dict.fromkeys(("create", "update", "delete"), after),
    )
    service = EntityService(
        repos["entity"], relationship_plugin=EntityRelationshipPluginService(plugin),
    )

    async def entity(name, entity_type=EntityType.INDIVIDUAL, user=None):
        user = user or users[0]
        result = await service.create_entity(user.id, EntityCreate(
            name=name, entity_type=entity_type, tags=[],
        ))
        return result.entity

    yield SimpleNamespace(
        repo=repos["entity"], user=users[0], other=users[1], state=state,
        service=service, entity=entity,
    )


async def linked(store, **changes):
    person = await store.entity("Synthetic Person")
    org = await store.entity("Synthetic Org", EntityType.ORGANIZATION)
    data = {
        "source_entity_id": person.id, "target_entity_id": org.id,
        "relationship_type": "works_for", "strength": 0.5,
    } | changes
    result = await store.service.create_entity_relationship(
        store.user.id, EntityRelationshipCreate(**data),
    )
    store.state.before.clear()
    store.state.after.clear()
    return person, org, result.relationship


class TestEntityRelationshipPluginPersistence:
    async def test_create_contexts_include_owned_endpoints(self, relationship_store):
        store = relationship_store
        person = await store.entity("Synthetic Person")
        org = await store.entity("Synthetic Org", EntityType.ORGANIZATION)

        result = await store.service.create_entity_relationship(
            store.user.id, EntityRelationshipCreate(
                source_entity_id=person.id, target_entity_id=org.id,
                relationship_type="works_for", metadata={"role": "engineer"},
            ),
        )

        before = store.state.before[0]
        assert before.operation == "create"
        assert before.user_id == store.user.id
        assert before.previous is None
        assert before.proposed.relationship_type == "works_for"
        assert (before.source.id, before.source.entity_type) == (person.id, EntityType.INDIVIDUAL)
        assert (before.target.id, before.target.entity_type) == (org.id, EntityType.ORGANIZATION)
        after = store.state.after[0]
        assert after.saved.id == result.relationship.id
        assert after.saved.metadata == {"role": "engineer"}
        assert [warning.code for warning in result.plugin_warnings] == ["REL_AFTER"]

    async def test_reject_create_persists_nothing(self, relationship_store):
        store = relationship_store
        person = await store.entity("Synthetic Person")
        org = await store.entity("Synthetic Org", EntityType.ORGANIZATION)
        store.state.decision = "reject"

        with pytest.raises(WritePluginRejectedError, match="Synthetic relationship policy"):
            await store.service.create_entity_relationship(
                store.user.id, EntityRelationshipCreate(
                    source_entity_id=person.id, target_entity_id=org.id,
                    relationship_type="works_for",
                ),
            )

        assert await store.repo.get_all_entity_relationships(store.user.id) == []
        assert store.state.after == []

    async def test_other_users_endpoint_fails_before_policy(self, relationship_store):
        store = relationship_store
        person = await store.entity("Synthetic Person")
        foreign = await store.entity("Foreign Org", EntityType.ORGANIZATION, user=store.other)

        with pytest.raises(NotFoundError, match="Target entity"):
            await store.service.create_entity_relationship(
                store.user.id, EntityRelationshipCreate(
                    source_entity_id=person.id, target_entity_id=foreign.id,
                    relationship_type="works_for",
                ),
            )

        assert store.state.before == []
        assert await store.repo.get_all_entity_relationships(store.user.id) == []

    async def test_update_contexts_and_noop_skip(self, relationship_store):
        store = relationship_store
        _, org, relationship = await linked(store)

        result = await store.service.update_entity_relationship(
            store.user.id, relationship.id, EntityRelationshipUpdate(strength=0.9),
        )

        before = store.state.before[0]
        assert before.previous.strength == 0.5
        assert before.proposed.strength == 0.9
        assert before.proposed.relationship_type == "works_for"
        assert before.target.id == org.id
        after = store.state.after[0]
        assert (after.previous.strength, after.saved.strength) == (0.5, 0.9)
        assert result.relationship.strength == 0.9

        store.state.before.clear()
        store.state.after.clear()
        unchanged = await store.service.update_entity_relationship(
            store.user.id, relationship.id, EntityRelationshipUpdate(strength=0.9),
        )
        assert unchanged.relationship.strength == 0.9
        assert unchanged.plugin_warnings == []
        assert (store.state.before, store.state.after) == ([], [])

    async def test_reject_update_and_delete_keep_stored_relationship(self, relationship_store):
        store = relationship_store
        _, _, relationship = await linked(store)
        store.state.decision = "reject"

        with pytest.raises(WritePluginRejectedError):
            await store.service.update_entity_relationship(
                store.user.id, relationship.id, EntityRelationshipUpdate(strength=0.1),
            )
        with pytest.raises(WritePluginRejectedError):
            await store.service.delete_entity_relationship(store.user.id, relationship.id)

        stored = await store.repo.get_entity_relationship_by_id(store.user.id, relationship.id)
        assert stored.strength == 0.5
        assert store.state.after == []

    async def test_delete_contexts_describe_removed_relationship(self, relationship_store):
        store = relationship_store
        person, _, relationship = await linked(store)

        result = await store.service.delete_entity_relationship(store.user.id, relationship.id)

        assert result.deleted is True
        before = store.state.before[0]
        assert before.submitted.relationship_id == relationship.id
        assert before.proposed is None
        after = store.state.after[0]
        assert after.deleted_relationship_id == relationship.id
        assert after.previous.relationship_type == "works_for"
        assert after.source.id == person.id
        assert not hasattr(after, "saved")
        assert await store.repo.get_entity_relationship_by_id(store.user.id, relationship.id) is None

    async def test_missing_or_foreign_relationship_skips_both_phases(self, relationship_store):
        store = relationship_store
        _, _, relationship = await linked(store)

        foreign = await store.service.delete_entity_relationship(store.other.id, relationship.id)
        missing = await store.service.delete_entity_relationship(store.user.id, relationship.id + 999)
        with pytest.raises(NotFoundError):
            await store.service.update_entity_relationship(
                store.other.id, relationship.id, EntityRelationshipUpdate(strength=0.1),
            )

        assert (foreign.deleted, missing.deleted) == (False, False)
        assert (store.state.before, store.state.after) == ([], [])
        assert await store.repo.get_entity_relationship_by_id(store.other.id, relationship.id) is None
        assert await store.repo.get_entity_relationship_by_id(store.user.id, relationship.id)

    async def test_entity_delete_cascade_does_not_call_relationship_hooks(self, relationship_store):
        store = relationship_store
        person, _, relationship = await linked(store)

        assert (await store.service.delete_entity(store.user.id, person.id)).deleted is True

        assert await store.repo.get_entity_relationship_by_id(store.user.id, relationship.id) is None
        assert (store.state.before, store.state.after) == ([], [])
