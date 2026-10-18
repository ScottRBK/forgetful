"""Skill name uniqueness on create, rename and migration with SQLite."""

import asyncio

import pytest
from fastmcp.exceptions import ToolError

from app.config.settings import settings
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter
from tests.skill_name_uniqueness_cases import (
    TestSkillNameUniquenessStorage as TestSkillNameUniquenessStorage,
)
from tests.skill_name_uniqueness_cases import skill_store as skill_store


@pytest.fixture
async def skill_db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATABASE", "SQLite")
    monkeypatch.setattr(settings, "SQLITE_MEMORY", False)
    monkeypatch.setattr(settings, "SQLITE_PATH", str(tmp_path / "skill-names.db"))
    adapter = SqliteDatabaseAdapter()
    await adapter.init_db()
    try:
        yield adapter
    finally:
        await adapter.dispose()


def skill_payload(name: str) -> dict:
    return {
        "name": name,
        "description": f"description for {name}",
        "content": f"# {name}\n\nSome procedural content.",
        "tags": ["t"],
        "importance": 5,
    }


async def list_names(http_client) -> list[str]:
    listing = (await http_client.get("/api/v1/skills")).json()["skills"]
    return sorted(skill["name"] for skill in listing)


class TestSkillRenameAPI:
    async def test_rename_to_existing_name_is_rejected(self, http_client):
        await http_client.post("/api/v1/skills", json=skill_payload("skill-a"))
        created = await http_client.post("/api/v1/skills", json=skill_payload("skill-b"))
        path = f"/api/v1/skills/{created.json()['id']}"

        response = await http_client.put(path, json={"name": "skill-a"})

        assert response.status_code == 400
        assert "already exists" in response.json()["error"]
        assert await list_names(http_client) == ["skill-a", "skill-b"]
        assert (await http_client.get(path)).json()["name"] == "skill-b"

    async def test_rename_to_own_or_free_name_still_works(self, http_client):
        created = await http_client.post("/api/v1/skills", json=skill_payload("skill-a"))
        path = f"/api/v1/skills/{created.json()['id']}"

        same = await http_client.put(path, json={"name": "skill-a", "importance": 9})
        renamed = await http_client.put(path, json={"name": "skill-z"})

        assert same.status_code == 200
        assert same.json()["importance"] == 9
        assert renamed.status_code == 200
        assert await list_names(http_client) == ["skill-z"]

    async def test_create_after_rename_checks_the_new_name(self, http_client):
        created = await http_client.post("/api/v1/skills", json=skill_payload("skill-a"))
        await http_client.put(f"/api/v1/skills/{created.json()['id']}", json={"name": "skill-b"})

        taken = await http_client.post("/api/v1/skills", json=skill_payload("skill-b"))
        freed = await http_client.post("/api/v1/skills", json=skill_payload("skill-a"))

        assert taken.status_code == 400
        assert freed.status_code == 201


class TestSimultaneousSkillWritesAPI:
    """Requests racing in one process share the in-memory connection: exactly one may win."""

    async def test_simultaneous_creates_of_the_same_name(self, http_client):
        await list_names(http_client)  # let the first request create the default user
        responses = await asyncio.gather(
            *(http_client.post("/api/v1/skills", json=skill_payload("racing")) for _ in range(2)),
        )

        assert sorted(r.status_code for r in responses) == [201, 400]
        assert await list_names(http_client) == ["racing"]
        assert (await http_client.post("/api/v1/skills", json=skill_payload("next"))).status_code == 201

    async def test_simultaneous_renames_to_the_same_name(self, http_client):
        ids = [
            (await http_client.post("/api/v1/skills", json=skill_payload(name))).json()["id"]
            for name in ("skill-a", "skill-b")
        ]

        responses = await asyncio.gather(
            *(http_client.put(f"/api/v1/skills/{i}", json={"name": "target"}) for i in ids),
        )

        assert sorted(r.status_code for r in responses) == [200, 400]
        assert sorted(await list_names(http_client)) in (["skill-a", "target"], ["skill-b", "target"])


class TestSkillRenameMCP:
    async def test_update_skill_tool_rejects_existing_name(self, mcp_client):
        async def call(tool_name, **arguments):
            result = await mcp_client.call_tool(
                "execute_forgetful_tool", {"tool_name": tool_name, "arguments": arguments},
            )
            return result.data

        await call("create_skill", **skill_payload("tool-skill-a"))
        second = await call("create_skill", **skill_payload("tool-skill-b"))

        with pytest.raises(ToolError, match="already exists"):
            await call("update_skill", skill_id=second["id"], name="tool-skill-a")

        assert (await call("get_skill", skill_id=second["id"]))["name"] == "tool-skill-b"
