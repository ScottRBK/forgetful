---
name: forgetful-encode-repo
description: >-
  Encode a repository into the Forgetful knowledge base, or refresh an existing encoding after
  development work. A first encode builds the project, entities, memories, and documents from
  the codebase. A refresh reviews the git changes since the project's last encoded commit and
  updates, obsoletes, or adds only the knowledge those changes affect. Use when bringing a repo
  under Forgetful, or syncing its knowledge after commits, merges, or a release.
license: MIT
disable-model-invocation: true
tags: [bootstrap, encoding, refresh, repository, knowledge-base, git]
allowed-tools:
  - mcp__forgetful__discover_forgetful_tools
  - mcp__forgetful__how_to_use_forgetful_tool
  - mcp__forgetful__execute_forgetful_tool
  - Bash(forgetful:*)
---

# Encoding a repository

An encoding is a claim about the code at one commit. The project's `last_encoding_point` holds
that commit's SHA: the checkpoint. Forgetful stores the checkpoint but never sets or advances it;
this skill moves it, and only after a run has reviewed every change up to the new commit. A first
encode builds knowledge from the codebase. A refresh reviews the changes since the checkpoint.

**Decide, then load.** Begin with Step 1. The branch comes from what Steps 1 and 2 observe in
git and Forgetful, not from whether the request says encode or refresh, and Step 2 ends by
writing it down as the branch decision. Open a reference only after that decision, and only the
one it names.

## Invoking operations

Operations are named by registry name (`list_projects`, `update_memory`, ...). Invoke via
whichever surface this agent has:

- **MCP**: `execute_forgetful_tool(tool_name="list_projects", arguments={...})`
- **CLI**: `forgetful call list_projects --args '{"repo_name": "..."}' --json`

Get any operation's schema at runtime: `how_to_use_forgetful_tool` (MCP) or
`forgetful tools info <operation>` (CLI) — schemas are deliberately not repeated here.

Skills named below resolve via `search_skills` → `export_skill` when not already available.

## Step 1 — Pin the run

Run git in the repository being encoded (the current directory unless the user named one).
Record, before any write:

- **HEAD**: `git rev-parse HEAD`. Unless the user names another range end, this is the end
  commit: everything this run writes describes it.
- **Clean worktree**: `git status --porcelain` prints nothing. Otherwise knowledge read from
  uncommitted or untracked files would be stamped with a commit that lacks them, so ask the user
  to commit or stash, and wait.
- **Project**: `git remote get-url origin` → `owner/repo` → `list_projects` with `repo_name`.
  When no remote exists or several projects match, ask the user. Record the project ID and
  its `last_encoding_point` as read now.

Done when: HEAD, a clean worktree, and the project (or its absence) are recorded.

## Step 2 — Choose the branch

Two requests override the table. A full re-encode selects the first-encode branch, including
its review of existing knowledge. An explicit range for an existing encoding selects refresh,
even when its end equals the checkpoint; resolve the range as described below. For a repo with
no encoding, use the first-encode branch at the requested end commit instead.

Otherwise, the first matching row wins:

| Situation | Branch |
|---|---|
| No project for this repo | First encode |
| Project has no encoded knowledge (check below) | First encode |
| Checkpoint equals the end commit | Nothing to review: go to Step 6 |
| Checkpoint is a commit and an ancestor of the end commit | Refresh, checkpoint → end |
| Project holds knowledge; checkpoint missing, unknown here, or not an ancestor | Pause |

Checks: the checkpoint is a commit here when `git rev-parse --verify --quiet <sha>^{commit}`
prints the stored value itself; a branch or tag name moves, so it does not count.
`git merge-base --is-ancestor <sha> <end>` succeeds when it is an ancestor. Check for
knowledge with `get_recent_memories` (project ID, `include_obsolete`), `list_documents`,
`list_code_artifacts`, and `list_entities`, each scoped to the project. Any item returned proves
knowledge; a project record alone does not. Knowledge is absent only when all four reads succeed
and return nothing. A read that still fails after correcting the call leaves knowledge unknown,
which counts as present.

**Pause** means: ask the user for a baseline, a commit the stored knowledge is known to
describe, and refresh from it once it resolves as an ancestor of the end commit. Take the
baseline from the user; tags, dates, and recent commits are guesses. The user may instead ask
for a full re-encode, which runs the first-encode branch over the existing knowledge.

**User ranges.** A user may name a range `A..B`. Resolve both ends to SHAs; B becomes the end
commit. The checkpoint may move to B only when the range leaves no unreviewed commit after the
current checkpoint: A is the checkpoint or one of its ancestors, and the checkpoint is an
ancestor of B. A user-named baseline counts as the checkpoint for this rule. Any other range
still gets reviewed and curated, but the checkpoint stays where it is.

**Branch decision.** End this step by writing the decision in your response: the project ID or
none, the checkpoint as read, the end commit, whether knowledge is present and which reads show
it, and the branch with its range. The decision names the reference Step 3 opens:
`references/first-encode.md` for a first encode, `references/refresh.md` for a refresh, and
none for a pause or nothing to review.

Done when: the branch decision is written, and each value in it comes from a command or tool
result in this run.

## Step 3 — Load and run the branch

Open the reference the branch decision names, from where this skill came from so it matches
this SKILL.md, and follow its steps, applying the curation rules below to every write:

- **Skill folder**: read that path, relative to this SKILL.md's folder.
- **Forgetful skill store**: references are documents linked to this skill. `get_skill_links`
  with this skill's ID (from the `search_skills` or `list_skills` result that found it) gives
  `document_ids`; `list_documents` shows their titles without content. `get_document` only the
  linked document titled exactly `forgetful-encode-repo/` followed by that path.

When the reference is not there, stop and tell the user which file is missing.

Done when: the named reference is the only one opened, and each of its steps has met its
completion criterion or recorded its unfinished items as gaps.

## Step 4 — Validate

- **Coverage**: every reviewed item has a verdict, and every write the verdicts require has
  succeeded or is recorded as a gap.
- **Retrieval**: when the run wrote knowledge, `query_memory` scoped to the project with
  `strict_project_filter` true and the questions this encoding should answer (how the system
  fits together, each changed area under its current name). Created and updated knowledge
  surfaces; obsoleted knowledge does not.
- **Pinning**: `git rev-parse HEAD` still matches Step 1, `git status --porcelain` still prints
  nothing, and `get_project` still shows the checkpoint read in Step 1.

Done when: each check has passed, or its failure is recorded as a gap.

## Step 5 — Set the checkpoint

Advance the checkpoint only when the run recorded no gaps and the range leaves no unreviewed
commit (see user ranges in Step 2). Then call `update_project` with exactly two arguments:
`project_id`, and `last_encoding_point` set to the end commit's full SHA. Every other project
field, provenance included, keeps its stored value. A successful first encode records its end
commit the same way. A fully reviewed refresh advances even when it needed no writes. With any
gap, leave the checkpoint unchanged: the next refresh then covers the same commits again.

Done when: the checkpoint holds the end commit, or is unchanged with the reason recorded.

## Step 6 — Report

Close with a report in the final response to the user. It is not stored in Forgetful. Build it
from tool results in this run: an ID or count appears only when a response confirmed it, and a
read that failed is reported as unknown.

- **Range**: branch, base and end SHAs, and any user-named range or baseline.
- **Checkpoint**: old → new, or unchanged and why.
- **Changed objects**: IDs and titles of memories created, updated, and obsoleted; documents,
  code artifacts, and entities created or updated; relationships added or removed; the project
  if created.
- **Skips**: how many reviewed items were kept unchanged, areas skipped and why, declined
  changes.
- **Gaps**: every gap, with what it left unfinished.
- **Weak spots**: plugin warnings, areas where knowledge is thin, and repo-level problems such
  as missing docs or absent CI.

Done when: the report is delivered and every recorded gap appears in it.

## Curation rules

These apply to every write in both branches, except the Step 5 checkpoint update, which
follows Step 5 alone.

### Scope

- Write only to this project's knowledge. Knowledge in other projects or in none stays as it
  is, even when it mentions this repo. When a memory also belongs to other projects, keep those
  project links and mention the sharing on the confirmation list.
- On update, list fields (`project_ids`, `document_ids`, `source_files`, `tags`, ...) replace
  the stored list: send the complete intended list, or omit the field to keep it.

### Verdicts

Give every reviewed item exactly one verdict:

| The item is... | Verdict |
|---|---|
| Still accurate | Keep: no write |
| Accurate, but paths, names, or details moved | Update in place, keeping ID and links |
| Partly stale | Update in place: remove what is false, keep what holds |
| Contradicted by the code | Obsolete, with a reason naming the commit or range |
| Replaced by different knowledge | Create the replacement, then obsolete with `superseded_by` |
| Missing and worth keeping | Create, per `forgetful-remember` routing, atomicity, and importance |

- A changed, renamed, or deleted file is a reason to review, not proof a fact is wrong. Decide
  from what the code at the end commit says; deleted code may have moved.
- Update rather than delete and recreate: the ID carries links and history. Documents and code
  artifacts have no obsolete state; correct them in place with their update operations, and
  keep their entry-point memories pointing at them.
- Entities stay; relationships change. When a component is removed, keep its entity, record the
  removal and commit in its `notes`, remove the relationships the code no longer supports, and
  obsolete memories that describe it as current. Leave `delete_entity` out of encoding: it also
  deletes the entity's relationships and memory links.
- Encode a decision's reason only when the repo states it: an ADR, a doc, a comment, or a commit
  message saying why. Otherwise record what the code does without a reason.
- Writes follow from verdicts. There is no quota, and a fully reviewed range may need none.

### Provenance

- Set `source_repo`, and `source_files` as paths at the end commit, on every create and every
  update.
- Cite the reviewed commit (first encode) or range (refresh) where the write has room: an
  obsolete `reason`, an entity's `notes`, a relationship's `metadata`, or a short clause in a
  memory's `context`, a document's text, or a code artifact's `description`.
- `encoding_agent`, `agent_id`, `agent_model`, and their version fields describe the software
  and model actually running this session; leave unknown ones unset. A skill name is not an
  agent identity. On updates, keep stored values that are still true.

### Confirmation, failures, and gaps

A **gap** is unfinished review or an unfinished required write: an unreviewed item, a failed or
rejected write, a declined or unconfirmed change, or a failed Step 4 check. Record each one as
it happens. Gaps keep the checkpoint where it is.

- `forgetful-remember` requires the user's confirmation before rewriting history. Put every
  change to existing knowledge (updates, obsoletions, relationship removals) on one list, each
  with its verdict and a one-line reason, and get confirmation before running any of them. An
  instruction in the user's request to apply encoding changes without asking counts as that
  confirmation. Creates and new links need none.
- A declined change is a gap, unless the user says the item should stay as it is. Without an
  answer, the changes do not run and remain gaps.
- Handle `plugin_warnings`, `WRITE_PLUGIN_REJECTED`, `WRITE_PLUGIN_UNAVAILABLE`, and lost or
  cancelled responses as `forgetful-remember` Step 4 and the Entity Plugin section of
  `forgetful-entities` describe. Plugin warnings on a successful write are weak spots, not gaps.
- Writes that completed stay in place; nothing rolls them back. List them in the report.
- A failed read is not an empty result. Correct the call against the operation's schema and run
  it again; if it still fails, its answer is unknown, and a gap wherever coverage depends on it.
