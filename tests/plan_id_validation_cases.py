"""MCP plan ID validation cases shared by SQLite and PostgreSQL."""

import pytest
from fastmcp.exceptions import ToolError

from tests.task_action_validation_cases import call


async def setup_plans(client):
    projects = []
    plans = []
    for suffix in ("first", "second"):
        project = await call(
            client,
            "create_project",
            name=f"Plan ID validation {suffix}",
            description="MCP plan ID validation regression",
            project_type="development",
        )
        plan = await call(
            client,
            "create_plan",
            project_id=project["id"],
            title=f"Validation {suffix}",
        )
        projects.append(project)
        plans.append(plan)
    return projects, plans


async def snapshot_all_plans(client):
    result = await call(client, "list_plans")
    return result["plans"]


def encode_id(value, representation):
    return {
        "int": value,
        "float": float(value),
        "string": str(value),
        "spaced": f" {value} ",
    }[representation]


def id_error(tool_name, field):
    return rf"Failed to execute '{tool_name}': {field} (?:cannot|must)"


class PlanIdValidationCases:
    @pytest.mark.parametrize("value", [True, None, "", "1.5", 1.5, [], {}])
    async def test_invalid_update_plan_ids_never_mutate(self, mcp_client, value):
        await setup_plans(mcp_client)
        before = await snapshot_all_plans(mcp_client)

        with pytest.raises(ToolError, match=id_error("update_plan", "plan_id")):
            await call(
                mcp_client,
                "update_plan",
                plan_id=value,
                title="changed",
            )

        assert await snapshot_all_plans(mcp_client) == before

    @pytest.mark.parametrize("value", [True, None, "", "1.5", 1.5, [], {}])
    async def test_invalid_create_plan_project_ids_never_mutate(
        self, mcp_client, value,
    ):
        await setup_plans(mcp_client)
        before = await snapshot_all_plans(mcp_client)

        with pytest.raises(ToolError, match=id_error("create_plan", "project_id")):
            await call(
                mcp_client,
                "create_plan",
                project_id=value,
                title="Invalid project ID",
            )

        assert await snapshot_all_plans(mcp_client) == before

    @pytest.mark.parametrize("value", [True, None, "", "1.5", 1.5, [], {}])
    async def test_invalid_get_plan_ids_raise(self, mcp_client, value):
        await setup_plans(mcp_client)

        with pytest.raises(ToolError, match=id_error("get_plan", "plan_id")):
            await call(mcp_client, "get_plan", plan_id=value)

    @pytest.mark.parametrize("value", [True, False, "", "1.5", 1.5, [], {}])
    async def test_invalid_list_plan_project_ids_raise(self, mcp_client, value):
        await setup_plans(mcp_client)

        with pytest.raises(ToolError, match=id_error("list_plans", "project_id")):
            await call(mcp_client, "list_plans", project_id=value)

    async def test_list_plans_none_project_id_is_no_filter(self, mcp_client):
        _, plans = await setup_plans(mcp_client)

        result = await call(mcp_client, "list_plans", project_id=None)

        assert {plan["id"] for plan in result["plans"]} == {
            plan["id"] for plan in plans
        }

    @pytest.mark.parametrize("action", ["get_plan", "update_plan"])
    @pytest.mark.parametrize("representation", ["int", "float", "string", "spaced"])
    async def test_plan_id_compatibility(self, mcp_client, action, representation):
        _, plans = await setup_plans(mcp_client)
        target = plans[1]
        plan_id = encode_id(target["id"], representation)

        if action == "get_plan":
            result = await call(mcp_client, action, plan_id=plan_id)
        else:
            untouched_before = await call(
                mcp_client,
                "get_plan",
                plan_id=plans[0]["id"],
            )
            result = await call(
                mcp_client,
                action,
                plan_id=plan_id,
                title=f"Updated via {representation}",
            )

        assert result["id"] == target["id"]
        if action == "update_plan":
            saved = await call(mcp_client, "get_plan", plan_id=target["id"])
            assert saved["title"] == f"Updated via {representation}"
            untouched_after = await call(
                mcp_client,
                "get_plan",
                plan_id=plans[0]["id"],
            )
            assert untouched_after == untouched_before

    @pytest.mark.parametrize("action", ["create_plan", "list_plans"])
    @pytest.mark.parametrize("representation", ["int", "float", "string", "spaced"])
    async def test_project_id_compatibility(self, mcp_client, action, representation):
        projects, plans = await setup_plans(mcp_client)
        target = projects[1]
        project_id = encode_id(target["id"], representation)

        if action == "create_plan":
            result = await call(
                mcp_client,
                action,
                project_id=project_id,
                title=f"Created via {representation}",
            )
            assert result["project_id"] == target["id"]
        else:
            result = await call(mcp_client, action, project_id=project_id)
            assert result["total_count"] == 1
            assert result["plans"][0]["id"] == plans[1]["id"]
