"""E2E tests for explicit nulls in REST PUT bodies (in-memory SQLite).

Every update model documents "Unchanged if null". A client that sends
``{"tags": null}`` (for example a form that serialises a cleared field as null)
must not damage the record: on SQLite a null list column used to be stored as
JSON ``null`` and the record could no longer be read, updated or deleted, and
NOT NULL columns raised ``IntegrityError`` (HTTP 500).
"""
import base64
from dataclasses import dataclass

import pytest

from app.config.settings import settings


class CountingEmbeddingAdapter:
    """Deterministic embedder that records how often it is asked to embed."""

    def __init__(self):
        self.calls = 0

    async def generate_embedding(self, text: str) -> list[float]:
        assert isinstance(text, str), f"embedding requested for {text!r}"
        self.calls += 1
        return [0.01] * settings.EMBEDDING_DIMENSIONS


@pytest.fixture(scope="module")
def embedding_adapter():
    return CountingEmbeddingAdapter()


@pytest.fixture(scope="module")
def reranker_adapter():
    return None


@dataclass(frozen=True)
class Resource:
    name: str
    base: str
    payload: dict
    # Fields that must ignore an explicit null.
    null_fields: tuple[str, ...]
    # A field and its current value: repeating it changes nothing.
    same_field: str


RESOURCES = [
    Resource(
        name="project",
        base="/api/v1/projects",
        payload={
            "name": "Proj",
            "description": "A project",
            "project_type": "development",
            "notes": "keep me",
            "repo_name": "github.com/example/proj",
        },
        null_fields=(
            "name", "description", "project_type", "status", "notes", "repo_name", "last_encoding_point",
        ),
        same_field="name",
    ),
    Resource(
        name="document",
        base="/api/v1/documents",
        payload={
            "title": "Doc",
            "description": "A document",
            "content": "Some document content that is long enough.",
            "document_type": "analysis",
            "tags": ["a", "b"],
            "source_url": "https://example.test/x",
        },
        null_fields=(
            "title", "description", "content", "document_type", "size_bytes", "tags", "source_url",
        ),
        same_field="title",
    ),
    Resource(
        name="code_artifact",
        base="/api/v1/code-artifacts",
        payload={
            "title": "Snippet",
            "description": "A snippet",
            "code": "def hello():\n    return 1",
            "language": "python",
            "tags": ["a", "b"],
        },
        null_fields=("title", "description", "code", "language", "tags"),
        same_field="title",
    ),
    Resource(
        name="file",
        base="/api/v1/files",
        payload={
            "filename": "t.txt",
            "description": "A text file",
            "data": base64.b64encode(b"Hello, World!").decode(),
            "mime_type": "text/plain",
            "tags": ["a", "b"],
        },
        null_fields=("filename", "description", "data", "mime_type", "tags"),
        same_field="filename",
    ),
    Resource(
        name="entity",
        base="/api/v1/entities",
        payload={
            "name": "Ent",
            "entity_type": "Individual",
            "notes": "keep me",
            "tags": ["a", "b"],
            "aka": ["x"],
        },
        null_fields=("name", "entity_type", "notes", "tags", "aka"),
        same_field="name",
    ),
    Resource(
        name="skill",
        base="/api/v1/skills",
        payload={
            "name": "null-patch-skill",
            "description": "Original description",
            "content": "# Original content",
            "license": "MIT",
            "compatibility": "claude-code",
            "tags": ["keep"],
            "importance": 6,
        },
        null_fields=(
            "name", "description", "content", "license", "compatibility", "tags", "importance",
        ),
        same_field="name",
    ),
]

FIELD_CASES = [
    pytest.param(resource, field, id=f"{resource.name}-{field}")
    for resource in RESOURCES
    for field in resource.null_fields
]


async def _create(http_client, resource):
    response = await http_client.post(resource.base, json=resource.payload)
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _get(http_client, resource, resource_id):
    response = await http_client.get(f"{resource.base}/{resource_id}")
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize(("resource", "field"), FIELD_CASES)
async def test_put_null_field_is_ignored(http_client, resource, field):
    """PUT {field: null} succeeds, changes nothing and leaves the record usable."""
    resource_id = await _create(http_client, resource)
    before = await _get(http_client, resource, resource_id)

    response = await http_client.put(f"{resource.base}/{resource_id}", json={field: None})

    assert response.status_code == 200, response.text
    assert await _get(http_client, resource, resource_id) == before
    assert (await http_client.get(resource.base)).status_code == 200
    deleted = await http_client.delete(f"{resource.base}/{resource_id}")
    assert deleted.status_code == 200, deleted.text


@pytest.mark.parametrize("resource", RESOURCES, ids=lambda resource: resource.name)
async def test_put_all_nulls_changes_nothing(http_client, resource):
    resource_id = await _create(http_client, resource)
    before = await _get(http_client, resource, resource_id)

    response = await http_client.put(
        f"{resource.base}/{resource_id}", json=dict.fromkeys(resource.null_fields),
    )

    assert response.status_code == 200, response.text
    assert await _get(http_client, resource, resource_id) == before


@pytest.mark.parametrize("resource", RESOURCES, ids=lambda resource: resource.name)
async def test_put_value_next_to_null_applies_only_the_value(http_client, resource):
    resource_id = await _create(http_client, resource)
    before = await _get(http_client, resource, resource_id)
    other_nulls = [field for field in resource.null_fields if field != resource.same_field]
    new_value = "Renamed" if resource.name != "file" else "renamed.txt"
    if resource.name == "skill":
        new_value = "renamed-skill"
    body = {**dict.fromkeys(other_nulls), resource.same_field: new_value}

    response = await http_client.put(f"{resource.base}/{resource_id}", json=body)

    assert response.status_code == 200, response.text
    after = await _get(http_client, resource, resource_id)
    assert after[resource.same_field] == new_value
    for field in other_nulls:
        assert after[field] == before[field], f"{field} changed"


@pytest.mark.parametrize(
    ("resource_name", "field"),
    [("project", "notes"), ("project", "repo_name"), ("entity", "notes"), ("document", "filename")],
)
async def test_empty_string_still_clears_optional_field(http_client, resource_name, field):
    """Null is ignored, but the documented way to clear a field keeps working."""
    resource = next(item for item in RESOURCES if item.name == resource_name)
    payload = {**resource.payload, field: "some value"}
    created = await http_client.post(resource.base, json=payload)
    assert created.status_code == 201, created.text
    resource_id = created.json()["id"]

    response = await http_client.put(f"{resource.base}/{resource_id}", json={field: ""})

    assert response.status_code == 200, response.text
    assert (await _get(http_client, resource, resource_id))[field] is None


async def test_put_null_strength_keeps_relationship_value(http_client):
    source = (await http_client.post("/api/v1/entities", json={
        "name": "Source", "entity_type": "Organization",
    })).json()["id"]
    target = (await http_client.post("/api/v1/entities", json={
        "name": "Target", "entity_type": "Team",
    })).json()["id"]
    created = await http_client.post(f"/api/v1/entities/{source}/relationships", json={
        "target_entity_id": target, "relationship_type": "manages", "strength": 0.7, "confidence": 0.9,
    })
    assert created.status_code == 201, created.text
    relationship_id = created.json()["id"]

    response = await http_client.put(
        f"/api/v1/entities/relationships/{relationship_id}",
        json={"relationship_type": None, "strength": None, "confidence": None, "metadata": None},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["relationship_type"] == "manages"
    assert body["strength"] == 0.7
    assert body["confidence"] == 0.9
    listed = (await http_client.get(f"/api/v1/entities/{source}/relationships")).json()
    assert [item["strength"] for item in listed["relationships"]] == [0.7]


async def test_skill_null_description_is_not_re_embedded(http_client, embedding_adapter):
    skill = next(item for item in RESOURCES if item.name == "skill")
    skill_id = await _create(http_client, skill)
    calls = embedding_adapter.calls

    response = await http_client.put(f"{skill.base}/{skill_id}", json={"description": None})

    assert response.status_code == 200, response.text
    assert embedding_adapter.calls == calls


# ---------------------------------------------------------------------------
# Updates that change nothing do not touch the record
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("resource", RESOURCES, ids=lambda resource: resource.name)
async def test_put_without_changes_keeps_updated_at(http_client, resource):
    resource_id = await _create(http_client, resource)
    before = await _get(http_client, resource, resource_id)

    same = await http_client.put(
        f"{resource.base}/{resource_id}",
        json={resource.same_field: resource.payload[resource.same_field]},
    )
    empty = await http_client.put(f"{resource.base}/{resource_id}", json={})

    assert same.status_code == 200, same.text
    assert empty.status_code == 200, empty.text
    assert (await _get(http_client, resource, resource_id))["updated_at"] == before["updated_at"]


async def test_skill_unchanged_description_is_not_re_embedded(http_client, embedding_adapter):
    skill = next(item for item in RESOURCES if item.name == "skill")
    skill_id = await _create(http_client, skill)
    calls = embedding_adapter.calls

    same = await http_client.put(
        f"{skill.base}/{skill_id}", json={"description": skill.payload["description"]},
    )

    assert same.status_code == 200, same.text
    assert embedding_adapter.calls == calls

    changed = await http_client.put(f"{skill.base}/{skill_id}", json={"description": "Something new"})

    assert changed.status_code == 200, changed.text
    assert embedding_adapter.calls == calls + 1
