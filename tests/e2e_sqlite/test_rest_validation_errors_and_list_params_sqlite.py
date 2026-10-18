"""E2E tests for REST validation error responses and list/search parameter bounds.

Uses in-memory SQLite for test isolation.

Invalid client input must always produce a 4xx JSON response. The client below is
built with ``raise_app_exceptions=False`` so an unhandled exception inside a route
shows up as the HTTP 500 a real client would see, instead of aborting the test.
"""
import pytest
from fastmcp import Client
from httpx import ASGITransport, AsyncClient

BIG = 10**30
INT64_MAX = 2**63 - 1
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


async def _create_skill(api, name="skill-one"):
    return await _create(api, "/api/v1/skills", {
        "name": name,
        "description": f"Deploy docker application {name}",
        "content": "# Skill\n\nsteps",
        "tags": ["t"],
        "importance": 7,
    })


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


class TestIntegerQueryParams:
    """Query integers must be rejected with 400 when they cannot fit the database column."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("path", [
        "/api/v1/documents",
        "/api/v1/files",
        "/api/v1/code-artifacts",
        "/api/v1/skills",
        "/api/v1/memories",
    ])
    async def test_list_project_id_out_of_range_returns_400(self, api, path):
        response = await api.get(f"{path}?project_id={BIG}")
        assert response.status_code == 400, f"{path}: {response.status_code}"
        assert "project_id" in response.json()["error"]

    @pytest.mark.asyncio
    async def test_other_out_of_range_query_ints_return_400(self, api):
        urls = [
            f"/api/v1/skills?importance_threshold={BIG}",
            f"/api/v1/skills/search?query=x&project_id={BIG}",
            f"/api/v1/skills/search?query=x&k={BIG}",
            f"/api/v1/entities?offset={2**63}",
            f"/api/v1/memories?offset={2**63}",
            f"/api/v1/memories?project_id=-{BIG}",
        ]
        for url in urls:
            response = await api.get(url)
            assert response.status_code == 400, f"{url}: {response.status_code}"
            assert isinstance(response.json()["error"], str)

    @pytest.mark.asyncio
    async def test_boundary_values_and_empty_filters_still_accepted(self, api):
        urls = [
            f"/api/v1/documents?project_id={INT64_MAX}",
            "/api/v1/documents?project_id=",
            "/api/v1/files?project_id=",
            "/api/v1/code-artifacts?project_id=",
            "/api/v1/skills?project_id=&importance_threshold=",
            f"/api/v1/entities?offset={INT64_MAX}",
        ]
        for url in urls:
            response = await api.get(url)
            assert response.status_code == 200, f"{url}: {response.status_code}"


class TestLinkBodyIds:
    """Ids in link request bodies must be integers within range; unknown ids stay 404."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("value", [BIG, -BIG, [1], {"a": 1}, "1", 1.5, True])
    async def test_skill_link_routes_reject_invalid_ids(self, api, value):
        skill_id = await _create_skill(api)
        routes = {
            "files": "file_id",
            "documents": "document_id",
            "code-artifacts": "code_artifact_id",
        }
        for route, key in routes.items():
            response = await api.post(f"/api/v1/skills/{skill_id}/{route}", json={key: value})
            assert response.status_code == 400, f"{route} {key}={value!r}: {response.status_code}"
            assert key in response.json()["error"]

    @pytest.mark.asyncio
    async def test_skill_link_unknown_integer_id_is_still_404(self, api):
        skill_id = await _create_skill(api)
        response = await api.post(f"/api/v1/skills/{skill_id}/files", json={"file_id": 987654})
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.parametrize("value", [BIG, -BIG, [1], {"a": 1}, "1", 1.5, True])
    async def test_entity_memory_link_rejects_invalid_memory_id(self, api, value):
        entity_id = await _create_entity(api)
        response = await api.post(
            f"/api/v1/entities/{entity_id}/memories", json={"memory_id": value},
        )
        assert response.status_code == 400, f"memory_id={value!r}: {response.status_code}"
        assert "memory_id" in response.json()["error"]

    @pytest.mark.asyncio
    async def test_entity_memory_link_unknown_integer_id_is_still_404(self, api):
        entity_id = await _create_entity(api)
        response = await api.post(
            f"/api/v1/entities/{entity_id}/memories", json={"memory_id": 987654},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.parametrize("value", [123, [1, 2], {"a": 1}, 1.5])
    async def test_skill_import_rejects_non_string_skill_md(self, api, value):
        response = await api.post("/api/v1/skills/import", json={"skill_md": value})
        assert response.status_code == 400, f"skill_md={value!r}: {response.status_code}"
        assert "skill_md" in response.json()["error"]


class TestSearchLimits:
    """limit/k below 1 must not turn into LIMIT -1 (unbounded) or LIMIT 0."""

    @pytest.mark.asyncio
    async def test_entity_search_limit_below_one_returns_400(self, api):
        for index in range(3):
            await _create_entity(api, f"Bulk{index}")

        for limit in (-1, 0, -1000):
            response = await api.post(
                "/api/v1/entities/search", json={"query": "Bulk", "limit": limit},
            )
            assert response.status_code == 400, f"limit={limit}: {response.status_code}"
            assert "limit must be between 1 and 100" in response.json()["error"]

    @pytest.mark.asyncio
    async def test_entity_search_valid_limits_still_work(self, api):
        for index in range(3):
            await _create_entity(api, f"Bulk{index}")

        one = await api.post("/api/v1/entities/search", json={"query": "Bulk", "limit": 1})
        assert one.status_code == 200
        assert len(one.json()["entities"]) == 1

        capped = await api.post(
            "/api/v1/entities/search", json={"query": "Bulk", "limit": 1000},
        )
        assert capped.status_code == 200
        assert len(capped.json()["entities"]) == 3

        default = await api.post("/api/v1/entities/search", json={"query": "Bulk"})
        assert default.status_code == 200

    @pytest.mark.asyncio
    async def test_skill_search_k_below_one_returns_400(self, api):
        for index in range(3):
            await _create_skill(api, f"deploy-skill-{index}")

        for k in (-1, 0):
            response = await api.get(f"/api/v1/skills/search?query=deploy+docker&k={k}")
            assert response.status_code == 400, f"k={k}: {response.status_code}"
            assert "Invalid k" in response.json()["error"]

        valid = await api.get("/api/v1/skills/search?query=deploy+docker&k=2")
        assert valid.status_code == 200
        assert len(valid.json()["skills"]) == 2
