"""E2E tests for REST validation error responses.

Uses in-memory SQLite for test isolation.

Invalid client input must always produce a 4xx JSON response. The client below is
built with ``raise_app_exceptions=False`` so an unhandled exception inside a route
shows up as the HTTP 500 a real client would see, instead of aborting the test.
"""
import pytest
from fastmcp import Client
from httpx import ASGITransport, AsyncClient

JSON_HEADERS = {"content-type": "application/json"}


@pytest.fixture
async def api(sqlite_app):
    """HTTP client that returns 500 responses instead of re-raising route exceptions."""
    async with Client(sqlite_app):
        transport = ASGITransport(app=sqlite_app.http_app(), raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


async def _create(api, url, payload):
    response = await api.post(url, json=payload)
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _create_entity(api, name="Entity"):
    return await _create(
        api, "/api/v1/entities", {"name": name, "entity_type": "Individual"},
    )


def _assert_validation_error(response, label):
    """A 400 whose body is a JSON list of pydantic-style field errors."""
    assert response.status_code == 400, f"{label}: {response.status_code} {response.text[:200]}"
    errors = response.json()["error"]
    assert isinstance(errors, list) and errors, f"{label}: {errors!r}"
    for error in errors:
        assert {"type", "loc", "msg"} <= set(error), f"{label}: {error!r}"


class TestCustomValidatorErrors:
    """Errors raised by custom validators carry an exception object and must still be 400."""

    @pytest.mark.asyncio
    async def test_documents_blank_fields_return_400(self, api):
        document_id = await _create(api, "/api/v1/documents", {
            "title": "Doc", "description": "d", "content": "content",
        })

        create = await api.post(
            "/api/v1/documents", json={"title": "   ", "description": "d", "content": "c"},
        )
        _assert_validation_error(create, "POST /documents blank title")

        update = await api.put(f"/api/v1/documents/{document_id}", json={"title": "  "})
        _assert_validation_error(update, "PUT /documents blank title")

    @pytest.mark.asyncio
    async def test_code_artifacts_blank_fields_return_400(self, api):
        artifact_id = await _create(api, "/api/v1/code-artifacts", {
            "title": "Snippet", "description": "d", "code": "print(1)", "language": "python",
        })

        create = await api.post("/api/v1/code-artifacts", json={
            "title": "   ", "description": "d", "code": "print(1)", "language": "python",
        })
        _assert_validation_error(create, "POST /code-artifacts blank title")

        update = await api.put(
            f"/api/v1/code-artifacts/{artifact_id}", json={"description": "  "},
        )
        _assert_validation_error(update, "PUT /code-artifacts blank description")

    @pytest.mark.asyncio
    async def test_files_invalid_fields_return_400(self, api):
        file_id = await _create(api, "/api/v1/files", {
            "filename": "a.txt", "description": "d", "mime_type": "text/plain",
            "data": "aGVsbG8=",
        })

        bad_base64 = await api.post("/api/v1/files", json={
            "filename": "b.txt", "description": "d", "mime_type": "text/plain",
            "data": "abc",
        })
        _assert_validation_error(bad_base64, "POST /files bad base64")

        blank_name = await api.post("/api/v1/files", json={
            "filename": "   ", "description": "d", "mime_type": "text/plain",
            "data": "aGVsbG8=",
        })
        _assert_validation_error(blank_name, "POST /files blank filename")

        update = await api.put(f"/api/v1/files/{file_id}", json={"filename": "  "})
        _assert_validation_error(update, "PUT /files blank filename")

    @pytest.mark.asyncio
    async def test_entities_invalid_fields_return_400(self, api):
        entity_id = await _create_entity(api, "Alice")
        other_id = await _create_entity(api, "Bob")

        other_without_custom = await api.post(
            "/api/v1/entities", json={"name": "x", "entity_type": "Other"},
        )
        _assert_validation_error(other_without_custom, "POST /entities Other w/o custom_type")

        blank_name = await api.post(
            "/api/v1/entities", json={"name": "   ", "entity_type": "Team"},
        )
        _assert_validation_error(blank_name, "POST /entities blank name")

        update = await api.put(f"/api/v1/entities/{entity_id}", json={"name": "  "})
        _assert_validation_error(update, "PUT /entities blank name")

        self_relationship = await api.post(
            f"/api/v1/entities/{entity_id}/relationships",
            json={"target_entity_id": entity_id, "relationship_type": "works_with"},
        )
        _assert_validation_error(self_relationship, "POST relationship to self")

        relationship_id = await _create(
            api,
            f"/api/v1/entities/{entity_id}/relationships",
            {"target_entity_id": other_id, "relationship_type": "works_with"},
        )
        blank_type = await api.put(
            f"/api/v1/entities/relationships/{relationship_id}",
            json={"relationship_type": "  "},
        )
        _assert_validation_error(blank_type, "PUT relationship blank type")

    @pytest.mark.asyncio
    async def test_built_in_constraint_errors_keep_documented_shape(self, api):
        response = await api.post("/api/v1/documents", json={"title": "only title"})
        _assert_validation_error(response, "POST /documents missing fields")
        locations = {tuple(error["loc"]) for error in response.json()["error"]}
        assert ("description",) in locations
        assert ("content",) in locations


class TestNonFiniteNumbers:
    """json.loads accepts NaN/Infinity/1e400; echoing them back must not break the 400."""

    async def _post_raw(self, api, url, raw, method="POST"):
        return await api.request(method, url, content=raw, headers=JSON_HEADERS)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity", "1e400"])
    async def test_memory_create_non_finite_confidence_returns_400(self, api, token):
        raw = (
            '{"title":"x","content":"c","context":"x","keywords":["a"],"tags":["t"],'
            f'"importance":5,"confidence":{token}}}'
        )
        response = await self._post_raw(api, "/api/v1/memories", raw)
        _assert_validation_error(response, f"POST /memories confidence={token}")

    @pytest.mark.asyncio
    async def test_memory_routes_non_finite_values_return_400(self, api):
        create = await self._post_raw(api, "/api/v1/memories", (
            '{"title":"x","content":"c","context":"x","keywords":["a"],"tags":["t"],'
            '"importance":5,"project_ids":[1e400]}'
        ))
        _assert_validation_error(create, "POST /memories project_ids=[1e400]")

        memory_id = await _create(api, "/api/v1/memories", {
            "title": "m", "content": "c", "context": "x", "keywords": ["a"],
            "tags": ["t"], "importance": 5,
        })
        update = await self._post_raw(
            api, f"/api/v1/memories/{memory_id}", '{"confidence":NaN}', method="PUT",
        )
        _assert_validation_error(update, "PUT /memories confidence=NaN")

        search = await self._post_raw(
            api, "/api/v1/memories/search", '{"query":"x","project_ids":[1e400]}',
        )
        _assert_validation_error(search, "POST /memories/search project_ids=[1e400]")

    @pytest.mark.asyncio
    async def test_other_resources_non_finite_values_return_400(self, api):
        project = await self._post_raw(api, "/api/v1/projects", (
            '{"name":NaN,"description":"d","project_type":"development"}'
        ))
        _assert_validation_error(project, "POST /projects name=NaN")

        plan = await self._post_raw(
            api, "/api/v1/plans", '{"title":"t","goal":"g","confidence":NaN}',
        )
        _assert_validation_error(plan, "POST /plans confidence=NaN")

        task = await self._post_raw(
            api, "/api/v1/tasks", '{"plan_id":1,"title":"t","confidence":Infinity}',
        )
        _assert_validation_error(task, "POST /tasks confidence=Infinity")

        document = await self._post_raw(api, "/api/v1/documents", (
            '{"title":"t","description":"d","content":"c","confidence":NaN}'
        ))
        _assert_validation_error(document, "POST /documents confidence=NaN")
