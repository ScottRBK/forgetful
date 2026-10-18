"""SQLite E2E tests: referenced projects must belong to the caller.

Documents, code artifacts, files, plans and skills accepted any ``project_id``.
The foreign key only checks that the id exists, so a user could attach rows to
another user's project (and the project owner's later delete then rewrote or
cascade-deleted those rows), and an unused id surfaced as a raw
``FOREIGN KEY constraint failed`` 500.

The REST surface is exercised with two users (full stack).
"""
import base64
from contextlib import contextmanager

import pytest

from app.config.settings import settings

UNKNOWN_PROJECT_ID = 424_242
FILE_DATA = base64.b64encode(b"Hello, World!").decode("utf-8")

# kind -> (collection url, list key, payload builder taking project_id)
CREATE_CASES = {
    "documents": (
        "/api/v1/documents",
        "documents",
        lambda pid: {
            "title": "Linked document",
            "description": "Document with a project link",
            "content": "Document body with enough text to be valid.",
            "project_id": pid,
        },
    ),
    "code-artifacts": (
        "/api/v1/code-artifacts",
        "code_artifacts",
        lambda pid: {
            "title": "Linked artifact",
            "description": "Artifact with a project link",
            "code": "print('hello')",
            "language": "python",
            "project_id": pid,
        },
    ),
    "files": (
        "/api/v1/files",
        "files",
        lambda pid: {
            "filename": "linked.txt",
            "description": "File with a project link",
            "data": FILE_DATA,
            "mime_type": "text/plain",
            "project_id": pid,
        },
    ),
    "plans": (
        "/api/v1/plans",
        "plans",
        lambda pid: {"title": "Linked plan", "project_id": pid},
    ),
    "skills": (
        "/api/v1/skills",
        "skills",
        lambda pid: {
            "name": "linked-skill",
            "description": "Skill with a project link",
            "content": "# Linked skill\n\n1. Do the thing",
            "project_id": pid,
        },
    ),
}
UPDATE_KINDS = ["documents", "code-artifacts", "files", "skills"]


@contextmanager
def acting_as(monkeypatch, name: str):
    """Run REST calls as another user (the test app has no auth, so identity is a setting)."""
    with monkeypatch.context() as patch:
        patch.setattr(settings, "DEFAULT_USER_ID", f"ref-check-{name}")
        patch.setattr(settings, "DEFAULT_USER_EMAIL", f"ref-check-{name}@example.test")
        yield


async def _create_project(http_client, name: str) -> int:
    response = await http_client.post("/api/v1/projects", json={
        "name": name,
        "description": f"{name} description",
        "project_type": "development",
    })
    assert response.status_code == 201
    return response.json()["id"]


async def _create(http_client, kind: str, project_id: int | None):
    url, _, build = CREATE_CASES[kind]
    return await http_client.post(url, json=build(project_id))


async def _count(http_client, kind: str) -> int:
    url, key, _ = CREATE_CASES[kind]
    response = await http_client.get(url)
    assert response.status_code == 200
    return len(response.json()[key])


# ============================================================================
# REST surface, two users
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", list(CREATE_CASES))
async def test_create_rejects_other_users_project(http_client, monkeypatch, kind):
    """A foreign project id is reported as not found and nothing is stored."""
    alice_project = await _create_project(http_client, "Alice private")

    with acting_as(monkeypatch, "bob"):
        response = await _create(http_client, kind, alice_project)

        assert response.status_code == 404
        assert "not found" in response.json()["error"].lower()
        assert await _count(http_client, kind) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", list(CREATE_CASES))
async def test_create_unknown_project_is_not_found(http_client, kind):
    """An unused project id is a clean 404, not a raw foreign-key error."""
    response = await _create(http_client, kind, UNKNOWN_PROJECT_ID)

    assert response.status_code == 404
    assert "FOREIGN KEY" not in response.text
    assert await _count(http_client, kind) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", list(CREATE_CASES))
async def test_create_with_own_project_still_works(http_client, kind):
    """The owner can still attach rows to their own project."""
    project_id = await _create_project(http_client, "Alice own")

    response = await _create(http_client, kind, project_id)

    assert response.status_code == 201
    assert response.json()["project_id"] == project_id


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", UPDATE_KINDS)
async def test_update_rejects_other_users_project(http_client, monkeypatch, kind):
    """Re-pointing an existing row at a foreign project is rejected and changes nothing."""
    alice_project = await _create_project(http_client, "Alice private")

    with acting_as(monkeypatch, "bob"):
        created = await _create(http_client, kind, None)
        assert created.status_code == 201
        item_url = f"{CREATE_CASES[kind][0]}/{created.json()['id']}"

        response = await http_client.put(item_url, json={"project_id": alice_project})

        assert response.status_code == 404
        fetched = await http_client.get(item_url)
        assert fetched.json()["project_id"] is None


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", UPDATE_KINDS)
async def test_update_unknown_project_is_not_found(http_client, kind):
    """An unused project id on update is a clean 404, not a raw foreign-key error."""
    created = await _create(http_client, kind, None)
    item_url = f"{CREATE_CASES[kind][0]}/{created.json()['id']}"

    response = await http_client.put(item_url, json={"project_id": UNKNOWN_PROJECT_ID})

    assert response.status_code == 404
    assert "FOREIGN KEY" not in response.text
    assert (await http_client.get(item_url)).json()["project_id"] is None


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", UPDATE_KINDS)
async def test_update_with_own_project_still_works(http_client, kind):
    """The owner can still move a row to their own project."""
    project_id = await _create_project(http_client, "Alice own")
    created = await _create(http_client, kind, None)
    item_url = f"{CREATE_CASES[kind][0]}/{created.json()['id']}"

    response = await http_client.put(item_url, json={"project_id": project_id})

    assert response.status_code == 200
    assert response.json()["project_id"] == project_id


@pytest.mark.asyncio
async def test_import_skill_rejects_other_users_project(http_client, monkeypatch):
    """The import path goes through skill creation, so it is guarded as well."""
    alice_project = await _create_project(http_client, "Alice private")
    skill_md = "---\nname: imported-skill\ndescription: Imported skill\n---\n\n# Steps\n1. Do it\n"

    with acting_as(monkeypatch, "bob"):
        response = await http_client.post("/api/v1/skills/import", json={
            "skill_md": skill_md,
            "project_id": alice_project,
        })

        assert response.status_code == 404
        assert await _count(http_client, "skills") == 0


@pytest.mark.asyncio
async def test_owner_project_delete_leaves_other_users_rows_alone(http_client, monkeypatch):
    """Deleting a project must not delete or rewrite another user's plans and documents."""
    alice_project = await _create_project(http_client, "Alice private")

    with acting_as(monkeypatch, "bob"):
        bob_project = await _create_project(http_client, "Bob own")
        # Rejected attempts to hang Bob's rows on Alice's project
        assert (await _create(http_client, "plans", alice_project)).status_code == 404
        assert (await _create(http_client, "documents", alice_project)).status_code == 404
        # Bob's legitimate rows, linked to his own project
        plan = await _create(http_client, "plans", bob_project)
        document = await _create(http_client, "documents", bob_project)

    deleted = await http_client.delete(f"/api/v1/projects/{alice_project}")
    assert deleted.status_code == 200

    with acting_as(monkeypatch, "bob"):
        assert await _count(http_client, "plans") == 1
        fetched = await http_client.get(f"/api/v1/documents/{document.json()['id']}")
        assert fetched.json()["project_id"] == bob_project
        assert plan.json()["project_id"] == bob_project
