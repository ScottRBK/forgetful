"""The same HTTP/SQL pagination contract against real SQLite and PostgreSQL."""
import base64
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, insert, select, text, update

from app.config.settings import settings
from app.middleware.auth import get_user_from_auth
from app.models.plan_models import PlanStatus, TaskPriority, TaskState
from app.models.project_models import ProjectStatus

RESOURCES = ("projects", "plans", "tasks", "documents", "code_artifacts", "files", "skills")
STAMP = datetime(2026, 1, 2, tzinfo=UTC)
SERVICE = {
    "projects": ("project_service", "project_repo"),
    "plans": ("plan_service", "plan_repo"),
    "tasks": ("task_service", "task_repo"),
    "documents": ("document_service", "document_repo"),
    "code_artifacts": ("code_artifact_service", "artifact_repo"),
    "files": ("file_service", "file_repo"),
    "skills": ("skill_service", "skill_repo"),
}


class FixedPaginationEmbeddings:
    """Only the external provider is replaced; database and HTTP code are real."""

    async def generate_embedding(self, text):
        return [1.0] + [0.0] * (settings.EMBEDDING_DIMENSIONS - 1)


@dataclass
class PaginationEnvironment:
    client: object
    mcp: object
    backend: str

    async def user(self):
        return await get_user_from_auth(SimpleNamespace(fastmcp=self.mcp))

    def service(self, resource):
        return getattr(self.mcp, SERVICE[resource][0])

    def repository(self, resource):
        return getattr(self.service(resource), SERVICE[resource][1])

    @property
    def adapter(self):
        return self.repository("projects").db_adapter

    def table(self, name):
        if self.backend == "SQLite":
            from app.repositories.sqlite.sqlite_tables import Base
        else:
            from app.repositories.postgres.postgres_tables import Base
        return Base.metadata.tables[name]

    async def post(self, resource, payload):
        response = await self.client.post(endpoint(resource), json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    async def full(self, resource, params=None):
        params = dict(params or {})
        for key, kind in (("status", PlanStatus if resource == "plans" else ProjectStatus),
                          ("state", TaskState), ("priority", TaskPriority)):
            if key in params:
                params[key] = kind(params[key])
        if isinstance(params.get("tags"), str):
            params["tags"] = [tag.strip() for tag in params["tags"].split(",")] if params["tags"] else None
        rows = await getattr(self.service(resource), "list_" + resource)(
            user_id=(await self.user()).id, **params,
        )
        return [row.model_dump(mode="json") for row in rows]


def endpoint(resource):
    return "/api/v1/" + resource.replace("_", "-")


@contextmanager
def acting_as_other(monkeypatch):
    with monkeypatch.context() as patch:
        patch.setattr(settings, "DEFAULT_USER_ID", "pagination-other-owner")
        patch.setattr(settings, "DEFAULT_USER_EMAIL", "other@example.test")
        yield


@contextmanager
def capture_sql(environment):
    statements = []

    def record(_connection, _cursor, statement, parameters, context, _many):
        compiled = getattr(context, "compiled", None)
        clause = getattr(compiled, "statement", None)
        columns = getattr(clause, "selected_columns", ())
        statements.append({
            "sql": statement, "parameters": parameters,
            "selected": [column.key for column in columns],
        })

    engine = environment.adapter._engine.sync_engine
    event.listen(engine, "before_cursor_execute", record)
    try:
        yield statements
    finally:
        event.remove(engine, "before_cursor_execute", record)


def payload(resource, index, project_id=None, plan_id=None, **changes):
    label = f"pagination-{index}"
    values = {
        "projects": {"name": label, "description": "Pagination project", "project_type": "development",
                     "repo_name": "https://github.com/Example/Paging.git", "status": "active"},
        "plans": {"title": label, "project_id": project_id, "status": "active",
                  "external_ref": f"pagination:{index}"},
        "tasks": {"title": label, "plan_id": plan_id, "priority": "P2", "assigned_agent": "page-reader"},
        "documents": {"title": label, "description": "Summary remains visible", "content": "large-content " * 300,
                      "document_type": "note", "tags": ["paging", "alpha"], "project_id": project_id},
        "code_artifacts": {"title": label, "description": "Code summary", "code": "print('paging')\n" * 300,
                           "language": "python", "tags": ["paging", "alpha"], "project_id": project_id},
        "files": {"filename": label + ".txt", "description": "File summary",
                  "data": base64.b64encode(b"large-file " * 300).decode(), "mime_type": "text/plain",
                  "tags": ["paging", "alpha"], "project_id": project_id},
        "skills": {"name": label, "description": "Skill summary", "content": "large-skill " * 300,
                   "tags": ["paging", "alpha"], "importance": 6, "project_id": project_id},
    }
    return dict(values[resource], **changes)


async def seed(environment, resource, count, project_id=None, plan_id=None, **changes):
    nonce = uuid4().hex
    if resource != "projects" and project_id is None:
        project_id = (await environment.post("projects", payload("projects", nonce)))["id"]
    if resource == "tasks" and plan_id is None:
        plan_id = (await environment.post("plans", payload("plans", nonce, project_id)))["id"]
    public_count = min(count, 3) if count > 20 else count
    created = [await environment.post(resource, payload(resource, f"{nonce}-{i}", project_id, plan_id, **changes))
               for i in range(public_count)]
    table = environment.table(resource)
    if public_count < count:
        # Scale fixtures copy a row that the real public API already validated/persisted.
        # Bulk inserts avoid thousands of repeated model/provider calls, not database reads.
        async with environment.adapter.system_session() as session:
            result = await session.execute(select(table).where(table.c.id == created[0]["id"]))
            template = dict(result.mappings().one())
            template.pop("id")
            label = "name" if resource in ("projects", "skills") else (
                "filename" if resource == "files" else "title"
            )
            copies = []
            for index in range(public_count, count):
                copy = dict(template, **{label: f"pagination-{nonce}-{index}"})
                if resource == "plans":
                    copy["external_ref"] = f"pagination-scale:{nonce}-{index}"
                copies.append(copy)
            columns = [table.c.id, table.c[label]]
            if resource == "tasks":
                columns.append(table.c.version)
            result = await session.execute(insert(table).returning(*columns), copies)
            inserted = [dict(row) for row in result.mappings()]
            if resource == "skills" and environment.backend == "SQLite":
                original = await session.execute(
                    text("SELECT embedding FROM vec_skills WHERE skill_id = :skill_id"),
                    {"skill_id": str(created[0]["id"])},
                )
                vector = original.scalar_one()
                await session.execute(
                    text("INSERT INTO vec_skills (skill_id, embedding) VALUES (:skill_id, :embedding)"),
                    [{"skill_id": str(row["id"]), "embedding": vector} for row in inserted],
                )
                vectors = await session.execute(text("SELECT skill_id FROM vec_skills"))
                assert {str(row["id"]) for row in inserted}.issubset(set(vectors.scalars()))
            created.extend(inserted)
        assert len(created) == count and len({row["id"] for row in created}) == count
    params = {"plan_id": plan_id} if resource == "tasks" else (
        {"project_id": project_id} if resource != "projects" else {}
    )
    # Real SQL fixture setup: equal sort values make the unique tie-breaker observable.
    async with environment.adapter.system_session() as session:
        await session.execute(update(table).where(table.c.id.in_([row["id"] for row in created])).values(created_at=STAMP))
    return created, params


async def get_page(environment, resource, params):
    response = await environment.client.get(endpoint(resource), params=params)
    assert response.status_code == 200, response.text
    return response.json()


class PaginationCases:
    """Inherited by both native-backend wrappers; no mock database is used."""

    @pytest.mark.parametrize("resource", RESOURCES)
    async def test_rest_explicit_page_contract(self, pagination_environment, resource):
        """Baseline red: fail at length assertion, not a missing new import/field."""
        environment = pagination_environment
        created, params = await seed(environment, resource, 3)
        result = await get_page(environment, resource, dict(params, limit=1, offset=1))
        assert len(result[resource]) == 1, "REST ignored the requested bounded page"
        assert result["total"] == len(created)
        assert (result["limit"], result["offset"]) == (1, 1)
        expected = sorted((row["id"] for row in created), reverse=resource != "tasks")
        assert result[resource][0]["id"] == expected[1]

    @pytest.mark.parametrize("resource", RESOURCES)
    async def test_all_summary_fields_pages_sql_and_ownership(self, pagination_environment, monkeypatch, resource):
        environment = pagination_environment
        created, params = await seed(environment, resource, 105)
        with acting_as_other(monkeypatch):
            await seed(environment, resource, 3)
        expected = await environment.full(resource, params)
        assert len(expected) == 105
        default = await get_page(environment, resource, params)
        assert (len(default[resource]), default["limit"], default["offset"], default["total"]) == (20, 20, 0, 105)
        collected = []
        for offset in range(0, 105, 17):
            with capture_sql(environment) as statements:
                result = await get_page(environment, resource, dict(params, limit=17, offset=offset))
            assert result["total"] == 105
            assert (result["limit"], result["offset"]) == (17, offset)
            assert any("count(" in row["sql"].lower() for row in statements), statements
            selects = [row for row in statements if row["sql"].lstrip().upper().startswith("SELECT")]
            page_selects = [row for row in selects if "LIMIT" in row["sql"].upper()]
            assert page_selects, statements
            assert any("OFFSET" in row["sql"].upper() for row in page_selects), statements
            for row in page_selects:
                assert not {"content", "code", "data", "embedding"}.intersection(row["selected"]), row
            collected.extend(result[resource])
        ids = [row["id"] for row in collected]
        assert len(ids) == len(set(ids)) == 105
        assert ids == sorted((row["id"] for row in created), reverse=resource != "tasks")
        assert {row["id"]: row for row in collected} == {row["id"]: row for row in expected}
        maximum = await get_page(environment, resource, dict(params, limit=100))
        assert len(maximum[resource]) == 100 and maximum["total"] == 105
        empty = await get_page(environment, resource, dict(params, limit=1, offset=9999))
        assert empty[resource] == [] and empty["total"] == 105
        boundary = await get_page(environment, resource, dict(params, limit=1, offset=2**63 - 1))
        assert boundary[resource] == [] and boundary["total"] == 105
        # The ordinary SQLite fixture propagates server exceptions. This diagnostic alone
        # observes the actual HTTP status, without changing that fixture or the parser.
        async with AsyncClient(
            transport=ASGITransport(app=environment.mcp.http_app(), raise_app_exceptions=False),
            base_url="http://test",
        ) as error_client:
            reference = await error_client.get("/api/v1/memories", params={"offset": str(2**63)})
            oversized = await error_client.get(endpoint(resource), params=dict(params, offset=str(2**63)))
        # Memories has no artificial signed-64 parser ceiling. Record actual driver behavior,
        # rather than introducing a new clamp or treating a server error as valid empty data.
        print("OFFSET_OVER_SIGNED64", environment.backend, resource,
              {"status": oversized.status_code, "memoryReferenceStatus": reference.status_code})
        assert oversized.status_code == reference.status_code
        if oversized.status_code == 200:
            assert oversized.json()[resource] == [] and oversized.json()["total"] == 105

    @pytest.mark.parametrize("resource", RESOURCES)
    async def test_page_ownership_not_hidden_by_parent_filter(
        self, pagination_environment, monkeypatch, resource,
    ):
        environment = pagination_environment
        owned, params = await seed(environment, resource, 3)
        owner_id = (await environment.user()).id
        with acting_as_other(monkeypatch):
            foreign, _ = await seed(environment, resource, 3)
            other_id = (await environment.user()).id
        assert owner_id != other_id
        table = environment.table(resource)
        # Deliberately construct cross-owner parent links through a system session.
        # Public creation correctly rejects these links; this fixture prevents the
        # project/plan predicate from masking a missing user_id predicate.
        if params:
            async with environment.adapter.system_session() as session:
                await session.execute(
                    update(table).where(table.c.id.in_([row["id"] for row in foreign])).values(**params),
                )
        async with environment.adapter.system_session() as session:
            rows = (await session.execute(
                select(table).where(table.c.id.in_([row["id"] for row in foreign])),
            )).mappings().all()
            assert len(rows) == 3
            assert all(str(row["user_id"]) == str(other_id) for row in rows)
            assert all(row[key] == value for row in rows for key, value in params.items())
        expected = {row["id"] for row in owned}
        actual = []
        for offset in range(3):
            page = await get_page(environment, resource, dict(params, limit=1, offset=offset))
            assert page["total"] == 3
            assert len(page[resource]) == 1
            actual.extend(row["id"] for row in page[resource])
        assert len(actual) == len(set(actual)) == 3
        assert set(actual) == expected
        empty = await get_page(environment, resource, dict(params, limit=1, offset=3))
        assert empty["total"] == 3 and empty[resource] == []

    @pytest.mark.parametrize("resource", RESOURCES)
    @pytest.mark.parametrize("key,value", [
        ("limit", ""), ("limit", "abc"), ("limit", "1.5"), ("limit", "0"),
        ("limit", "-1"), ("limit", "101"), ("offset", ""), ("offset", "abc"),
        ("offset", "1.5"), ("offset", "-1"),
    ], ids=[
        "limit-empty", "limit-text", "limit-fraction", "limit-zero", "limit-negative", "limit-over-max",
        "offset-empty", "offset-text", "offset-fraction", "offset-negative",
    ])
    async def test_page_errors_exactly_match_memories(self, pagination_environment, resource, key, value):
        environment = pagination_environment
        # Validation does not need a resource row; tasks still needs its existing plan argument.
        params = {key: value, **({"plan_id": 1} if resource == "tasks" else {})}
        reference = await environment.client.get("/api/v1/memories", params={key: value})
        with capture_sql(environment) as statements:
            response = await environment.client.get(endpoint(resource), params=params)
        assert response.status_code == reference.status_code == 400
        assert response.json() == reference.json()
        assert not any(resource in row["sql"].lower() for row in statements), statements

    @pytest.mark.parametrize("resource", RESOURCES)
    async def test_combined_filters_empty_and_backend_tag_semantics(self, pagination_environment, resource):
        environment = pagination_environment
        _, params = await seed(environment, resource, 5)
        if resource == "projects":
            variants = [{"status": "active", "repo_name": "git@github.com:Example/Paging.git"},
                        {"status": "archived", "repo_name": "git@github.com:Example/Paging.git"}]
        elif resource == "plans":
            all_rows = await environment.full(resource, params)
            variants = [dict(params, status="active", external_ref=all_rows[0]["external_ref"]),
                        dict(params, status="archived")]
        elif resource == "tasks":
            variants = [dict(params, state="todo", priority="P2", assigned_agent="page-reader"),
                        dict(params, state="cancelled", priority="P0")]
        else:
            for index, tag in enumerate(("%", "_", "'", "")):
                await environment.post(resource, payload(
                    resource, f"literal-{uuid4().hex}-{index}", project_id=params["project_id"], tags=[tag],
                ))
            discriminator = {"documents": ("document_type", "note"), "code_artifacts": ("language", "python"),
                             "files": ("mime_type", "text/plain"), "skills": ("importance_threshold", 6)}[resource]
            variants = [dict(params, tags=tag, **{discriminator[0]: discriminator[1]})
                        for tag in ("alpha,absent", "%", "_", "'", ",", "")]
            variants.append(dict(params, tags="no-match"))
        for filters in variants:
            expected = await environment.full(resource, filters)
            rows = []
            for offset in range(0, len(expected) + 1, 2):
                result = await get_page(environment, resource, dict(filters, limit=2, offset=offset))
                assert result["total"] == len(expected)
                rows.extend(result[resource])
            assert {row["id"]: row for row in rows} == {row["id"]: row for row in expected}
        if resource == "tasks":
            missing = await environment.client.get(endpoint(resource), params={"limit": 1})
            assert missing.status_code == 400
            assert missing.json() == {"error": "plan_id query param is required"}

    async def test_large_exact_repository_identity_membership(self, pagination_environment):
        environment = pagination_environment
        user = await environment.user()
        table = environment.table("projects")
        uid = str(user.id) if environment.backend == "SQLite" else user.id
        rows = [{"user_id": uid, "name": f"large-{i}", "description": "Lightweight identity fixture",
                 "project_type": "development", "status": "active", "created_at": STAMP,
                 "repo_name": "https://github.com/Example/Paging.git" if i % 2 else "git@github.com:Example/Paging.git"}
                for i in range(1105)]
        rows += [{"user_id": uid, "name": f"literal-{i}", "description": "Not canonical alias",
                  "project_type": "development", "status": "active", "created_at": STAMP,
                  "repo_name": literal} for i, literal in enumerate((
                      "github.com/example/Paging", "ssh://git@github.com:2222/Example/Paging.git", "Example/Paging",
                  ))]
        async with environment.adapter.system_session() as session:
            await session.execute(insert(table), rows)
        filters = {"repo_name": "github.com/Example/Paging", "status": "active"}
        expected = await environment.full("projects", filters)
        assert len(expected) == 1105
        result = await get_page(environment, "projects", dict(filters, limit=100, offset=1000))
        assert result["total"] == 1105 and len(result["projects"]) == 100
        expected_ids = sorted((row["id"] for row in expected), reverse=True)
        assert [row["id"] for row in result["projects"]] == expected_ids[1000:1100]
        for literal in ("github.com/example/Paging", "ssh://git@github.com:2222/Example/Paging.git", "Example/Paging"):
            same = await environment.full("projects", {"repo_name": literal})
            page = await get_page(environment, "projects", {"repo_name": literal, "limit": 1})
            assert page["total"] == len(same) == 1
            assert page["projects"] == same

    @pytest.mark.parametrize("resource", ["projects", "plans", "tasks"])
    async def test_nontrivial_derived_summary_fields(self, pagination_environment, resource):
        environment = pagination_environment
        created, params = await seed(environment, resource, 3)
        if resource == "projects":
            for index in range(2):
                memory = await environment.post("memories", {
                    "title": f"Counted memory {index}", "content": "Actual persisted memory",
                    "context": "Pagination count fixture", "keywords": ["paging"],
                    "tags": [], "importance": 5, "project_ids": [created[0]["id"]],
                })
                if index == 1:
                    response = await environment.client.delete(f"/api/v1/memories/{memory['id']}")
                    assert response.status_code == 200, response.text
        elif resource == "plans":
            for index in range(2):
                await environment.post("tasks", payload("tasks", index, plan_id=created[0]["id"]))
        else:
            for index in range(2):
                response = await environment.client.post(
                    f"/api/v1/tasks/{created[0]['id']}/criteria", json={"description": f"Criterion {index}"},
                )
                assert response.status_code == 201, response.text
                if index == 0:
                    changed = await environment.client.put(
                        f"/api/v1/criteria/{response.json()['id']}", json={"met": True},
                    )
                    assert changed.status_code == 200, changed.text
            for target in created[1:]:
                response = await environment.client.post(
                    f"/api/v1/tasks/{created[0]['id']}/dependencies", json={"depends_on_task_id": target["id"]},
                )
                assert response.status_code == 201, response.text
            table = environment.table("tasks")
            async with environment.adapter.system_session() as session:
                await session.execute(update(table).where(table.c.id == created[1]["id"]).values(state="done"))
                await session.execute(update(table).where(table.c.id == created[2]["id"]).values(state="cancelled"))
        expected = await environment.full(resource, params)
        actual = await get_page(environment, resource, dict(params, limit=100))
        assert {row["id"]: row for row in actual[resource]} == {row["id"]: row for row in expected}
        selected = next(row for row in actual[resource] if row["id"] == created[0]["id"])
        if resource == "projects":
            assert selected["memory_count"] == 2  # Obsolete memories are counted by the legacy property.
        elif resource == "plans":
            assert selected["task_count"] == 2
        else:
            assert (selected["criteria_total"], selected["criteria_met"], selected["blocked"]) == (2, 1, True)
            async with environment.adapter.system_session() as session:
                await session.execute(update(table).where(table.c.id == created[2]["id"]).values(state="done"))
            changed = await get_page(environment, resource, dict(params, limit=100))
            assert not next(row for row in changed[resource] if row["id"] == created[0]["id"])["blocked"]
