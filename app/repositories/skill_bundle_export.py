"""Snapshot-consistent export: authorization and exact sizes precede body loading."""
from types import SimpleNamespace

from sqlalchemy import (
    Integer,
    LargeBinary,
    String,
    case,
    cast,
    false,
    func,
    literal,
    select,
    union_all,
)

from app.config.settings import settings
from app.exceptions import BundleReadDeniedError, NotFoundError
from app.models.skill_bundle_models import (
    SkillBundleSnapshot,
    bundle_resource_bytes,
    bundle_text_bytes,
    project_bundle_resource,
    validate_bundle_paths,
)
from app.utils.skill_markdown import format_bundle_skill_markdown


def selection(table, skill_id, members):
    if members is None:
        return table
    validate_bundle_paths([m.path for m in members])
    rows = [select(
        literal(skill_id, Integer).label("skill_id"), literal(m.path, String).label("path"),
        literal(m.kind, String).label("kind"),
        *[literal(m.resource_id if m.kind == kind else None, Integer).label(key)
          for kind, key in (("document", "document_id"), ("code_artifact", "code_artifact_id"), ("file", "file_id"))],
    ) for m in members]
    if not rows:
        rows = [select(literal(skill_id, Integer).label("skill_id"),
                       literal(None, String).label("path"), literal(None, String).label("kind"),
                       *[literal(None, Integer).label(k) for k in ("document_id", "code_artifact_id", "file_id")]).where(false())]
    return union_all(*rows).subquery("selected_bundle_members")


def metadata_statement(tables, skill_id, members, allowed_kinds, user_id, sqlite):
    skill, membership, resources, links = tables
    chosen = selection(membership, skill_id, members)
    # A denied selection returns no resource metadata, even when ordinary CRUD
    # has stored values that cannot pass portable-bundle validation.
    denied = select(func.count()).select_from(chosen).where(
        chosen.c.skill_id == skill_id, chosen.c.kind.not_in(sorted(allowed_kinds)),
    ).correlate(None).scalar_subquery() > 0
    columns = [skill, chosen.c.path, chosen.c.kind]
    statement = select().select_from(skill).outerjoin(chosen, chosen.c.skill_id == skill.id)
    for kind, table in resources.items():
        key = {"document": "document_id", "code_artifact": "code_artifact_id", "file": "file_id"}[kind]
        statement = statement.outerjoin(table, (table.id == chosen.c[key]) & (table.user_id == user_id))
        link = links[kind]
        statement = statement.outerjoin(link, (link.c.skill_id == skill.id) & (link.c[key] == chosen.c[key]))
        columns += [chosen.c[key].label(kind + "_selected_id"), table.id.label(kind + "_id"), link.c[key].label(kind + "_linked")]
        fields = {"document": ("title", "description", "document_type", "tags"),
                  "code_artifact": ("title", "description", "language", "tags"),
                  "file": ("description", "mime_type", "tags")}[kind]
        columns += [case((~denied, getattr(table, f))).label(kind + "_" + f) for f in fields]
        body = getattr(table, {"document": "content", "code_artifact": "code", "file": "data"}[kind])
        size = func.length(cast(body, LargeBinary)) if sqlite else func.octet_length(body)
        columns.append(case((~denied, size)).label(kind + "_body_bytes"))
    return statement.with_only_columns(*columns).where(skill.id == skill_id, skill.user_id == user_id).order_by(chosen.c.path)


async def read_bodies(session, resources, selected):
    values = {}
    # One body SELECT, using UNION ALL to preserve each kind's native ID space.
    parts = []
    for kind, table in resources.items():
        ids = {r["id"] for r in selected if r["kind"] == kind}
        if not ids:
            continue
        body = getattr(table, {"document": "content", "code_artifact": "code", "file": "data"}[kind])
        # Separate typed columns avoid PostgreSQL text/bytea UNION coercion.
        parts.append(select(literal(kind).label("kind"), table.id,
                            body.label("text_body") if kind != "file" else cast(literal(None), String).label("text_body"),
                            body.label("binary_body") if kind == "file" else cast(literal(None), LargeBinary).label("binary_body"))
                     .where(table.id.in_(ids), table.user_id == selected[0]["user_id"]))
    if parts:
        for kind, native_id, text_body, binary_body in (await session.execute(union_all(*parts))).all():
            values[kind, native_id] = binary_body if kind == "file" else text_body
    return values


async def read_bundle(repo, tables, user_id, skill_id, members, allowed_kinds, sqlite):
    if members is not None and len(members) > settings.SKILL_BUNDLE_MAX_RESOURCES:
        denied = {m.kind for m in members} - allowed_kinds
        if denied:
            raise BundleReadDeniedError(denied)
        raise ValueError("Bundle resource count exceeds SKILL_BUNDLE_MAX_RESOURCES")
    resources = tables[2]
    statement = metadata_statement(tables, skill_id, members, allowed_kinds, user_id, sqlite)
    async with repo.db_adapter.snapshot_session(user_id) as session:
        rows = await repo._read_bundle_metadata(session, statement)
        if not rows:
            raise NotFoundError(f"Skill {skill_id} not found")
        denied = {r.kind for r in rows if r.path is not None} - allowed_kinds
        if denied:
            raise BundleReadDeniedError(denied)
        selected = []
        for row in rows:
            if row.path is None:
                continue
            kind = row.kind
            data = row._mapping
            native_id, present, linked = [data[kind + suffix] for suffix in ("_selected_id", "_id", "_linked")]
            if present is None and (members is not None or native_id is not None):
                raise NotFoundError(f"Bundle member '{row.path}' not found")
            if native_id is None or present is None:
                raise ValueError(f"Bundle member '{row.path}' was deleted")
            if linked is None:
                raise ValueError(f"Bundle member '{row.path}' was unlinked")
            fields = {k[len(kind) + 1:]: v for k, v in data.items() if isinstance(k, str) and k.startswith(kind + "_")}
            selected.append(dict(path=row.path, kind=kind, id=present, user_id=user_id, **{
                k: v for k, v in fields.items() if k not in {"id", "selected_id", "linked"}
            }))
        selected.sort(key=lambda item: item["path"])
        if len(selected) > settings.SKILL_BUNDLE_MAX_RESOURCES:
            raise ValueError("Bundle resource count exceeds SKILL_BUNDLE_MAX_RESOURCES")
        skill = repo._to_skill(rows[0][0])
        total = bundle_text_bytes(format_bundle_skill_markdown(skill))
        for item in selected:
            total += item["body_bytes"] + bundle_resource_bytes({k: v for k, v in item.items() if k not in {"id", "user_id", "body_bytes"}})
        if total > settings.SKILL_BUNDLE_MAX_BYTES:
            raise ValueError("Bundle exceeds SKILL_BUNDLE_MAX_BYTES")
        bodies = await repo._read_bundle_bodies(session, resources, selected)
        # No conversion (especially base64) until both the exact total and every
        # body length are proven against the same metadata snapshot.
        for item in selected:
            body = bodies[item["kind"], item["id"]]
            size = len(body if isinstance(body, bytes) else body.encode("utf-8"))
            if size != item["body_bytes"]:
                raise RuntimeError("Bundle snapshot body length changed")
        portable = []
        for item in selected:
            fields = {k: v for k, v in item.items() if k not in {"path", "kind", "id", "user_id", "body_bytes"}}
            fields[{"document": "content", "code_artifact": "code", "file": "data"}[item["kind"]]] = bodies[item["kind"], item["id"]]
            portable.append(project_bundle_resource(item["path"], item["kind"], SimpleNamespace(**fields)))
        return SkillBundleSnapshot(skill=skill, resources=portable)
