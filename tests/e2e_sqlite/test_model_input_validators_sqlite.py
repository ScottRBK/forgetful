"""E2E tests for input model validation through REST and MCP (in-memory SQLite).

Garbage base64 file data, indented code, blank plan/task/criterion/skill text and
oversized skill allowed-tools lists must be rejected (or stored verbatim) at the
API boundary, without leaving unusable rows behind.
"""
import base64

import pytest
from fastmcp.exceptions import ToolError
from sqlalchemy import update

from app.repositories.sqlite.sqlite_tables import FilesTable, PlansTable

GOOD_DATA = base64.b64encode(b"hello world").decode()
GARBAGE_DATA = ["!!!!", "====", "    "]
BLANKS = ["", "   ", " \t\n "]
INDENTED_CODE = "    def foo():\n        return 1\n"


def _file_payload(data: str = GOOD_DATA) -> dict:
    return {
        "filename": "a.bin",
        "description": "d",
        "data": data,
        "mime_type": "application/octet-stream",
    }


async def _create_project(http_client) -> int:
    response = await http_client.post("/api/v1/projects", json={
        "name": "p", "description": "d", "project_type": "development",
    })
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _create_plan(http_client) -> int:
    project_id = await _create_project(http_client)
    response = await http_client.post(
        "/api/v1/plans", json={"title": "plan", "project_id": project_id},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _create_task(http_client) -> int:
    plan_id = await _create_plan(http_client)
    response = await http_client.post(
        "/api/v1/tasks", json={"title": "task", "plan_id": plan_id},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


# ============================================================================
# Files: strict base64


# ============================================================================


class TestFileBase64Api:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("garbage", GARBAGE_DATA)
    async def test_create_with_garbage_data_is_rejected_and_nothing_is_stored(
        self, http_client, garbage,
    ):
        response = await http_client.post("/api/v1/files", json=_file_payload(garbage))

        assert response.status_code == 400, response.text
        listing = await http_client.get("/api/v1/files")
        assert listing.json()["total"] == 0

    @pytest.mark.asyncio
    @pytest.mark.parametrize("garbage", GARBAGE_DATA)
    async def test_update_with_garbage_data_keeps_existing_content(
        self, http_client, garbage,
    ):
        created = await http_client.post("/api/v1/files", json=_file_payload())
        assert created.status_code == 201, created.text
        file_id = created.json()["id"]

        response = await http_client.put(f"/api/v1/files/{file_id}", json={"data": garbage})

        assert response.status_code == 400, response.text
        fetched = await http_client.get(f"/api/v1/files/{file_id}")
        assert fetched.status_code == 200
        assert fetched.json()["data"] == GOOD_DATA
        assert fetched.json()["size_bytes"] == len(b"hello world")

    @pytest.mark.asyncio
    async def test_line_wrapped_base64_is_still_stored(self, http_client):
        wrapped = base64.encodebytes(b"x" * 200).decode()

        response = await http_client.post("/api/v1/files", json=_file_payload(wrapped))

        assert response.status_code == 201, response.text
        assert response.json()["size_bytes"] == 200
        fetched = await http_client.get(f"/api/v1/files/{response.json()['id']}")
        assert base64.b64decode(fetched.json()["data"]) == b"x" * 200

    @pytest.mark.asyncio
    async def test_zero_byte_file_stored_earlier_stays_readable_and_deletable(
        self, sqlite_app, http_client,
    ):
        created = await http_client.post("/api/v1/files", json=_file_payload())
        file_id = created.json()["id"]
        db_adapter = sqlite_app.file_service.file_repo.db_adapter
        async with db_adapter.system_session() as session:
            await session.execute(
                update(FilesTable)
                .where(FilesTable.id == file_id)
                .values(data=b"", size_bytes=0),
            )

        fetched = await http_client.get(f"/api/v1/files/{file_id}")
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["data"] == ""

        deleted = await http_client.delete(f"/api/v1/files/{file_id}")
        assert deleted.status_code == 200, deleted.text

    @pytest.mark.asyncio
    async def test_mcp_create_file_with_garbage_data_is_rejected(self, mcp_client):
        with pytest.raises(ToolError):
            await mcp_client.call_tool("execute_forgetful_tool", {
                "tool_name": "create_file",
                "arguments": _file_payload("!!!!"),
            })

        listing = await mcp_client.call_tool(
            "execute_forgetful_tool", {"tool_name": "list_files", "arguments": {}},
        )
        assert listing.data["files"] == []


# ============================================================================
# Code artifacts: verbatim code


# ============================================================================


class TestCodeArtifactVerbatimApi:
    @pytest.mark.asyncio
    async def test_create_and_update_round_trip_code_unchanged(self, http_client):
        created = await http_client.post("/api/v1/code-artifacts", json={
            "title": "t", "description": "d", "code": INDENTED_CODE, "language": "python",
        })
        assert created.status_code == 201, created.text
        artifact_id = created.json()["id"]
        assert created.json()["code"] == INDENTED_CODE

        fetched = await http_client.get(f"/api/v1/code-artifacts/{artifact_id}")
        assert fetched.json()["code"] == INDENTED_CODE

        new_code = "\tif x:\n\t\tpass\n\n"
        updated = await http_client.put(
            f"/api/v1/code-artifacts/{artifact_id}", json={"code": new_code},
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["code"] == new_code


# ============================================================================
# Plans, tasks, criteria: blank text


# ============================================================================


class TestBlankPlanningTextApi:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("blank", BLANKS)
    async def test_create_plan_with_blank_title_is_rejected(self, http_client, blank):
        project_id = await _create_project(http_client)

        response = await http_client.post(
            "/api/v1/plans", json={"title": blank, "project_id": project_id},
        )

        assert response.status_code == 400, response.text
        assert "cannot be empty or whitespace only" in response.text

    @pytest.mark.asyncio
    @pytest.mark.parametrize("blank", BLANKS)
    async def test_update_plan_with_blank_title_is_rejected(self, http_client, blank):
        plan_id = await _create_plan(http_client)

        response = await http_client.put(f"/api/v1/plans/{plan_id}", json={"title": blank})

        assert response.status_code == 400, response.text
        assert (await http_client.get(f"/api/v1/plans/{plan_id}")).json()["title"] == "plan"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("blank", BLANKS)
    async def test_create_task_with_blank_title_is_rejected(self, http_client, blank):
        plan_id = await _create_plan(http_client)

        response = await http_client.post("/api/v1/tasks", json={"title": blank, "plan_id": plan_id})

        assert response.status_code == 400, response.text

    @pytest.mark.asyncio
    @pytest.mark.parametrize("blank", BLANKS)
    async def test_update_task_with_blank_title_is_rejected(self, http_client, blank):
        task_id = await _create_task(http_client)

        response = await http_client.put(f"/api/v1/tasks/{task_id}", json={"title": blank})

        assert response.status_code == 400, response.text
        assert (await http_client.get(f"/api/v1/tasks/{task_id}")).json()["title"] == "task"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("blank", BLANKS)
    async def test_add_criterion_with_blank_description_is_rejected(self, http_client, blank):
        task_id = await _create_task(http_client)

        response = await http_client.post(
            f"/api/v1/tasks/{task_id}/criteria", json={"description": blank},
        )

        assert response.status_code == 400, response.text

    @pytest.mark.asyncio
    @pytest.mark.parametrize("blank", BLANKS)
    async def test_update_criterion_with_blank_description_is_rejected(self, http_client, blank):
        task_id = await _create_task(http_client)
        created = await http_client.post(
            f"/api/v1/tasks/{task_id}/criteria", json={"description": "real"},
        )
        criterion_id = created.json()["id"]

        response = await http_client.put(
            f"/api/v1/criteria/{criterion_id}", json={"description": blank},
        )

        assert response.status_code == 400, response.text

    @pytest.mark.asyncio
    async def test_padded_titles_are_trimmed_and_met_only_update_still_works(self, http_client):
        project_id = await _create_project(http_client)
        plan = await http_client.post(
            "/api/v1/plans", json={"title": "  padded  ", "project_id": project_id},
        )
        assert plan.json()["title"] == "padded"

        task = await http_client.post(
            "/api/v1/tasks", json={"title": "  task  ", "plan_id": plan.json()["id"]},
        )
        assert task.json()["title"] == "task"

        criterion = await http_client.post(
            f"/api/v1/tasks/{task.json()['id']}/criteria", json={"description": "  done  "},
        )
        assert criterion.json()["description"] == "done"
        met_only = await http_client.put(
            f"/api/v1/criteria/{criterion.json()['id']}", json={"met": True},
        )
        assert met_only.status_code == 200, met_only.text
        assert met_only.json()["description"] == "done"

    @pytest.mark.asyncio
    async def test_mcp_create_plan_with_blank_title_is_rejected(self, mcp_client):
        project = await mcp_client.call_tool("execute_forgetful_tool", {
            "tool_name": "create_project",
            "arguments": {"name": "p", "description": "d", "project_type": "development"},
        })
        project_id = project.data["id"]

        with pytest.raises(ToolError):
            await mcp_client.call_tool("execute_forgetful_tool", {
                "tool_name": "create_plan",
                "arguments": {"title": "   ", "project_id": project_id},
            })

    @pytest.mark.asyncio
    async def test_plan_stored_with_blank_title_earlier_stays_readable_and_deletable(
        self, sqlite_app, http_client,
    ):
        plan_id = await _create_plan(http_client)
        db_adapter = sqlite_app.plan_service.plan_repo.db_adapter
        async with db_adapter.system_session() as session:
            await session.execute(update(PlansTable).where(PlansTable.id == plan_id).values(title=""))

        fetched = await http_client.get(f"/api/v1/plans/{plan_id}")
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["title"] == ""

        deleted = await http_client.delete(f"/api/v1/plans/{plan_id}")
        assert deleted.status_code == 200, deleted.text


