# First encode

Loaded by `forgetful-encode-repo` Step 3 when Step 2 chose a first encode. Read code at the end
commit pinned in SKILL.md; when it is not HEAD, use `git show <end>:<path>`. The curation rules
in SKILL.md govern every write. When F4 is done, return to SKILL.md Step 4.

The goal is a knowledge base a future session can lean on: the system modelled as entities, the
decisions and conventions as atomic memories, the long-form understanding as documents, all
traceable to the source.

## F1 — Resolve the project

Use the project Step 1 found. With none, `create_project` with the repo as `repo_name` and a
description of what the codebase is for. Leave `last_encoding_point` unset; SKILL.md Step 5
sets it once the encode is validated.

**Existing knowledge.** When the user chose a full re-encode over a project that already holds
knowledge, review that knowledge as well as the code. Page through `get_recent_memories` with
`project_ids` set to this project, `sort_by` `created_at`, `sort_order` `asc`, and `limit` 100,
raising `offset` by 100 until all `total_count` memories are collected. Each one is nominated:
it gets a verdict against the code at the end commit, including memories whose files no longer
exist. Also list all project documents, code artifacts, and entities with their list operations,
and get every listed entity's relationships. Keep each relationship once in the inventory.
Include objects with no memory links; otherwise retired components and unattached documents
can escape review. Changes to existing knowledge go on the SKILL.md confirmation list.

Done when: a project ID exists, and on a re-encode, every existing project memory, document,
code artifact, entity, and relationship is listed for review.

## F2 — Survey the sources

Read what the repo says about itself before reading code: README, `docs/`, contributor and agent
guides, manifests (dependencies, entry points, scripts), CI and deploy configuration. Note
repo-level problems for the report's weak spots: missing docs, absent CI, and the like.

Done when: there is a source list of what will be encoded, ordered by signal.

## F3 — Model the system as entities

Per `forgetful-entities`: the system itself and its key components (services, packages,
databases, external dependencies that matter) as `entity_type: "System"`, linked to the
project, and their structure as relationships: `part_of` for composition, `depends_on` for
coupling. Search for existing entities before creating.

On a full re-encode, review every entity and relationship in the F1 inventory, including
components absent from the current source. Compare both existing edges and relationships the
source supports but the graph lacks. Apply the shared entity rules: keep valid entities and
edges, record retired components, and add, update, or remove relationships as supported.

Done when: the architecture is walkable as a graph, and every inventoried entity and
relationship has a verdict with its required writes completed or recorded as gaps.

## F4 — Store the knowledge

Two layers, per `forgetful-remember` (its routing, atomicity test, and importance rubric govern
every write here):

- **Documents** for long-form understanding: architecture overviews, subsystem guides, design
  analyses.
- **Atomic memories** as the entry points: decisions, conventions, patterns, constraints. Link
  each to its document via `document_ids`, and to the entities it concerns with a separate
  `link_entity_to_memory` call; `create_memory` does not make that link.

Code worth reusing verbatim becomes a code artifact. Query before create, so overlap with
existing knowledge becomes an update rather than a duplicate. On a full re-encode, read every
memory, document, and artifact in the F1 inventory, even if nothing in the current source points
to it. Apply its verdict, preserving accurate knowledge and identifying retired material.

Done when: each surveyed source area has produced its documents and entry-point memories, or is
recorded as having nothing worth encoding, and every inventoried item has a verdict with its
required writes completed or recorded as gaps.
