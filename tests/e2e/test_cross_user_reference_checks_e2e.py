"""PostgreSQL E2E tests: referenced projects must belong to the caller.

PostgreSQL has no row-level security policies in this repository and foreign keys
only prove that the project id exists, so documents, code artifacts, files, plans
and skills could be attached to another user's project. The repositories now filter
on the project owner. Mirrors the SQLite two-user tests.
"""
import base64
from contextlib import contextmanager

import pytest

from app.config.settings import settings

pytestmark = pytest.mark.asyncio(loop_scope="session")

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


@pytest.mark.e2e
@pytest.mark.parametrize("kind", list(CREATE_CASES))
async def test_create_rejects_other_users_project_e2e(http_client, monkeypatch, kind):
    """A foreign project id is reported as not found and nothing is stored."""
    alice_project = await _create_project(http_client, "Alice private")

    with acting_as(monkeypatch, "bob"):
        response = await _create(http_client, kind, alice_project)

        assert response.status_code == 404
        assert "not found" in response.json()["error"].lower()
        assert await _count(http_client, kind) == 0


@pytest.mark.e2e
@pytest.mark.parametrize("kind", list(CREATE_CASES))
async def test_create_unknown_project_is_not_found_e2e(http_client, kind):
    """An unused project id is a clean 404, not a raw foreign-key error."""
    response = await _create(http_client, kind, UNKNOWN_PROJECT_ID)

    assert response.status_code == 404
    assert await _count(http_client, kind) == 0


@pytest.mark.e2e
@pytest.mark.parametrize("kind", list(CREATE_CASES))
async def test_create_with_own_project_still_works_e2e(http_client, kind):
    """The owner can still attach rows to their own project."""
    project_id = await _create_project(http_client, "Alice own")

    response = await _create(http_client, kind, project_id)

    assert response.status_code == 201
    assert response.json()["project_id"] == project_id


@pytest.mark.e2e
@pytest.mark.parametrize("kind", UPDATE_KINDS)
async def test_update_rejects_other_users_project_e2e(http_client, monkeypatch, kind):
    """Re-pointing an existing row at a foreign project is rejected and changes nothing."""
    alice_project = await _create_project(http_client, "Alice private")

    with acting_as(monkeypatch, "bob"):
        created = await _create(http_client, kind, None)
        assert created.status_code == 201
        item_url = f"{CREATE_CASES[kind][0]}/{created.json()['id']}"

        response = await http_client.put(item_url, json={"project_id": alice_project})

        assert response.status_code == 404
        assert (await http_client.get(item_url)).json()["project_id"] is None


@pytest.mark.e2e
@pytest.mark.parametrize("kind", UPDATE_KINDS)
async def test_update_unknown_project_is_not_found_e2e(http_client, kind):
    """An unused project id on update is a clean 404 and the row keeps its project."""
    created = await _create(http_client, kind, None)
    item_url = f"{CREATE_CASES[kind][0]}/{created.json()['id']}"

    response = await http_client.put(item_url, json={"project_id": UNKNOWN_PROJECT_ID})

    assert response.status_code == 404
    assert (await http_client.get(item_url)).json()["project_id"] is None


@pytest.mark.e2e
@pytest.mark.parametrize("kind", UPDATE_KINDS)
async def test_update_with_own_project_still_works_e2e(http_client, kind):
    """The owner can still move a row to their own project."""
    project_id = await _create_project(http_client, "Alice own")
    created = await _create(http_client, kind, None)
    item_url = f"{CREATE_CASES[kind][0]}/{created.json()['id']}"

    response = await http_client.put(item_url, json={"project_id": project_id})

    assert response.status_code == 200
    assert response.json()["project_id"] == project_id


@pytest.mark.e2e
async def test_owner_project_delete_leaves_other_users_rows_alone_e2e(http_client, monkeypatch):
    """Deleting a project must not delete or rewrite another user's plans and documents."""
    alice_project = await _create_project(http_client, "Alice private")

    with acting_as(monkeypatch, "bob"):
        bob_project = await _create_project(http_client, "Bob own")
        assert (await _create(http_client, "plans", alice_project)).status_code == 404
        assert (await _create(http_client, "documents", alice_project)).status_code == 404
        await _create(http_client, "plans", bob_project)
        document = await _create(http_client, "documents", bob_project)

    assert (await http_client.delete(f"/api/v1/projects/{alice_project}")).status_code == 200

    with acting_as(monkeypatch, "bob"):
        assert await _count(http_client, "plans") == 1
        fetched = await http_client.get(f"/api/v1/documents/{document.json()['id']}")
        assert fetched.json()["project_id"] == bob_project
