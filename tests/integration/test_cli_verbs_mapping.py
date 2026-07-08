"""Integration tests for curated verb flag -> tool-argument mapping (phase 5)

Verbs are exercised through the real argparse tree against a recording executor, so
these tests pin the exact registry arguments each flag combination produces -
including project name -> id resolution via list_projects.
"""
import pytest

from app.routes.cli import verbs
from app.routes.cli.parser import build_parser


class RecordingExecutor:
    """ToolExecutor double that records execute() calls and returns canned payloads."""

    def __init__(self, responses=None):
        self.calls = []
        self._responses = dict(responses or {})

    async def execute(self, tool_name, arguments):
        self.calls.append((tool_name, dict(arguments)))
        return self._responses.get(tool_name, {})

    async def close(self):
        pass


def _args(argv):
    return build_parser().parse_args(argv)


PROJECT_LISTING = {
    "projects": [
        {"id": 4, "name": "Forgetful", "project_type": "development", "status": "active"},
        {"id": 7, "name": "Homelab", "project_type": "personal", "status": "active"},
    ],
    "total_count": 2,
}

QUERY_RESULT = {"query": "q", "primary_memories": [], "linked_memories": [], "total_count": 0, "token_count": 0}


async def test_search_maps_flags_onto_query_memory_arguments():
    executor = RecordingExecutor({"query_memory": QUERY_RESULT})

    await verbs.run(executor, _args(
        ["memory", "search", "dns fix", "-n", "5", "-c", "debugging wsl", "-p", "3"],
    ))

    assert executor.calls == [(
        "query_memory",
        {"query": "dns fix", "query_context": "debugging wsl", "k": 5, "project_ids": [3]},
    )]


async def test_search_defaults_query_context_and_omits_optionals():
    executor = RecordingExecutor({"query_memory": QUERY_RESULT})

    await verbs.run(executor, _args(["memory", "search", "dns fix"]))

    assert executor.calls == [(
        "query_memory",
        {"query": "dns fix", "query_context": "cli search"},
    )]


async def test_save_maps_flags_onto_create_memory_arguments():
    executor = RecordingExecutor({"create_memory": {"id": 9, "title": "T"}})

    await verbs.run(executor, _args(
        ["memory", "save", "some content", "--title", "T", "--importance", "8", "-p", "3"],
    ))

    tool_name, arguments = executor.calls[0]
    assert tool_name == "create_memory"
    assert arguments["title"] == "T"
    assert arguments["content"] == "some content"
    assert arguments["importance"] == 8
    assert arguments["project_ids"] == [3]
    assert arguments["keywords"] == []
    assert arguments["tags"] == []
    assert arguments["context"]  # a non-empty default context is supplied


async def test_get_and_recent_map_arguments():
    executor = RecordingExecutor({
        "get_memory": {"id": 12, "title": "T", "importance": 5},
        "get_recent_memories": {"memories": [], "total_count": 0},
    })

    await verbs.run(executor, _args(["memory", "get", "12"]))
    await verbs.run(executor, _args(["memory", "recent", "-n", "3"]))

    assert executor.calls[0] == ("get_memory", {"memory_id": 12})
    assert executor.calls[1] == ("get_recent_memories", {"limit": 3})


async def test_project_name_resolves_to_id_via_list_projects():
    executor = RecordingExecutor({
        "list_projects": PROJECT_LISTING,
        "query_memory": QUERY_RESULT,
    })

    await verbs.run(executor, _args(["memory", "search", "dns", "-p", "forgetful"]))

    assert executor.calls[0] == ("list_projects", {})
    assert executor.calls[1][1]["project_ids"] == [4]


async def test_unknown_project_name_raises_with_available_names():
    executor = RecordingExecutor({"list_projects": PROJECT_LISTING})

    with pytest.raises(Exception) as excinfo:
        await verbs.run(executor, _args(["memory", "search", "dns", "-p", "nope"]))

    message = str(excinfo.value)
    assert "nope" in message
    assert "Forgetful" in message
    assert "Homelab" in message


async def test_project_list_renders_human_lines():
    executor = RecordingExecutor({"list_projects": PROJECT_LISTING})

    payload, human = await verbs.run(executor, _args(["project", "list"]))

    assert executor.calls == [("list_projects", {})]
    assert payload["total_count"] == 2
    assert "Forgetful" in human
    assert "Homelab" in human
