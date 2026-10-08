"""Plan reference contracts exercised unchanged against SQLite and PostgreSQL."""

import asyncio
from pathlib import Path

import pytest
from alembic.config import Config
from fastmcp.exceptions import ToolError
from sqlalchemy import MetaData, Table
from sqlalchemy.exc import IntegrityError

from alembic import command
from app.bootstrap import create_repositories
from app.config.settings import settings
from app.exceptions import ConflictError
from app.models.plan_models import Plan, PlanCreate, PlanUpdate, TaskCreate
from app.models.project_models import ProjectCreate
from app.models.user_models import UserCreate
from app.services.plan_service import PlanService


async def create_project(http_client):
    response = await http_client.post("/api/v1/projects", json={
        "name": "Plan references",
        "description": "External reference regression tests",
        "project_type": "development",
    })
    assert response.status_code == 201
    return response.json()["id"]


class TestPlanExternalRefAPI:
    @pytest.mark.parametrize("reference", ["", " \t\n ", "x" * 256])
    async def test_invalid_references_on_create_update_and_lookup(self, http_client, reference):
        project_id = await create_project(http_client)
        payload = {"project_id": project_id, "title": "Valid", "external_ref": "x" * 255}
        created = await http_client.post("/api/v1/plans", json=payload)
        assert created.status_code == 201
        path = f"/api/v1/plans/{created.json()['id']}"

        rejected = [
            await http_client.post("/api/v1/plans", json={**payload, "external_ref": reference}),
            await http_client.put(path, json={"external_ref": reference}),
            await http_client.get("/api/v1/plans", params={"external_ref": reference}),
        ]

        assert [response.status_code for response in rejected] == [400, 400, 400]
        assert (await http_client.get(path)).json()["external_ref"] == "x" * 255

    async def test_external_ref_is_private_and_unique_per_user(self, http_client, monkeypatch):
        project_id = await create_project(http_client)
        payload = {"project_id": project_id, "title": "Private", "external_ref": "private:42"}
        original = await http_client.post("/api/v1/plans", json=payload)
        original_id = original.json()["id"]

        with monkeypatch.context() as other_user:
            other_user.setattr(settings, "DEFAULT_USER_ID", "external-ref-other-user")
            other_user.setattr(settings, "DEFAULT_USER_EMAIL", "ref-other@example.test")
            other_project = await create_project(http_client)
            missing = await http_client.get("/api/v1/plans", params={"external_ref": "private:42"})
            assert missing.json() == {"plans": [], "total": 0}
            assert (await http_client.get(f"/api/v1/plans/{original_id}")).status_code == 404
            update = await http_client.put(
                f"/api/v1/plans/{original_id}", json={"external_ref": "stolen"},
            )
            assert update.status_code == 404
            independent = await http_client.post("/api/v1/plans", json={
                **payload, "project_id": other_project,
            })
            assert independent.status_code == 201
            private = await http_client.get("/api/v1/plans", params={"external_ref": "private:42"})
            assert [p["id"] for p in private.json()["plans"]] == [independent.json()["id"]]

        found = await http_client.get("/api/v1/plans", params={"external_ref": "private:42"})
        assert [p["id"] for p in found.json()["plans"]] == [original_id]

    @pytest.mark.parametrize("status", ["completed", "archived"])
    async def test_inactive_plans_retain_reference_until_deleted(self, http_client, status):
        project_id = await create_project(http_client)
        payload = {
            "project_id": project_id, "title": "Finished", "external_ref": "work:42",
            "status": status,
        }
        created = await http_client.post("/api/v1/plans", json=payload)
        assert created.status_code == 201

        duplicate = await http_client.post("/api/v1/plans", json={**payload, "status": "draft"})

        assert duplicate.status_code == 409
        found = await http_client.get("/api/v1/plans", params={"external_ref": "work:42"})
        assert [p["id"] for p in found.json()["plans"]] == [created.json()["id"]]
        filtered = await http_client.get("/api/v1/plans", params={
            "external_ref": "work:42", "status": "active",
        })
        assert filtered.json()["plans"] == []
        other_project = await create_project(http_client)
        filtered = await http_client.get("/api/v1/plans", params={
            "external_ref": "work:42", "project_id": other_project,
        })
        assert filtered.json()["plans"] == []
        deleted = await http_client.delete(f"/api/v1/plans/{created.json()['id']}")
        assert deleted.status_code == 200
        recreated = await http_client.post("/api/v1/plans", json=payload)
        assert recreated.status_code == 201

    async def test_external_ref_round_trip_and_lookup(self, http_client):
        project_id = await create_project(http_client)
        reference = "github:ScottRBK/factory#42"
        source_url = "https://github.com/ScottRBK/factory/issues/42"

        created = await http_client.post("/api/v1/plans", json={
            "project_id": project_id, "title": "Factory plan",
            "external_ref": f"  {reference}\n", "source_url": source_url,
        })

        assert created.status_code == 201
        plan = created.json()
        assert plan["external_ref"] == reference
        assert plan["source_url"] == source_url
        retrieved = await http_client.get(f"/api/v1/plans/{plan['id']}")
        assert retrieved.json()["external_ref"] == reference
        found = await http_client.get("/api/v1/plans", params={"external_ref": f" {reference} "})
        assert found.status_code == 200
        assert found.json()["total"] == 1
        assert found.json()["plans"][0]["external_ref"] == reference
        assert found.json()["plans"][0]["id"] == plan["id"]
        missing = await http_client.get("/api/v1/plans", params={"external_ref": reference.lower()})
        assert missing.json() == {"plans": [], "total": 0}


    async def test_external_ref_duplicate_create_and_optional_reference(self, http_client):
        project_id = await create_project(http_client)
        other_project = await create_project(http_client)
        reference = "tracker:Issue/42"
        payload = {"project_id": project_id, "title": "Original", "external_ref": reference}
        original = await http_client.post("/api/v1/plans", json=payload)
        assert original.status_code == 201

        duplicate = await http_client.post("/api/v1/plans", json={
            **payload, "project_id": other_project, "external_ref": f" {reference} ",
        })

        assert duplicate.status_code == 409
        assert "external_ref" in duplicate.json()["error"]
        assert "list_plans" in duplicate.json()["error"]
        found = await http_client.get("/api/v1/plans", params={"external_ref": reference})
        assert [p["id"] for p in found.json()["plans"]] == [original.json()["id"]]
        # Case is significant; null and omitted references never collide.
        for optional in ({"external_ref": reference.lower()}, {}, {"external_ref": None}):
            response = await http_client.post("/api/v1/plans", json={
                "project_id": project_id, "title": "Independent plan", **optional,
            })
            assert response.status_code == 201
            assert response.json()["external_ref"] == optional.get("external_ref")


    async def test_external_ref_updates_preserve_replace_and_reject_duplicates(self, http_client):
        project_id = await create_project(http_client)
        plans = []
        for reference in ("issue:42", "issue:43"):
            created = await http_client.post("/api/v1/plans", json={
                "project_id": project_id, "title": "Original", "external_ref": reference,
            })
            plans.append(created.json())
        path = f"/api/v1/plans/{plans[1]['id']}"
        before = (await http_client.get(path)).json()

        duplicate = await http_client.put(path, json={"external_ref": " issue:42 ", "title": "Bad"})

        assert duplicate.status_code == 409
        unchanged = await http_client.get(path)
        assert unchanged.json() == before
        for update in ({"title": "Renamed"}, {"title": "Null preserved", "external_ref": None}):
            response = await http_client.put(path, json=update)
            assert response.status_code == 200
            assert response.json()["external_ref"] == "issue:43"
            assert response.json()["title"] == update["title"]
        replaced = await http_client.put(path, json={"external_ref": " issue:44 "})
        assert replaced.status_code == 200
        assert replaced.json()["external_ref"] == "issue:44"
        old = await http_client.get("/api/v1/plans", params={"external_ref": "issue:43"})
        assert old.json()["plans"] == []
        reused = await http_client.post("/api/v1/plans", json={
            "project_id": project_id, "title": "Reused reference", "external_ref": "issue:43",
        })
        assert reused.status_code == 201
        before = (await http_client.get(path)).json()
        for fields in ({"external_ref": "issue:44"}, {"external_ref": None}):
            same = await http_client.put(path, json=fields)
            assert same.json() == before


class TestPlanExternalRefMCP:
    async def test_external_ref_mcp_workflow(self, mcp_client):
        async def call(tool_name, **arguments):
            result = await mcp_client.call_tool(
                "execute_forgetful_tool", {"tool_name": tool_name, "arguments": arguments},
            )
            return result.data

        project = await call(
            "create_project", name="Plan references", description="MCP reference tests",
            project_type="development",
        )
        project_id = project["id"]
        plan = await call(
            "create_plan", project_id=project_id, title="Watcher plan",
            external_ref=" issue:42 ", source_url="https://tracker.test/42",
        )

        assert plan["external_ref"] == "issue:42"
        assert plan["source_url"] == "https://tracker.test/42"
        assert (await call("get_plan", plan_id=plan["id"]))["external_ref"] == "issue:42"
        with pytest.raises(ToolError, match="external_ref already exists"):
            await call(
                "create_plan", project_id=project_id, title="Duplicate", external_ref="issue:42",
            )
        found = await call("list_plans", external_ref=" issue:42 ")
        assert found["total_count"] == 1
        assert found["plans"][0]["id"] == plan["id"]
        assert found["plans"][0]["external_ref"] == "issue:42"
        for fields in ({"title": "Renamed"}, {"external_ref": None}):
            preserved = await call("update_plan", plan_id=plan["id"], **fields)
            assert preserved["external_ref"] == "issue:42"
        other = await call(
            "create_plan", project_id=project_id, title="Other plan", external_ref="issue:43",
        )
        with pytest.raises(ToolError, match="external_ref already exists"):
            await call("update_plan", plan_id=other["id"], external_ref="issue:42")
        changed = await call("update_plan", plan_id=plan["id"], external_ref=" issue:44 ")
        assert changed["external_ref"] == "issue:44"
        for tool_name, arguments in (
            ("create_plan", {"project_id": project_id, "title": "Blank"}),
            ("update_plan", {"plan_id": plan["id"]}),
            ("list_plans", {}),
        ):
            with pytest.raises(ToolError, match="at least 1 character"):
                await call(tool_name, external_ref=" \t ", **arguments)
            info = await mcp_client.call_tool(
                "how_to_use_forgetful_tool", {"tool_name": tool_name},
            )
            assert "external_ref" in {p["name"] for p in info.data["parameters"]}


@pytest.fixture
async def reference_store(reference_db, monkeypatch):
    monkeypatch.setattr(settings, "PLANNING_ENABLED", True)
    repos = create_repositories(reference_db, None, None)
    user = await repos["user"].create_user(UserCreate(
        external_id="reference-storage-user", name="Reference tests", email="ref@example.test",
    ))
    project = await repos["project"].create_project(user.id, ProjectCreate(
        name="Reference storage", description="Persistence regressions", project_type="development",
    ))
    return repos, user, project


class TestPlanExternalRefStorage:
    async def test_concurrent_creates_on_separate_connections(self, reference_db, reference_store):
        repos, user, project = reference_store
        # Independent engines guarantee independent physical database connections (also on SQLite).
        other_db = type(reference_db)()
        other_repo = type(repos["plan"])(other_db)
        services = [PlanService(repos["plan"]), PlanService(other_repo)]
        ready = asyncio.Barrier(2)

        async def create(service):
            await ready.wait()
            return await service.create_plan(user.id, PlanCreate(
                title="Concurrent watcher", project_id=project.id, external_ref="race:42",
            ))

        try:
            results = await asyncio.gather(*(create(s) for s in services), return_exceptions=True)
        finally:
            await other_db.dispose()

        winners = [result for result in results if isinstance(result, Plan)]
        conflicts = [result for result in results if isinstance(result, ConflictError)]
        assert len(winners) == len(conflicts) == 1, results
        found = await services[0].list_plans(user.id, external_ref="race:42")
        assert [p.id for p in found] == [winners[0].id]
        # A failed transaction must not poison the next request.
        created = await services[0].create_plan(user.id, PlanCreate(
            title="Next request", project_id=project.id, external_ref="race:43",
        ))
        assert created.external_ref == "race:43"

    async def test_unrelated_integrity_error_is_not_a_reference_conflict(self, reference_store):
        repos, user, _ = reference_store
        with pytest.raises(IntegrityError):
            await repos["plan"].create_plan(user.id, PlanCreate(
                title="Missing project", project_id=-1, external_ref="foreign-key:42",
            ))

    async def test_migration_preserves_existing_plans_and_tasks(
        self, reference_db, reference_store,
    ):
        repos, user, project = reference_store
        config = Config(str(Path(__file__).parents[1] / "alembic.ini"))

        def migrate(connection, direction, revision):
            config.attributes["connection"] = connection
            getattr(command, direction)(config, revision)

        async with reference_db._engine.begin() as connection:
            await connection.run_sync(migrate, "downgrade", "20260822_project_encoding_point")

        # Seed using the actual old schema: new ORM models already include external_ref.
        def insert_legacy_plans(connection):
            plans = Table("plans", MetaData(), autoload_with=connection)
            owner = str(user.id) if connection.dialect.name == "sqlite" else user.id
            return [connection.execute(plans.insert().values(
                user_id=owner, project_id=project.id, title=f"Legacy {i}",
                source_url="https://tracker.test/shared", status="draft",
            ).returning(plans.c.id)).scalar_one() for i in range(2)]

        try:
            async with reference_db._engine.begin() as connection:
                plan_ids = await connection.run_sync(insert_legacy_plans)
            task = await repos["task"].create_task(user.id, TaskCreate(
                plan_id=plan_ids[0], title="Existing task",
            ))
        finally:
            async with reference_db._engine.begin() as connection:
                await connection.run_sync(migrate, "upgrade", "head")

        service = PlanService(repos["plan"])
        for plan_id in plan_ids:
            existing = await service.get_plan(user.id, plan_id)
            assert existing.external_ref is None
            assert existing.source_url == "https://tracker.test/shared"
        assert (await service.get_plan(user.id, plan_ids[0])).task_count == 1
        assert (await repos["task"].get_task_by_id(user.id, task.id)).title == "Existing task"
        # Old callers still create/update without the new field after upgrading.
        old_client = await service.create_plan(user.id, PlanCreate(
            title="Old client", project_id=project.id,
        ))
        updated = await service.update_plan(user.id, old_client.id, PlanUpdate(title="Renamed"))
        assert updated.external_ref is None
        assigned = await service.update_plan(
            user.id, plan_ids[0], PlanUpdate(external_ref="migrated:42"),
        )
        assert assigned.external_ref == "migrated:42"
        with pytest.raises(ConflictError):
            await service.update_plan(user.id, plan_ids[1], PlanUpdate(external_ref="migrated:42"))
