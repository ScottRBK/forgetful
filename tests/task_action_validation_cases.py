"""MCP task-action validation cases shared by SQLite and PostgreSQL."""

import pytest
from fastmcp.exceptions import ToolError


async def call(client, tool_name, /, **arguments):
    result = await client.call_tool(
        "execute_forgetful_tool",
        {"tool_name": tool_name, "arguments": arguments},
    )
    return result.data


async def setup_tasks(client):
    project = await call(
        client,
        "create_project",
        name="Task action validation",
        description="MCP task-action validation regression",
        project_type="development",
    )
    plan = await call(client, "create_plan", project_id=project["id"], title="Validation")
    await call(client, "update_plan", plan_id=plan["id"], status="active")
    first = await call(client, "create_task", plan_id=plan["id"], title="First task")
    second = await call(client, "create_task", plan_id=plan["id"], title="Second task")
    return first, second


async def snapshot(client, tasks):
    return [await call(client, "get_task", task_id=task["id"]) for task in tasks]


def action_arguments(action, tasks):
    first, second = tasks
    arguments = {"task_id": first["id"]}
    if action == "claim_task":
        arguments.update(agent_id="worker", version=first["version"])
    elif action == "transition_task":
        arguments.update(state="doing", version=first["version"])
    else:
        arguments["depends_on_task_id"] = second["id"]
    return arguments


class TaskActionValidationCases:
    @pytest.mark.parametrize("action", ["claim_task", "transition_task"])
    @pytest.mark.parametrize("value", [True, False, 1.0, 1.5, "1", None, [], {}])
    async def test_versions_are_strict_and_never_mutate(
        self, mcp_client, action, value,
    ):
        tasks = await setup_tasks(mcp_client)
        before = await snapshot(mcp_client, tasks)
        arguments = action_arguments(action, tasks)
        arguments["version"] = value

        with pytest.raises(ToolError, match="version"):
            await call(mcp_client, action, **arguments)

        assert await snapshot(mcp_client, tasks) == before

    @pytest.mark.parametrize("value", [True, 1, None, [], {}])
    async def test_agent_ids_are_strings_and_never_mutate(self, mcp_client, value):
        tasks = await setup_tasks(mcp_client)
        before = await snapshot(mcp_client, tasks)
        arguments = action_arguments("claim_task", tasks)
        arguments["agent_id"] = value

        with pytest.raises(ToolError, match="agent_id"):
            await call(mcp_client, "claim_task", **arguments)

        assert await snapshot(mcp_client, tasks) == before

    @pytest.mark.parametrize("value", [True, None, 1, "unknown", "DOING", "doing "])
    async def test_states_are_explicit_and_never_mutate(self, mcp_client, value):
        tasks = await setup_tasks(mcp_client)
        before = await snapshot(mcp_client, tasks)
        arguments = action_arguments("transition_task", tasks)
        arguments["state"] = value

        with pytest.raises(ToolError, match="state"):
            await call(mcp_client, "transition_task", **arguments)

        assert await snapshot(mcp_client, tasks) == before

    @pytest.mark.parametrize(
        "action,field",
        [
            ("claim_task", "task_id"),
            ("transition_task", "task_id"),
            ("add_dependency", "task_id"),
            ("add_dependency", "depends_on_task_id"),
        ],
    )
    @pytest.mark.parametrize("value", [True, None, "", "1.5", 1.5, [], {}])
    async def test_invalid_ids_never_mutate(
        self, mcp_client, action, field, value,
    ):
        tasks = await setup_tasks(mcp_client)
        before = await snapshot(mcp_client, tasks)
        arguments = action_arguments(action, tasks)
        arguments[field] = value

        with pytest.raises(ToolError, match=field):
            await call(mcp_client, action, **arguments)

        assert await snapshot(mcp_client, tasks) == before

    @pytest.mark.parametrize("action", ["claim_task", "transition_task", "add_dependency"])
    @pytest.mark.parametrize("representation", ["int", "float", "string", "spaced"])
    async def test_identifier_compatibility(self, mcp_client, action, representation):
        tasks = await setup_tasks(mcp_client)
        arguments = action_arguments(action, tasks)

        def encode(value):
            return {
                "int": value,
                "float": float(value),
                "string": str(value),
                "spaced": f" {value} ",
            }[representation]

        arguments["task_id"] = encode(tasks[0]["id"])
        if action == "add_dependency":
            arguments["depends_on_task_id"] = encode(tasks[1]["id"])

        result = await call(mcp_client, action, **arguments)
        saved = await call(mcp_client, "get_task", task_id=tasks[0]["id"])
        if action == "add_dependency":
            assert tasks[1]["id"] in saved["dependency_ids"]
        else:
            assert saved["state"] == "doing"
            assert saved["version"] == tasks[0]["version"] + 1
            assert result["id"] == tasks[0]["id"]

    @pytest.mark.parametrize("agent_id", ["", "worker"])
    async def test_string_agent_ids_are_not_rewritten(self, mcp_client, agent_id):
        first, _ = await setup_tasks(mcp_client)

        result = await call(
            mcp_client,
            "claim_task",
            task_id=first["id"],
            agent_id=agent_id,
            version=first["version"],
        )

        assert result["assigned_agent"] == agent_id

    async def test_valid_workflow_and_stale_version_conflict(self, mcp_client):
        first, second = await setup_tasks(mcp_client)
        await call(
            mcp_client,
            "add_dependency",
            task_id=first["id"],
            depends_on_task_id=second["id"],
        )
        claimed_second = await call(
            mcp_client,
            "claim_task",
            task_id=second["id"],
            agent_id="worker",
            version=second["version"],
        )
        await call(
            mcp_client,
            "transition_task",
            task_id=second["id"],
            state="done",
            version=claimed_second["version"],
        )
        claimed_first = await call(
            mcp_client,
            "claim_task",
            task_id=first["id"],
            agent_id="worker",
            version=first["version"],
        )
        before = await snapshot(mcp_client, (first, second))

        with pytest.raises(ToolError, match="[Vv]ersion"):
            await call(
                mcp_client,
                "transition_task",
                task_id=first["id"],
                state="waiting",
                version=first["version"],
            )

        assert await snapshot(mcp_client, (first, second)) == before
        waiting = await call(
            mcp_client,
            "transition_task",
            task_id=first["id"],
            state="waiting",
            version=claimed_first["version"],
        )
        assert waiting["state"] == "waiting"
