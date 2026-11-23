"""Real clients and internal invariants must retain their full collections."""
from types import SimpleNamespace

import pytest
from fastmcp import Client
from sqlalchemy import update

from app.config.settings import settings
from app.routes.cli.local_executor import LocalExecutor
from app.routes.cli.remote_executor import RemoteExecutor
from app.routes.cli.verbs import resolve_project, run
from app.routes.mcp.scope_resolver import parse_scopes, resolve_permitted_tools
from tests.list_pagination_cases import RESOURCES, endpoint, seed

TOOLS = {resource: ("query_tasks" if resource == "tasks" else "list_" + resource)
         for resource in RESOURCES}


class PaginationCompatibilityCases:
    @pytest.mark.parametrize("resource", RESOURCES)
    async def test_mcp_lists_remain_complete_above_one_hundred(self, pagination_environment, resource):
        environment = pagination_environment
        created, params = await seed(environment, resource, 105)
        async with Client(environment.mcp) as client:
            result = await client.call_tool("execute_forgetful_tool", {
                "tool_name": TOOLS[resource], "arguments": params,
            })
        data = result.data
        assert data is not None
        assert data["total_count"] == 105
        assert {row["id"] for row in data[resource]} == {row["id"] for row in created}

    async def test_local_and_remote_cli_resolve_and_list_project_after_one_hundred(self, pagination_environment):
        environment = pagination_environment
        created, _ = await seed(environment, "projects", 105)
        target = created[0]  # Newest-first REST default would exclude this oldest project.
        scopes = parse_scopes(settings.FORGETFUL_SCOPES)
        runtime = SimpleNamespace(
            services=SimpleNamespace(user=environment.mcp.user_service),
            registry=environment.mcp.registry,
            permitted_tools=resolve_permitted_tools(scopes, environment.mcp.registry),
            instance_scopes=scopes,
        )
        local = LocalExecutor(runtime)
        remote = RemoteExecutor("http://127.0.0.1:8020", token="synthetic-local-fixture",
                                client_factory=lambda _url, _token: Client(environment.mcp))
        try:
            for executor in (local, remote):
                assert await resolve_project(executor, target["name"]) == target["id"]
                result, rendered = await run(executor, SimpleNamespace(command="project"))
                assert len(result["projects"]) == 105
                assert target["name"] in rendered
        finally:
            await remote.close()

    async def test_graph_nodes_and_file_edges_after_one_hundred_survive(self, pagination_environment):
        environment = pagination_environment
        projects, _ = await seed(environment, "projects", 105)
        owner_project = projects[0]["id"]
        files, _ = await seed(environment, "files", 105, project_id=owner_project)
        response = await environment.client.get("/api/v1/graph", params={
            "node_types": "project,file", "limit": 1000,
        })
        assert response.status_code == 200, response.text
        graph = response.json()
        assert {f"project_{row['id']}" for row in projects}.issubset({node["id"] for node in graph["nodes"]})
        assert {f"file_{row['id']}" for row in files}.issubset({node["id"] for node in graph["nodes"]})
        assert any(edge["source"] == f"file_{files[0]['id']}" and edge["target"] == f"project_{owner_project}"
                   for edge in graph["edges"])
        subgraph = await environment.client.get("/api/v1/graph/subgraph", params={
            "node_id": f"project_{owner_project}", "depth": 1, "max_nodes": 200,
            "node_types": "project,file",
        })
        assert subgraph.status_code == 200, subgraph.text
        data = subgraph.json()
        assert f"file_{files[0]['id']}" in {node["id"] for node in data["nodes"]}
        assert any(edge["source"] == f"file_{files[0]['id']}" and edge["target"] == f"project_{owner_project}"
                   for edge in data["edges"])

    async def test_nonterminal_task_after_one_hundred_blocks_auto_completion(self, pagination_environment):
        environment = pagination_environment
        tasks, params = await seed(environment, "tasks", 106)
        table = environment.table("tasks")
        async with environment.adapter.system_session() as session:
            await session.execute(update(table).where(table.c.id.in_([row["id"] for row in tasks[:104]])).values(state="done"))
        user = await environment.user()
        assert not await environment.mcp.task_service._plan_tasks_allow_completion(user.id, params["plan_id"])
        for index in (104, 105):
            url = f"{endpoint('tasks')}/{tasks[index]['id']}/transition"
            version = tasks[index]["version"]
            for state in ("doing", "done"):
                response = await environment.client.post(url, json={"state": state, "version": version})
                assert response.status_code == 200, response.text
                assert response.json()["state"] == state
                version = response.json()["version"]
            plan = await environment.client.get(f"/api/v1/plans/{params['plan_id']}")
            assert plan.status_code == 200, plan.text
            assert plan.json()["status"] == ("active" if index == 104 else "completed")
