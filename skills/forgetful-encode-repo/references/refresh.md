# Refresh

Loaded by `forgetful-encode-repo` Step 3 when Step 2 chose a refresh. `<base>` is the range
start: the checkpoint, a user-named baseline, or the start of a user range. `<end>` is the end
commit. Read code as it is at `<end>`; when `<end>` is not HEAD, use `git show <end>:<path>`.
The curation rules in SKILL.md govern every verdict and write. R1–R6 decide; R7 writes. When
R7 is done, return to SKILL.md Step 4.

## R1 — Read the change set

`git diff --name-status -M <base> <end>` lists every changed path with its status:

| Status | Review for |
|---|---|
| Added | New components, features, patterns, and documented decisions (R6) |
| Modified or deleted | Knowledge that cites or describes the file |
| Renamed or copied | Both paths: usually the paths change, not the facts |
| Type changed | Treat as deleted plus added |

`git log --format='%h %s' <base>..<end>` gives intent. Read a file's diff
(`git diff <base> <end> -- <path>`) when reviewing items that touch it. A comment-only or
formatting change matters only when the comment states a fact or reason the knowledge repeats.
A large range is a note for the report, not a reason to stop.

Done when: every changed path is listed with its status, and rename and copy pairs are kept
together.

## R2 — Map direct references

Page through `get_recent_memories` with `project_ids` set to this project, `sort_by`
`created_at`, `sort_order` `asc`, and `limit` 100, raising `offset` by 100 until all
`total_count` memories are collected. Build the map before this run's first write, so new
memories cannot shift the pages.

Match each memory's `source_files` against every changed path, using both paths of a rename or
copy. Compare paths relative to the repo root; an entry naming a directory matches the changed
files under it. Record `memory_id → [changed paths]`.

A match nominates the memory for review. It does not make the memory stale.

Done when: the collected count equals `total_count`, and every match is in the map.

## R3 — Search for indirect effects

The map finds only memories that cite a changed file. Knowledge can also be affected when it
has no `source_files`, cites other files, or describes behaviour the change moved.

For each changed area, run `query_memory` scoped to this project with `strict_project_filter`
true, so linked results stay in scope too. Query the concept the change touches (component,
feature, config key, command, renamed symbol), not just the filename, and let `query_context`
say this is a refresh review of `<base>..<end>`. `k` defaults to 3; raise it up to 20 primary
matches. Linked results may add more. Search ranks title, content, context, keywords, and tags;
it never reads `source_files`. A miss does not prove absence. The R2 map, not search, is the
completeness check for direct references. Re-query from another angle when results are
truncated or hint at more.

Then nominate attached knowledge:

- Documents and code artifacts linked from nominated memories (`document_ids` and
  `code_artifact_ids` in `get_memory`), and project documents and artifacts whose titles cover
  a changed area (`list_documents` and `list_code_artifacts` with the project ID).
- For each nominated document, its entry-point memories: those whose `document_ids` include it
  (visible in the R2 pages).
- Entities for touched components (`list_entities` with the project ID, `search_entities` by
  name).

Done when: every changed area has had at least one concept search, and everything those
searches and links turned up is nominated.

## R4 — Review nominated knowledge

For each nominated memory, document, and code artifact, read it in full (`get_memory`,
`get_document`, `get_code_artifact`), read the code at `<end>` and the diff, and give it a
verdict under the SKILL.md curation rules. Keep a verdict list: item, verdict, and evidence
(path and commit).

Done when: every nominated item has a verdict with evidence.

## R5 — Reconcile entities and relationships

For each entity whose component the range touched, `get_entity_relationships` with direction
`both`. Derive supported relationships from the changed code at `<end>` as well, then compare
the two sets. Checking existing edges alone misses additions between existing components:

- **Still true**: keep it.
- **Same endpoints, changed details** (type, strength, metadata): update it.
- **New relationship**: add it if absent, even when both endpoints already exist. If existing
  A starts using existing C without replacing another dependency, add A → C.
- **Contradicted**: remove it, with a replacement when the code supports one. When A
  `depends_on` B becomes A `depends_on` existing C, plan to add A → C if absent, then remove
  A → B. B stays, with its other edges and memories.
- **New component**: plan an entity per `forgetful-entities`, linked to the project, its
  memories, and its edges.
- **Removed component**: apply the entity rule in SKILL.md.

Done when: every existing edge and newly supported relationship on a touched component has a
planned outcome (keep, add, update, or remove), and every new or removed component is handled.

## R6 — Encode what is new

Added and changed code can carry knowledge nothing covers yet: components, features, patterns,
conventions, documented decisions, code worth reusing verbatim. Query before create per
`forgetful-remember` Step 3, and prefer adding a new instance to an existing memory over storing
a near-duplicate. Where to look: manifests and lockfiles for the tech stack; env, container, and
test config for setup and testing; README and contributor docs for the overview; `docs/`, ADRs,
and rationale comments for decisions.

Done when: every added path and changed area has been checked for new knowledge, with "nothing
new" recorded where that is the answer.

## R7 — Apply

When the plan changes existing knowledge, get confirmation for it as SKILL.md describes. Then
write in this order, so every replacement exists before what it replaces goes:

1. Creates: entities, documents, code artifacts, and memories, with their links.
2. Updates to existing items, keeping IDs and links.
3. Obsoletions, with `superseded_by` pointing at replacements from 1.
4. Relationships: `create_entity_relationship` for new edges, `update_entity_relationship` for
   changed details, then `delete_entity_relationship` for contradicted edges.

Check each result before the next write.

Done when: every planned write has succeeded, or is recorded as a gap.
