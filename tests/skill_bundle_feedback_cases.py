"""Owner feedback regressions exercised on both native database backends."""
import ast
import base64
import copy
import difflib
import json
from unittest.mock import AsyncMock

import pytest
from fastmcp.exceptions import ToolError
from sqlalchemy import text

from app.config.settings import settings
from app.exceptions import NotFoundError
from tests.skill_bundle_cases import call_tool, skill_bundle


def payload_size(bundle):
    def strings(value):
        if isinstance(value, str):
            return len(value.encode("utf-8"))
        if isinstance(value, list):
            return sum(strings(v) for v in value)
        if isinstance(value, dict):
            return sum(strings(v) for v in value.values())
        return 0
    total = strings(bundle["skill_md"])
    for resource in bundle["resources"]:
        value = dict(resource)
        data = value.pop("data", None)
        if value["kind"] == "document":
            value.setdefault("document_type", "text")
        total += strings(value) + (len(base64.b64decode(data)) if data is not None else 0)
    return total


async def reject_without_mutation(client, bundle_app, monkeypatch, value):
    tools = [("list_skills", "skills"), ("list_documents", "documents"),
             ("list_files", "files"), ("list_code_artifacts", "code_artifacts")]
    before = {tool: {row["id"] for row in (await call_tool(client, tool))[key]}
              for tool, key in tools}
    adapter = bundle_app.skill_service.skill_repo.db_adapter
    async with adapter.system_session() as session:
        bindings = (await session.execute(text("SELECT COUNT(*) FROM skill_bundle_resources"))).scalar_one()
    embedding = AsyncMock(side_effect=AssertionError("under-limit import embedded"))
    with monkeypatch.context() as patch:
        patch.setattr(bundle_app.skill_service.skill_repo.embedding_adapter, "generate_embedding", embedding)
        with pytest.raises(ToolError, match="SKILL_BUNDLE_MAX_BYTES"):
            await call_tool(client, "import_skill_bundle", bundle=value)
    assert embedding.await_count == 0
    for tool, key in tools:
        assert {row["id"] for row in (await call_tool(client, tool))[key]} == before[tool]
    async with adapter.system_session() as session:
        assert (await session.execute(text("SELECT COUNT(*) FROM skill_bundle_resources"))).scalar_one() == bindings


def check_help(info):
    schema = info["json_schema"]
    definitions = schema["$defs"]
    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "$ref":
                    assert item.startswith("#/$defs/") and item[8:] in definitions
                else:
                    walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
    walk(schema)
    assert info["examples"]
    if info["name"] == "import_skill_bundle":
        for name, fields in {"BundleDocument": {"path", "title", "description", "content"},
                             "BundleCodeArtifact": {"path", "title", "description", "code", "language"},
                             "BundleFile": {"path", "description", "data", "mime_type"}}.items():
            assert fields <= set(definitions[name]["required"])
        assert "after commit" in info["description"]
    else:
        assert {"path", "kind", "resource_id"} <= set(definitions["SkillBundleMember"]["required"])


def example_arguments(example):
    node = ast.parse(example, mode="eval").body
    assert isinstance(node, ast.Call) and node.func.id == "execute_forgetful_tool"
    return ast.literal_eval(node.args[0]), ast.literal_eval(node.args[1])


class SkillBundleFeedbackCases:
    @pytest.mark.parametrize("explicit", [False, True])
    @pytest.mark.parametrize("invalid", ["nul", "file_limit"])
    async def test_denied_export_never_loads_or_converts_body(self, mcp_client, bundle_app, monkeypatch, explicit, invalid):
        import sys

        from app.routes.mcp.scope_resolver import parse_scopes, resolve_permitted_tools

        value = skill_bundle("export-auth")
        value["resources"] = [value["resources"][2]]
        value["resources"][0].update(data="c2VjcmV0", tags=["CONFIDENTIAL"])
        created = await call_tool(mcp_client, "import_skill_bundle", bundle=value)
        if invalid == "nul":
            # PostgreSQL rejects NUL in TEXT, so use the lowered per-file limit
            # there; SQLite additionally exercises the exact normal-limit report.
            if "sqlite" in bundle_app.skill_service.skill_repo.__module__:
                await call_tool(mcp_client, "update_file", file_id=created["members"][0]["resource_id"], description="binary" + chr(0))
            else:
                monkeypatch.setattr(settings, "FILE_MAX_SIZE_BYTES", 1)
        else:
            monkeypatch.setattr(settings, "FILE_MAX_SIZE_BYTES", 1)
        repo = bundle_app.skill_service.skill_repo
        original = sys.modules[repo.__module__].file_model
        conversions = []
        monkeypatch.setattr(sys.modules[repo.__module__], "file_model", lambda row: (conversions.append(row), original(row))[1])
        body_reads = AsyncMock(side_effect=AssertionError("denied export fetched bodies"))
        monkeypatch.setattr(repo, "_read_bundle_bodies", body_reads, raising=False)
        scopes = parse_scopes("read:skills")
        monkeypatch.setattr(bundle_app, "_instance_scopes", scopes, raising=False)
        monkeypatch.setattr(bundle_app, "_instance_permitted_tools", resolve_permitted_tools(scopes, bundle_app.registry), raising=False)
        arguments = {"skill_id": created["skill"]["id"]}
        if explicit:
            arguments["members"] = created["members"]
        with pytest.raises(ToolError, match="get_file") as error:
            await call_tool(mcp_client, "export_skill_bundle", **arguments)
        assert not any(v in str(error.value) for v in ("CONFIDENTIAL", "c2VjcmV0", "input_value"))
        assert conversions == [] and body_reads.await_count == 0

    async def test_authorized_invalid_export_is_sanitized(self, mcp_client, monkeypatch):
        value = skill_bundle("safe-error")
        value["resources"] = [value["resources"][2]]
        value["resources"][0].update(data="c2VjcmV0", tags=["CONFIDENTIAL"])
        created = await call_tool(mcp_client, "import_skill_bundle", bundle=value)
        monkeypatch.setattr(settings, "FILE_MAX_SIZE_BYTES", 1)
        with pytest.raises(ToolError) as error:
            await call_tool(mcp_client, "export_skill_bundle", skill_id=created["skill"]["id"])
        assert not any(v in str(error.value) for v in ("CONFIDENTIAL", "c2VjcmV0", "input_value"))

    @pytest.mark.parametrize("metadata_heavy", [False, True])
    async def test_budget_precedes_body_fetch(self, mcp_client, bundle_app, monkeypatch, metadata_heavy):
        value = skill_bundle("size-guard")
        value["resources"] = [value["resources"][2]]
        value["resources"][0]["data"] = base64.b64encode(b"x" * (1 if metadata_heavy else 1024)).decode()
        value["resources"][0]["tags"] = ["metadata" * 20] if metadata_heavy else []
        created = await call_tool(mcp_client, "import_skill_bundle", bundle=value)
        member = created["members"][0]
        members = [dict(member, path=f"assets/copy-{i}.bin") for i in range(3 if metadata_heavy else 100)]
        monkeypatch.setattr(settings, "SKILL_BUNDLE_MAX_BYTES", 512)
        reads = AsyncMock(side_effect=AssertionError("oversize export fetched bodies"))
        monkeypatch.setattr(bundle_app.skill_service.skill_repo, "_read_bundle_bodies", reads, raising=False)
        with pytest.raises(ToolError, match="SKILL_BUNDLE_MAX_BYTES"):
            await call_tool(mcp_client, "export_skill_bundle", skill_id=created["skill"]["id"], members=members)
        assert reads.await_count == 0

    async def test_export_exact_cap_and_repeated_ids(self, mcp_client, monkeypatch):
        value = skill_bundle("exact-export")
        value["resources"][0]["document_type"] = "text"
        created = await call_tool(mcp_client, "import_skill_bundle", bundle=value)
        members = created["members"] + [dict(created["members"][0], path="references/repeated.md")]
        exported = await call_tool(mcp_client, "export_skill_bundle", skill_id=created["skill"]["id"], members=members)
        size = payload_size(exported)
        monkeypatch.setattr(settings, "SKILL_BUNDLE_MAX_BYTES", size)
        assert await call_tool(mcp_client, "export_skill_bundle", skill_id=created["skill"]["id"], members=members) == exported
        monkeypatch.setattr(settings, "SKILL_BUNDLE_MAX_BYTES", size - 1)
        with pytest.raises(ToolError, match="SKILL_BUNDLE_MAX_BYTES"):
            await call_tool(mcp_client, "export_skill_bundle", skill_id=created["skill"]["id"], members=members)

    @pytest.mark.parametrize("mixed", [False, True])
    async def test_canonical_import_rejected_before_embedding(self, mcp_client, bundle_app, monkeypatch, mixed):
        value = {"schema_version": 1, "skill_md": "---\nname: x\ndescription: x\n---\nx", "resources": []}
        if mixed:
            value["resources"] = copy.deepcopy(skill_bundle()["resources"])
            value["resources"][0]["content"] = "café"
            value["resources"][1]["code"] = "print('ready')"
        cap = payload_size(value)
        monkeypatch.setattr(settings, "SKILL_BUNDLE_MAX_BYTES", cap)
        embedding = AsyncMock(side_effect=AssertionError("rejected canonical import embedded"))
        monkeypatch.setattr(bundle_app.skill_service.skill_repo.embedding_adapter, "generate_embedding", embedding)
        with pytest.raises(ToolError, match="SKILL_BUNDLE_MAX_BYTES"):
            await call_tool(mcp_client, "import_skill_bundle", bundle=value)
        assert embedding.await_count == 0
        assert (await call_tool(mcp_client, "list_skills"))["skills"] == []
        assert (await call_tool(mcp_client, "list_documents"))["documents"] == []
        assert (await call_tool(mcp_client, "list_files"))["files"] == []
        assert (await call_tool(mcp_client, "list_code_artifacts"))["code_artifacts"] == []
        async with bundle_app.skill_service.skill_repo.db_adapter.system_session() as session:
            assert (await session.execute(text("SELECT COUNT(*) FROM skill_bundle_resources"))).scalar_one() == 0

    async def test_canonical_exact_limit_and_integer_metadata_key(self, mcp_client, monkeypatch):
        from app.services.skill_service import (
            format_skill_markdown,
            parse_skill_markdown,
        )
        value = {"schema_version": 1, "skill_md": "---\nname: x\ndescription: x\nmetadata:\n  1: value\n---\nx", "resources": []}
        skill = parse_skill_markdown(value["skill_md"], None, 7)
        skill = skill.model_copy(update={"metadata": json.loads(json.dumps(skill.metadata))})
        canonical = format_skill_markdown(skill)
        monkeypatch.setattr(settings, "SKILL_BUNDLE_MAX_BYTES", max(len(value["skill_md"].encode()), len(canonical.encode())))
        created = await call_tool(mcp_client, "import_skill_bundle", bundle=value)
        exported = await call_tool(mcp_client, "export_skill_bundle", skill_id=created["skill"]["id"])
        assert exported["skill_md"] == canonical

    async def test_detailed_help_and_examples(self, mcp_client):
        docs = {}
        for tool in ("import_skill_bundle", "export_skill_bundle"):
            result = await mcp_client.call_tool("how_to_use_forgetful_tool", {"tool_name": tool})
            check_help(result.data)
            docs[tool] = result.data
        tool, arguments = example_arguments(docs["import_skill_bundle"]["examples"][0])
        created = await call_tool(mcp_client, tool, **arguments)
        for example in docs["export_skill_bundle"]["examples"]:
            tool, arguments = example_arguments(example)
            arguments["skill_id"] = created["skill"]["id"]
            if "members" in arguments:
                arguments["members"][0]["resource_id"] = created["members"][0]["resource_id"]
            exported = await call_tool(mcp_client, tool, **arguments)
            assert exported["resources"][0]["content"] == "Run the checks before deploying."

    async def test_native_text_length_and_isolation(self, bundle_app, mcp_client):
        adapter = bundle_app.skill_service.skill_repo.db_adapter
        sqlite = "sqlite" in type(adapter).__module__
        async with adapter.snapshot_session(None) as session:
            if not sqlite:
                assert (await session.execute(text("SHOW server_encoding"))).scalar_one() == "UTF8"
                assert (await session.execute(text("SHOW transaction_isolation"))).scalar_one() == "repeatable read"
            query = "SELECT length(CAST(:value AS BLOB))" if sqlite else "SELECT octet_length(CAST(:value AS TEXT))"
            assert (await session.execute(text(query), {"value": "café😀"})).scalar_one() == len("café😀".encode())
        if not sqlite:
            async with adapter.session(None) as session:
                assert (await session.execute(text("SHOW transaction_isolation"))).scalar_one() == "read committed"

    @pytest.mark.parametrize("mutation", ["grow", "tags", "unlink", "delete"])
    async def test_export_snapshot_survives_concurrent_commit(self, bundle_app, mcp_client, monkeypatch, tmp_path, mutation):
        from app.models.skill_bundle_models import SkillBundle
        from app.models.user_models import UserCreate
        from app.services.skill_service import SkillService

        original_repo = bundle_app.skill_service.skill_repo
        sqlite = "sqlite" in original_repo.__module__
        owned = None
        if sqlite:
            from app.repositories.sqlite.skill_repository import SqliteSkillRepository
            from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter
            from app.repositories.sqlite.sqlite_tables import (
                DocumentsTable,
                skill_document_association,
            )
            from app.repositories.sqlite.user_repository import SqliteUserRepository
            with monkeypatch.context() as config:
                config.setattr(settings, "SQLITE_MEMORY", False)
                config.setattr(settings, "SQLITE_PATH", str(tmp_path / "bundle-snapshot.db"))
                owned = SqliteDatabaseAdapter()
                await owned.init_db()
            user = await SqliteUserRepository(owned).create_user(UserCreate(
                external_id="snapshot-owner", name="Snapshot owner", email="snapshot@example.test"))
            repo = SqliteSkillRepository(owned, original_repo.embedding_adapter)
        else:
            from app.repositories.postgres.postgres_tables import (
                DocumentsTable,
                skill_document_association,
            )
            user = await bundle_app.user_service.get_or_create_user(UserCreate(
                external_id="snapshot-owner", name="Snapshot owner", email="snapshot@example.test"))
            repo = original_repo
        service = SkillService(repo)
        value = skill_bundle("snapshot-case")
        value["resources"] = [value["resources"][0]]
        try:
            created = await service.import_skill_bundle(user.id, SkillBundle.model_validate(value))
            kinds = frozenset({"document", "code_artifact", "file"})
            before = await service.export_skill_bundle(user.id, created.skill.id, allowed_kinds=kinds)
            monkeypatch.setattr(settings, "SKILL_BUNDLE_MAX_BYTES", payload_size(before.model_dump()))
            member = created.members[0]
            read_metadata = repo._read_bundle_metadata
            writer_done = []
            async def interleave(session, statement):
                rows = await read_metadata(session, statement)
                async with repo.db_adapter.session(user.id) as writer:
                    if mutation == "grow":
                        await writer.execute(DocumentsTable.__table__.update().where(DocumentsTable.id == member.resource_id).values(content="grown" * 200))
                    elif mutation == "tags":
                        await writer.execute(DocumentsTable.__table__.update().where(DocumentsTable.id == member.resource_id).values(tags=["larger-tag" * 20]))
                    elif mutation == "unlink":
                        await writer.execute(skill_document_association.delete().where(skill_document_association.c.document_id == member.resource_id))
                    else:
                        await writer.execute(DocumentsTable.__table__.delete().where(DocumentsTable.id == member.resource_id))
                writer_done.append(True)
                return rows
            with monkeypatch.context() as patch:
                patch.setattr(repo, "_read_bundle_metadata", interleave)
                current = await service.export_skill_bundle(user.id, created.skill.id, allowed_kinds=kinds)
            assert writer_done == [True] and current == before
            with pytest.raises((ValueError, NotFoundError)) as error:
                await service.export_skill_bundle(user.id, created.skill.id, allowed_kinds=kinds)
            assert any(word in str(error.value) for word in ("SKILL_BUNDLE_MAX_BYTES", "unlinked", "deleted", "not found"))
        finally:
            if owned is not None:
                await owned._engine.dispose()

    @pytest.mark.parametrize("mixed", [False, True])
    async def test_accepted_canonical_import_at_exact_cap(self, mcp_client, bundle_app, monkeypatch, mixed):
        value = {"schema_version": 1, "skill_md": "---\nname: boundary\ndescription: Boundary\n---\nx", "resources": []}
        if mixed:
            value["resources"] = copy.deepcopy(skill_bundle()["resources"])
            value["resources"][0]["content"] = "café"
            value["resources"][1]["code"] = "print('ready')"
        first = await call_tool(mcp_client, "import_skill_bundle", bundle=value)
        canonical = await call_tool(mcp_client, "export_skill_bundle", skill_id=first["skill"]["id"])
        await call_tool(mcp_client, "delete_skill", skill_id=first["skill"]["id"])
        cap = payload_size(canonical)
        assert payload_size(value) <= cap
        monkeypatch.setattr(settings, "SKILL_BUNDLE_MAX_BYTES", cap - 1)
        await reject_without_mutation(mcp_client, bundle_app, monkeypatch, value)
        monkeypatch.setattr(settings, "SKILL_BUNDLE_MAX_BYTES", cap)
        second = await call_tool(mcp_client, "import_skill_bundle", bundle=value)
        assert await call_tool(mcp_client, "export_skill_bundle", skill_id=second["skill"]["id"]) == canonical

    @pytest.mark.parametrize("tools", [None, [], ["Read"]])
    async def test_bundle_optional_tools_exact_boundary(self, mcp_client, bundle_app, monkeypatch, tools):
        from app.models.skill_models import Skill
        from app.utils.skill_markdown import (
            format_bundle_skill_markdown,
            format_skill_markdown,
            parse_skill_markdown,
        )

        tag_names = [chr(97 + i) for i in range(10)]
        tool_line = "" if tools is None else "allowed-tools: " + json.dumps(tools) + "\n"
        markdown = "---\nname: x\ndescription: x\ntags: [" + ",".join(tag_names) + "]\n" + tool_line + "---\nx"
        value = {"schema_version": 1, "skill_md": markdown, "resources": []}
        canonical = format_bundle_skill_markdown(parse_skill_markdown(markdown, None, 7))
        assert ("allowed-tools:" in canonical) == bool(tools)
        cap = len(canonical.encode())
        assert len(markdown.encode()) <= cap
        monkeypatch.setattr(settings, "SKILL_BUNDLE_MAX_BYTES", cap - 1)
        embedding = AsyncMock(side_effect=AssertionError("under-limit import embedded"))
        with monkeypatch.context() as patch:
            patch.setattr(bundle_app.skill_service.skill_repo.embedding_adapter, "generate_embedding", embedding)
            with pytest.raises(ToolError, match="SKILL_BUNDLE_MAX_BYTES"):
                await call_tool(mcp_client, "import_skill_bundle", bundle=value)
        assert embedding.await_count == 0
        for tool, key in [("list_skills", "skills"), ("list_documents", "documents"),
                          ("list_files", "files"), ("list_code_artifacts", "code_artifacts")]:
            assert (await call_tool(mcp_client, tool))[key] == []
        async with bundle_app.skill_service.skill_repo.db_adapter.system_session() as session:
            assert (await session.execute(text("SELECT COUNT(*) FROM skill_bundle_resources"))).scalar_one() == 0
        monkeypatch.setattr(settings, "SKILL_BUNDLE_MAX_BYTES", cap)
        created = await call_tool(mcp_client, "import_skill_bundle", bundle=value)
        exported = await call_tool(mcp_client, "export_skill_bundle", skill_id=created["skill"]["id"])
        diff = "".join(difflib.unified_diff(canonical.splitlines(True), exported["skill_md"].splitlines(True)))
        assert exported["skill_md"] == canonical, (len(canonical.encode()), len(exported["skill_md"].encode()), diff[:4000])
        stored = await call_tool(mcp_client, "get_skill", skill_id=created["skill"]["id"])
        legacy = await mcp_client.call_tool("execute_forgetful_tool", {
            "tool_name": "export_skill", "arguments": {"skill_id": created["skill"]["id"]},
        })
        assert legacy.content[0].text == format_skill_markdown(Skill.model_validate(stored))

    async def test_nested_metadata_canonical_boundary(self, mcp_client, monkeypatch):
        from app.utils.skill_markdown import (
            format_bundle_skill_markdown,
            parse_skill_markdown,
        )

        markdown = "---\nname: x\ndescription: x\nmetadata:\n  z: [{z: 2, a: 1}, b, a]\n  1: value\n  a: {z: 2, a: 1}\n---\nx"
        value = {"schema_version": 1, "skill_md": markdown, "resources": []}
        canonical = format_bundle_skill_markdown(parse_skill_markdown(markdown, None, 7))
        assert canonical.index("\n  '1':") < canonical.index("\n  a:") < canonical.index("\n  z:")
        assert "  - b\n  - a" in canonical
        assert len(markdown.encode()) <= len(canonical.encode())
        monkeypatch.setattr(settings, "SKILL_BUNDLE_MAX_BYTES", len(canonical.encode()))
        created = await call_tool(mcp_client, "import_skill_bundle", bundle=value)
        exported = await call_tool(mcp_client, "export_skill_bundle", skill_id=created["skill"]["id"])
        diff = "".join(difflib.unified_diff(canonical.splitlines(True), exported["skill_md"].splitlines(True)))
        assert exported["skill_md"] == canonical, (len(canonical.encode()), len(exported["skill_md"].encode()), diff[:4000])

    async def test_null_document_type_persisted_budget(self, mcp_client, bundle_app, monkeypatch):
        value = {"schema_version": 1, "skill_md": "---\nname: x\ndescription: x\n---\nx", "resources": [
            {"kind": "document", "path": "a.md", "title": "Doc", "description": "Test", "content": "text", "document_type": None},
        ]}
        first = await call_tool(mcp_client, "import_skill_bundle", bundle=value)
        canonical = await call_tool(mcp_client, "export_skill_bundle", skill_id=first["skill"]["id"])
        assert canonical["resources"][0]["document_type"] == "text"
        await call_tool(mcp_client, "delete_skill", skill_id=first["skill"]["id"])
        cap = payload_size(canonical)
        assert payload_size(value) <= cap
        monkeypatch.setattr(settings, "SKILL_BUNDLE_MAX_BYTES", cap - 1)
        await reject_without_mutation(mcp_client, bundle_app, monkeypatch, value)
        monkeypatch.setattr(settings, "SKILL_BUNDLE_MAX_BYTES", cap)
        second = await call_tool(mcp_client, "import_skill_bundle", bundle=value)
        assert await call_tool(mcp_client, "export_skill_bundle", skill_id=second["skill"]["id"]) == canonical
