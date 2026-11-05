---
name: forgetful-update-encoding
description: >-
  Bring the Forgetful knowledge base back in sync with a repository after development work —
  a differential pass over one git range that updates what drifted, obsoletes what the code
  now contradicts, and encodes only what is genuinely new. Use after a release, a merged
  branch, or any run of commits on a repo that forgetful-encode-repo already bootstrapped.
  Never re-encodes the whole repository.
license: MIT
disable-model-invocation: true
tags: [encoding, delta, repository, knowledge-base, git]
allowed-tools:
  - mcp__forgetful__discover_forgetful_tools
  - mcp__forgetful__how_to_use_forgetful_tool
  - mcp__forgetful__execute_forgetful_tool
  - Bash(forgetful:*)
---

# Updating an encoding

An encode is a claim about the code at one commit. Code moves. This skill closes the gap
without starting over: read the diff, touch only the memories the diff contradicts, and let
supersession rather than duplication do the work. Every write cites the range it came from, so
a future reader can tell a refresh from a first encode.

Requires a prior `forgetful-encode-repo` run. Phases below mirror that skill's phases, so a
refresh writes into the same structure rather than alongside it.

## Invoking operations

Operations are named by registry name (`query_memory`, `update_memory`, ...). Invoke via
whichever surface this agent has:

- **MCP**: `execute_forgetful_tool(tool_name="query_memory", arguments={...})`
- **CLI**: `forgetful call query_memory --args '{"query": "..."}' --json`

Get any operation's schema at runtime: `how_to_use_forgetful_tool` (MCP) or
`forgetful tools info <operation>` (CLI) — schemas are deliberately not repeated here.

Skills referenced by name below resolve via `search_skills` → `export_skill` when not already
available. Routing, atomicity and importance come from `forgetful-remember`; retrieval
discipline from `forgetful-recall`; graph walking from `forgetful-explore`; entity modelling
from `forgetful-entities`.

## Arguments

A range `<refA>..<refB>` is optional; refs may be branches, tags, SHAs, `HEAD`, `HEAD~N`. An
optional second argument names a different repo path. A versioned project defaults to its
latest semver tag → `HEAD`; an unversioned one to roughly the last ten commits.

## Phase 0 — Diff analysis

No git repo means this skill does not apply — that is first-encode territory. Resolve both ends
to SHAs and say which range you are actually analysing; if the start is not an ancestor of the
end, say so rather than assuming a linear history, because a merge-heavy range changes what
"changed" means.

Resolve the project from the origin remote → `owner/repo` → `list_projects` filtered by
`repo_name`. **Abort if no project exists**: every later operation needs `project_ids`, and a
partial encode is worse than none.

Then build the two artefacts every later phase consumes. A **classified file list**, where the
git status drives the treatment — added code is assessed for new patterns, features, entities
and artifacts; modified code means finding the memories that reference it; deleted code means
obsoleting them; a rename means rewriting file references, not the knowledge; a copy is
added-plus-linked-to-source; a type change is delete-then-add. And an **affected memory map**,
one `query_memory` per changed path with `query_context` naming the delta-encoding intent,
deduplicated into `memory_id → [changed paths]`. Build it once here and reuse it everywhere —
re-querying per phase wastes calls and drifts.

Read the full diff as well. The file list says where to look; the diff says what changed.

Classify paths into knowledge domains before going further: manifests and lockfiles to tech
stack; env, container and test config to setup and testing; README and contributor docs to
overview; layer directories to architecture; shared helpers, base classes and decorators to
patterns; `docs/`, ADR directories and rationale comments to decisions.

Detect versioning and adapt. Semver tags give meaningful ranges plus release notes worth
encoding as documented decisions or features. No tags means the diff is the only source of
truth. Sparse tags mean using them where they exist and reporting the gaps rather than
pretending coverage. Over 100 files changed is a note, not a stop.

Done when: a report exists covering range and SHAs, versioning mode, file counts by git status,
project ID, unique affected memory count, and which domains moved.

## The curation workflow

Every affected memory gets exactly one of these verdicts. Nothing else.

| Situation | Action |
|---|---|
| Still accurate after the change | Leave it alone |
| Accurate, but the change adds detail | `update_memory` with the delta folded in |
| Partially stale | Update to prune dead references, keep what holds |
| Contradicted by deleted code | `mark_memory_obsolete`, `reason` naming the range |
| Superseded by a better answer | Obsolete it *and* name the replacement via `superseded_by` |
| Genuinely new knowledge | Create it |

Update, never delete-and-recreate — deletion destroys provenance and link history. Obsolescence
is soft and reversible (`unobsolete_memory` exists for the case where the code comes back).
Provenance on every write: `source_files` and `source_repo` current, `encoding_agent` set to
`update-encoding`.

Two brakes matter more than they sound like they do. **Be conservative** — a file changing is
not a claim that knowledge about it changed. **If in doubt, skip** — a missed update is
recoverable on the next pass; a corrupted memory is not.

## Phase 1 — Foundation

Tech stack, development setup, testing strategy, project overview, architecture pattern. Read
each current memory in full before editing and fold the delta in rather than rewriting — these
carry reviewed prose a diff cannot reconstruct. Dependency and provider changes land here, as do
new test frameworks and changed run commands.

Done when: each affected foundation memory has been read and verdicted, with 3+ updated or
created. Fewer affected files than that is a legitimate gap to report, not a reason to invent
writes.

## Phase 2 — Architecture

One memory per affected layer. Layer memories drift three ways: files moved out from under them,
new modules the layer never mentions, or a boundary that changed meaning. Check the diff against
the layer's own file references and update the ones it now misstates. If a change crosses
layers, say so in both.

Done when: every affected layer has been read and verdicted, cross-layer effects noted.

## Phase 3 — Entities

New components, services and external integrations become entities; relationships follow
(`part_of` for composition, `depends_on` for coupling), linked to the memories that discuss them
via `link_entity_to_memory`. Dedupe against existing entities first.

Disappeared components are the interesting case: record the removal with a reason citing the
range rather than deleting the entity, which would silently sever its memory links. Preserve the
existing entity count unless every removal is justified.

Done when: new entities modelled and related, removals accounted for with a reason, no entity
deleted without one.

## Phase 4 — Patterns

Added code is where new patterns surface: fresh helpers, base classes, decorators, factories,
error and concurrency conventions. Check for an existing pattern memory before creating one —
the usual right answer is adding the new instance to an existing memory rather than storing a
near-duplicate.

Done when: each detected pattern category has been checked against existing memories.

## Phases 5–8 — Conditional

Run on evidence; skip out loud with the reason when there is none.

- **Features** — new or materially changed capability, endpoint, background task or integration.
- **Decisions** — only what is *explicitly documented* (ADR, rationale section, a comment
  stating why). Inferred reasoning is not a decision record; same discipline as
  `forgetful-encode-repo` on the bootstrap side. Also check whether a change supersedes a
  recorded decision, and obsolete it with the range cited if so.
- **Artifacts** — snippets worth reusing verbatim: config loaders, connection helpers,
  middlewares, serializers. Update an existing artifact rather than storing a variant.
- **Documents** — long-form content over ~400 words in `docs/` or README material. Update the
  document rather than adding a competing one, and keep the entry-point memories pointed at it.

Done when: each of these ran or was explicitly skipped with a stated reason.

## Phase 9 — Validate and report

A refresh can make knowledge undiscoverable — an obsolete memory still ranking, an updated one
whose keywords no longer match how anyone would ask. Re-run the questions the encoding is
supposed to answer (architecture, how to add an endpoint, what services exist) and check the
updated memories surface.

Then report honestly in the final response — it is not written into Forgetful: range and
versioning mode, file counts by git status, memories updated / obsoleted / created and artifacts
and entities touched, per-phase status including skips with reasons, and where knowledge is now
thin. Thinness is the useful half of this report; a reader should be able to spot a gap from it
alone.

Done when: validation queries have run and the report names both what changed and what is still
weak.

## When things go wrong

**No changes in range** — report it and stop; do not manufacture an update. **Ref will not
resolve** — list recent commits and tags so the range can be corrected. **No project for this
repo** — bootstrap first with `forgetful-encode-repo`. **Changed files but no memory references
them** — the encoding predates this code; run the addition phases only and flag the coverage
hole. **Large diff** — proceed, and note that per-memory confidence is lower for the same effort.
