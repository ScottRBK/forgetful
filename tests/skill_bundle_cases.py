"""The same package workflows must pass through real SQLite and PostgreSQL MCP."""
import base64
import copy

import pytest
from fastmcp.exceptions import ToolError


def skill_bundle(name="portable-procedure"):
    return {
        "schema_version": 1,
        "skill_md": (f"---\nname: {name}\ndescription: Portable procedure\n"
                     "metadata:\n  author: package-test\n---\n\n"
                     "Read [reference](references/nested/refresh.md), run "
                     "[script](scripts/run.py), and use [asset](assets/icon.bin)."),
        "resources": [
            {"kind": "document", "path": "references/nested/refresh.md",
             "title": "Refresh", "description": "Reference text", "content": "  café refresh\n",
             "document_type": "markdown", "tags": ["reference"]},
            {"kind": "code_artifact", "path": "scripts/run.py", "title": "Run",
             "description": "Run script", "code": "  print('ready')\n", "language": "Python"},
            {"kind": "file", "path": "assets/icon.bin", "description": "Binary asset",
             "mime_type": "application/octet-stream", "data": base64.b64encode(b"\x00\xffasset").decode()},
        ],
    }


async def call_tool(client, tool, **arguments):
    result = await client.call_tool("execute_forgetful_tool", {
        "tool_name": tool, "arguments": arguments,
    })
    assert result.data is not None
    return result.data


class SkillBundleCases:
    async def test_bundle_roundtrip_new_resource_ids(self, mcp_client):
        original = await call_tool(mcp_client, "import_skill_bundle", bundle=skill_bundle())
        exported = await call_tool(mcp_client, "export_skill_bundle", skill_id=original["skill"]["id"])
        assert [r["path"] for r in exported["resources"]] == sorted(r["path"] for r in skill_bundle()["resources"])
        by_kind = {r["kind"]: r for r in exported["resources"]}
        assert by_kind["document"]["content"] == "café refresh"
        assert by_kind["code_artifact"]["language"] == "python"
        assert base64.b64decode(by_kind["file"]["data"]) == b"\x00\xffasset"
        assert "package-test" in exported["skill_md"]
        assert all("resource_id" not in r and "id" not in r for r in exported["resources"])
        await call_tool(mcp_client, "delete_skill", skill_id=original["skill"]["id"])
        recreated = await call_tool(mcp_client, "import_skill_bundle", bundle=exported)
        assert {(m["kind"], m["resource_id"]) for m in original["members"]}.isdisjoint(
            {(m["kind"], m["resource_id"]) for m in recreated["members"]},
        )
        second = await call_tool(mcp_client, "export_skill_bundle", skill_id=recreated["skill"]["id"])
        assert second == exported

    @pytest.mark.parametrize("kind", ["document", "code_artifact", "file"])
    @pytest.mark.parametrize("operation", ["delete", "unlink"])
    async def test_missing_member_is_not_silently_lost(self, mcp_client, kind, operation):
        created = await call_tool(mcp_client, "import_skill_bundle", bundle=skill_bundle())
        member = next(m for m in created["members"] if m["kind"] == kind)
        key = {"document": "document_id", "code_artifact": "artifact_id", "file": "file_id"}[kind]
        args = {key: member["resource_id"]}
        tool = f"delete_{kind}"
        if operation == "unlink":
            tool = f"unlink_skill_from_{kind}"
            if kind == "code_artifact":
                args = {"code_artifact_id": member["resource_id"]}
            args["skill_id"] = created["skill"]["id"]
        await call_tool(mcp_client, tool, **args)
        with pytest.raises(ToolError, match="deleted|unlinked"):
            await call_tool(mcp_client, "export_skill_bundle", skill_id=created["skill"]["id"])

    async def test_legacy_linked_reference_explicit_export(self, mcp_client):
        skill = await call_tool(mcp_client, "import_skill", skill_md_content=skill_bundle()["skill_md"])
        document = await call_tool(mcp_client, "create_document", title="Reference",
                                   description="Existing linked document", content="Reference content")
        await call_tool(mcp_client, "link_skill_to_document", skill_id=skill["id"], document_id=document["id"])
        mapping = [{"kind": "document", "path": "references/nested/refresh.md", "resource_id": document["id"]}]
        exported = await call_tool(mcp_client, "export_skill_bundle", skill_id=skill["id"], members=mapping)
        assert exported["resources"][0]["content"] == "Reference content"
        # Explicit mapping is read-only, not silently stored as membership.
        default = await call_tool(mcp_client, "export_skill_bundle", skill_id=skill["id"])
        assert default["resources"] == []

    async def test_unlinked_explicit_id_is_refused(self, mcp_client):
        skill = await call_tool(mcp_client, "import_skill", skill_md_content=skill_bundle()["skill_md"])
        document = await call_tool(mcp_client, "create_document", title="Not linked",
                                   description="Must not export", content="Private content")
        with pytest.raises(ToolError, match="unlinked"):
            await call_tool(mcp_client, "export_skill_bundle", skill_id=skill["id"], members=[{
                "kind": "document", "path": "references/private.md", "resource_id": document["id"],
            }])

    @pytest.mark.parametrize("path", ["../escape", "/absolute", "a/../b", "a//b", "SKILL.md",
                                       "C:/file", "a\\b", "a/", "nul.txt", "a/CON", "a."])
    async def test_invalid_paths_have_no_side_effects(self, mcp_client, path):
        value = skill_bundle()
        value["resources"][0]["path"] = path
        with pytest.raises(ToolError):
            await call_tool(mcp_client, "import_skill_bundle", bundle=value)
        listed = await call_tool(mcp_client, "list_skills")
        assert listed["skills"] == []
        assert (await call_tool(mcp_client, "list_documents"))["documents"] == []

    @pytest.mark.parametrize("field,value", [("content", "\x00"), ("content", "   ")])
    async def test_invalid_text_rejected_before_storage(self, mcp_client, field, value):
        bundle = skill_bundle()
        bundle["resources"][0][field] = value
        with pytest.raises(ToolError, match="NUL|empty|whitespace|at least"):
            await call_tool(mcp_client, "import_skill_bundle", bundle=bundle)
        assert (await call_tool(mcp_client, "list_skills"))["skills"] == []

    async def test_collision_rejected_before_storage(self, mcp_client):
        bundle = skill_bundle()
        duplicate = copy.deepcopy(bundle["resources"][0])
        duplicate["path"] = duplicate["path"].upper()
        bundle["resources"].append(duplicate)
        with pytest.raises(ToolError):
            await call_tool(mcp_client, "import_skill_bundle", bundle=bundle)
        assert (await call_tool(mcp_client, "list_skills"))["skills"] == []

    async def test_legacy_markdown_still_has_original_shape(self, mcp_client):
        created = await call_tool(mcp_client, "import_skill", skill_md_content=skill_bundle()["skill_md"])
        assert "id" in created and "members" not in created
        # Scalar results travel in MCP text, so inspect the actual text response.
        result = await mcp_client.call_tool("execute_forgetful_tool", {
            "tool_name": "export_skill", "arguments": {"skill_id": created["id"]},
        })
        assert result.content and "portable-procedure" in result.content[0].text

    async def test_component_scope_denial_has_no_writes(self, mcp_client, bundle_app, monkeypatch):
        from app.routes.mcp.scope_resolver import parse_scopes, resolve_permitted_tools

        scopes = parse_scopes("write:skills,read")
        monkeypatch.setattr(bundle_app, "_instance_scopes", scopes, raising=False)
        monkeypatch.setattr(bundle_app, "_instance_permitted_tools", resolve_permitted_tools(
            scopes, bundle_app.registry,
        ), raising=False)
        with pytest.raises(ToolError, match="create_"):
            await call_tool(mcp_client, "import_skill_bundle", bundle=skill_bundle())
        assert (await call_tool(mcp_client, "list_skills"))["skills"] == []

    async def test_binary_feature_disabled_before_any_write(self, mcp_client, monkeypatch):
        from app.config.settings import settings

        monkeypatch.setattr(settings, "FILES_ENABLED", False)
        with pytest.raises(ToolError, match="disabled"):
            await call_tool(mcp_client, "import_skill_bundle", bundle=skill_bundle())
        assert (await call_tool(mcp_client, "list_skills"))["skills"] == []
        # Reference-only packages do not depend on the Files feature.
        value = skill_bundle()
        value["resources"] = value["resources"][:2]
        created = await call_tool(mcp_client, "import_skill_bundle", bundle=value)
        assert len(created["members"]) == 2

    async def test_midway_database_failure_rolls_back_all_records(self, mcp_client, bundle_app):
        from sqlalchemy import event

        engine = bundle_app.skill_service.skill_repo.db_adapter._engine.sync_engine
        inserts = 0

        def fail_second_member(connection, cursor, statement, parameters, context, executemany):
            nonlocal inserts
            if statement.lstrip().upper().startswith("INSERT INTO SKILL_BUNDLE_RESOURCES"):
                inserts += 1
                if inserts == 2:
                    raise RuntimeError("synthetic bundle transaction failure")

        event.listen(engine, "before_cursor_execute", fail_second_member)
        try:
            with pytest.raises(ToolError):
                await call_tool(mcp_client, "import_skill_bundle", bundle=skill_bundle())
        finally:
            event.remove(engine, "before_cursor_execute", fail_second_member)
        assert inserts == 2
        assert (await call_tool(mcp_client, "list_skills"))["skills"] == []
        assert (await call_tool(mcp_client, "list_documents"))["documents"] == []
        assert (await call_tool(mcp_client, "list_code_artifacts"))["code_artifacts"] == []
        assert (await call_tool(mcp_client, "list_files"))["files"] == []

    async def test_events_follow_commit_and_redact_binary(self, mcp_client, bundle_app, monkeypatch):
        events = []

        async def capture(**event):
            events.append(event)

        monkeypatch.setattr(bundle_app.skill_service, "_emit_event", capture)
        created = await call_tool(mcp_client, "import_skill_bundle", bundle=skill_bundle())
        assert len(events) == 4
        from app.models.activity_models import EntityType
        binary = next(event for event in events if event["entity_type"] == EntityType.FILE)
        assert "data" not in binary["snapshot"]
        assert binary["snapshot"]["size_bytes"] == len(b"\x00\xffasset")
        assert events[-1]["entity_id"] == created["skill"]["id"]

    async def test_postcommit_event_failure_preserves_whole_package(self, mcp_client, bundle_app, monkeypatch):
        async def fail(**event):
            raise RuntimeError("synthetic event delivery failure")

        monkeypatch.setattr(bundle_app.skill_service, "_emit_event", fail)
        with pytest.raises(ToolError):
            await call_tool(mcp_client, "import_skill_bundle", bundle=skill_bundle())
        skills = (await call_tool(mcp_client, "list_skills"))["skills"]
        assert len(skills) == 1
        bundle = await call_tool(mcp_client, "export_skill_bundle", skill_id=skills[0]["id"])
        assert len(bundle["resources"]) == 3

    async def test_export_reads_one_statement(self, mcp_client, bundle_app):
        from sqlalchemy import event

        created = await call_tool(mcp_client, "import_skill_bundle", bundle=skill_bundle())
        statements = []
        engine = bundle_app.skill_service.skill_repo.db_adapter._engine.sync_engine

        def count(connection, cursor, statement, parameters, context, executemany):
            if statement.lstrip().upper().startswith("SELECT") and "skills" in statement:
                statements.append(statement)

        event.listen(engine, "before_cursor_execute", count)
        try:
            await call_tool(mcp_client, "export_skill_bundle", skill_id=created["skill"]["id"])
        finally:
            event.remove(engine, "before_cursor_execute", count)
        assert len(statements) == 1
        assert "skill_bundle_resources" in statements[0]

    async def test_existing_create_conversion_matches_bundle(self, mcp_client):
        value = skill_bundle()
        created = await call_tool(mcp_client, "import_skill_bundle", bundle=value)
        for resource in value["resources"]:
            kind = resource["kind"]
            arguments = {key: val for key, val in resource.items() if key not in {"kind", "path"}}
            if kind in {"document", "file"}:
                arguments["filename"] = resource["path"].rsplit("/", 1)[-1]
            ordinary = await call_tool(mcp_client, "create_" + kind, **arguments)
            member = next(m for m in created["members"] if m["kind"] == kind)
            bundled = await call_tool(mcp_client, "get_" + kind, **{{"document": "document_id", "code_artifact": "artifact_id", "file": "file_id"}[kind]: member["resource_id"]})
            ignored = {"id", "created_at", "updated_at"}
            assert {k: v for k, v in ordinary.items() if k not in ignored} == {
                k: v for k, v in bundled.items() if k not in ignored
            }

    async def test_foreign_owner_never_exported(self, mcp_client, bundle_app):
        from app.models.user_models import UserCreate

        created = await call_tool(mcp_client, "import_skill_bundle", bundle=skill_bundle())
        other = await bundle_app.user_service.get_or_create_user(UserCreate(
            external_id="bundle-other", name="Other bundle owner", email="other@example.test",
        ))
        adapter = bundle_app.skill_service.skill_repo.db_adapter
        if adapter._engine.dialect.name == "sqlite":
            from app.repositories.sqlite.sqlite_tables import DocumentsTable
            owner = str(other.id)
        else:
            from app.repositories.postgres.postgres_tables import DocumentsTable
            owner = other.id
        member = next(m for m in created["members"] if m["kind"] == "document")
        # Arrange a corrupt cross-owner association to verify the export boundary,
        # not a normal operation that already prevents such a link.
        async with adapter.system_session() as session:
            await session.execute(DocumentsTable.__table__.update().where(
                DocumentsTable.id == member["resource_id"],
            ).values(user_id=owner))
        with pytest.raises(ToolError, match="not found"):
            await call_tool(mcp_client, "export_skill_bundle", skill_id=created["skill"]["id"])

    @pytest.mark.parametrize("when", ["before_commit", "after_commit"])
    async def test_cancellation_preserves_transaction_boundary(self, mcp_client, bundle_app, monkeypatch, when):
        import asyncio

        from sqlalchemy import event

        from app.config.settings import settings
        from app.models.skill_bundle_models import SkillBundle
        from app.models.user_models import UserCreate

        user = await bundle_app.user_service.get_or_create_user(UserCreate(
            external_id=settings.DEFAULT_USER_ID, name=settings.DEFAULT_USER_NAME,
            email=settings.DEFAULT_USER_EMAIL,
        ))
        service = bundle_app.skill_service
        engine = service.skill_repo.db_adapter._engine.sync_engine

        def cancel_insert(connection, cursor, statement, parameters, context, executemany):
            if statement.lstrip().upper().startswith("INSERT INTO SKILL_BUNDLE_RESOURCES"):
                raise asyncio.CancelledError()

        async def cancel_event(**event):
            raise asyncio.CancelledError()

        if when == "before_commit":
            event.listen(engine, "before_cursor_execute", cancel_insert)
        else:
            monkeypatch.setattr(service, "_emit_event", cancel_event)
        try:
            with pytest.raises(asyncio.CancelledError):
                await service.import_skill_bundle(user.id, SkillBundle.model_validate(skill_bundle()))
        finally:
            if when == "before_commit":
                event.remove(engine, "before_cursor_execute", cancel_insert)
        skills = (await call_tool(mcp_client, "list_skills"))["skills"]
        if when == "before_commit":
            assert skills == []
            assert (await call_tool(mcp_client, "list_documents"))["documents"] == []
        else:
            assert len(skills) == 1
            bundle = await call_tool(mcp_client, "export_skill_bundle", skill_id=skills[0]["id"])
            assert len(bundle["resources"]) == 3

    async def test_sqlite_foreign_keys_actually_enabled(self, mcp_client, bundle_app):
        from sqlalchemy import text

        adapter = bundle_app.skill_service.skill_repo.db_adapter
        if adapter._engine.dialect.name != "sqlite":
            pytest.skip("SQLite only")
        async with adapter.system_session() as session:
            assert (await session.execute(text("PRAGMA foreign_keys"))).scalar_one() == 1

    async def test_rest_bundle_and_legacy_shapes(self, http_client):
        response = await http_client.post("/api/v1/skills/bundle/import", json={"bundle": skill_bundle()})
        assert response.status_code == 201, response.text
        created = response.json()
        response = await http_client.post(f"/api/v1/skills/{created['skill']['id']}/bundle/export", json={})
        assert response.status_code == 200, response.text
        assert len(response.json()["resources"]) == 3
        legacy = await http_client.get(f"/api/v1/skills/{created['skill']['id']}/export")
        assert legacy.status_code == 200
        assert set(legacy.json()) == {"skill_md"}

    async def test_large_bundle_uses_transport_not_cli_argv(self, mcp_client):
        value = skill_bundle()
        value["resources"] = [{
            "kind": "document", "path": f"references/chapter-{i}.md", "title": f"Chapter {i}",
            "description": "Large transport proof", "content": "x" * 70000,
        } for i in range(2)]
        created = await call_tool(mcp_client, "import_skill_bundle", bundle=value)
        exported = await call_tool(mcp_client, "export_skill_bundle", skill_id=created["skill"]["id"])
        assert sum(len(r["content"]) for r in exported["resources"]) == 140000

    async def test_destination_project_applies_to_all_records(self, mcp_client):
        project = await call_tool(mcp_client, "create_project", name="Bundle destination",
                                  description="Native project ownership", project_type="development")
        created = await call_tool(mcp_client, "import_skill_bundle", bundle=skill_bundle(), project_id=project["id"])
        assert created["skill"]["project_id"] == project["id"]
        for member in created["members"]:
            resource = await call_tool(mcp_client, "get_" + member["kind"], **{
                {"document": "document_id", "code_artifact": "artifact_id", "file": "file_id"}[member["kind"]]: member["resource_id"],
            })
            assert resource["project_id"] == project["id"]

    async def test_missing_project_creates_no_package(self, mcp_client):
        with pytest.raises(ToolError):
            await call_tool(mcp_client, "import_skill_bundle", bundle=skill_bundle(), project_id=999999)
        assert (await call_tool(mcp_client, "list_skills"))["skills"] == []
        assert (await call_tool(mcp_client, "list_documents"))["documents"] == []

    async def test_hidden_yaml_nul_rejected_before_any_write(self, mcp_client):
        value = skill_bundle()
        value["skill_md"] = '---\nname: hidden-nul\ndescription: "a\\0b"\n---\n\nBody'
        with pytest.raises(ToolError, match="NUL"):
            await call_tool(mcp_client, "import_skill_bundle", bundle=value)
        assert (await call_tool(mcp_client, "list_skills"))["skills"] == []
        assert (await call_tool(mcp_client, "list_documents"))["documents"] == []

    async def test_export_codepoint_order(self, mcp_client):
        paths = ["B.md", "a.md", "a-b.md", "a_b.md", "a/c.md"]
        value = skill_bundle()
        value["resources"] = [{"path": path, "kind": "document", "title": path,
                               "description": "Ordering", "content": "text"} for path in paths]
        created = await call_tool(mcp_client, "import_skill_bundle", bundle=value)
        exported = await call_tool(mcp_client, "export_skill_bundle", skill_id=created["skill"]["id"])
        assert [r["path"] for r in exported["resources"]] == sorted(paths)

    async def test_foreign_explicit_member_is_indistinguishable_from_absent(self, mcp_client, bundle_app):
        from app.models.document_models import DocumentCreate
        from app.models.user_models import UserCreate

        skill = await call_tool(mcp_client, "import_skill", skill_md_content=skill_bundle()["skill_md"])
        other = await bundle_app.user_service.get_or_create_user(UserCreate(
            external_id="bundle-explicit-other", name="Other", email="other@example.test",
        ))
        document = await bundle_app.document_service.create_document(other.id, DocumentCreate(
            title="Private", description="Must not reveal existence", content="private",
        ))
        errors = []
        for resource_id in (document.id, 99999999):
            with pytest.raises(ToolError, match="not found") as exc:
                await call_tool(mcp_client, "export_skill_bundle", skill_id=skill["id"], members=[{
                    "path": "references/private.md", "kind": "document", "resource_id": resource_id,
                }])
            errors.append(str(exc.value))
        assert errors[0] == errors[1]
        assert "unlinked" not in errors[0]

    async def test_skill_delete_cascades_only_membership(self, mcp_client, bundle_app):
        from sqlalchemy import text

        created = await call_tool(mcp_client, "import_skill_bundle", bundle=skill_bundle())
        skill_id = created["skill"]["id"]
        await call_tool(mcp_client, "delete_skill", skill_id=skill_id)
        async with bundle_app.skill_service.skill_repo.db_adapter.system_session() as session:
            count = (await session.execute(text(
                "SELECT COUNT(*) FROM skill_bundle_resources WHERE skill_id = :id",
            ), {"id": skill_id})).scalar_one()
            assert count == 0
        for member in created["members"]:
            key = {"document": "document_id", "code_artifact": "artifact_id", "file": "file_id"}[member["kind"]]
            result = await call_tool(mcp_client, "get_" + member["kind"], **{key: member["resource_id"]})
            assert result["id"] == member["resource_id"]
