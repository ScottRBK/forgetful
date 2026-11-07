# Portable skill bundles

A version 1 JSON bundle contains `schema_version: 1`, a `skill_md` string and a
`resources` list. Each resource has a package-relative `path` and one `kind`:

- `document`: `title`, `description`, `content`, optional `document_type` and `tags`.
- `code_artifact`: `title`, `description`, `code`, `language`, optional `tags`.
- `file`: `description`, strict base64 `data`, `mime_type`, optional `tags`.

No resource IDs, project IDs or provenance fields belong in this portable data.
Import returns destination IDs separately. The destination `project_id` applies
to the skill and every resource; ordinary provenance defaults apply there.

## Import and export

Invoke `import_skill_bundle` with `bundle`, optional `project_id` and `importance`.
Invoke `export_skill_bundle` with `skill_id`. Discovery returns their current
schemas. The legacy `import_skill` and `export_skill` retain their Markdown-only
inputs and response types.

REST accepts `POST /api/v1/skills/bundle/import` with
`{"bundle": {...}, "project_id": null, "importance": 7}` and read-only
`POST /api/v1/skills/{skill_id}/bundle/export` with `{}`.
MCP and local CLI require permission for the skill operation and each resource's
ordinary create/read tool. REST follows the existing identity and ownership
model; it does not implement MCP tool scopes. Binary members also require
`FILES_ENABLED`; all bundle operations require `SKILLS_ENABLED`.

For an existing skill with separately linked resources, export accepts an explicit
`members` list: `[{"path": "references/example.md", "kind": "document",
"resource_id": 123}]`. Each ID must be owned and linked. The list replaces stored
membership for that export only and saves nothing. Default export uses the paths
stored at bundle import, not every object connected to the knowledge graph.
Deleting or unlinking a member makes default export fail explicitly.

The generic CLI uses JSON in `--args`; it has no stdin/file input mode. Keep CLI
arguments below the operating system's argument-size limits (on Linux a single
argument is limited to about 128 KiB). Use REST or MCP for larger bundles. This
feature does not change the CLI parser or install skills in a local directory.

## Validation and persistence

Paths are NFC, portable relative file paths, at most 500 characters and 32
segments. Absolute paths, traversal, reserved device names, control characters,
backslashes, trailing dots/spaces and casefold/file-directory collisions are
rejected. `SKILL.md` is reserved. Nothing is extracted to a filesystem, executed
or fetched from a network.

`SKILL_BUNDLE_MAX_RESOURCES` defaults to 100 and `SKILL_BUNDLE_MAX_BYTES` to
20,971,520 decoded bytes, counting UTF-8 text and decoded binary. Existing
per-resource limits still apply. Text must be valid UTF-8 without NUL. Empty or
whitespace-only documents/scripts and zero-byte binary files are unsupported by
the existing resource models and rejected before mutation. Text uses their
existing surrounding-whitespace stripping; script language is lower-cased.
Binary content is preserved byte for byte. Export/import/export is stable after
that canonicalisation. Required titles, descriptions, language and MIME types
must be supplied; import never invents them silently.

The repository stores the skill, embedding, resources, ordinary graph links and
package membership in one transaction. Validation failure creates nothing.
Creation activity events are emitted after commit, using existing event types;
file snapshots exclude data. An activity failure after commit does not roll back
the package. Do not automatically retry a failed response assuming no records
were committed. Skill-name checking preserves the existing behavior and does
not introduce a database uniqueness guarantee.

Export reads the skill, bindings, links and current contents in one SQL statement.
It does not traverse memories or unrelated graph neighbors, and does not claim to
prove every Markdown link resolves. Callers choose the resources forming the
package; external URLs are left unchanged.
