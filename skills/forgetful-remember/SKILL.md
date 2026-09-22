---
name: forgetful-remember
description: >-
  Remember knowledge worth keeping — a decision made, a solution found, a preference stated,
  a pattern confirmed. Use when work surfaces something future sessions will need, or the
  user asks to remember something. Routes content to the right store (memory, document, code
  artifact, entity, procedure, file) and enforces query-before-create.
license: MIT
tags: [memory, capture, curation, knowledge-management]
allowed-tools:
  - mcp__forgetful__discover_forgetful_tools
  - mcp__forgetful__how_to_use_forgetful_tool
  - mcp__forgetful__execute_forgetful_tool
  - Bash(forgetful:*)
---

# Remembering knowledge in Forgetful

Capture is a sequence, not a single call: route the content to the right store, ground it in
a project, check what already exists, then create atomically and link. Removal and rewriting
happen by supersession only — a memory does not become less true because it hasn't been
queried lately.

## Invoking operations

Operations are named by registry name (`query_memory`, `create_memory`, ...). Invoke via
whichever surface this agent has:

- **MCP**: `execute_forgetful_tool(tool_name="create_memory", arguments={...})`
- **CLI**: `forgetful call create_memory --args '{"title": "..."}' --json`

Get any operation's schema at runtime: `how_to_use_forgetful_tool` (MCP) or
`forgetful tools info <operation>` (CLI) — schemas are deliberately not repeated here.

## Step 1 — Route the type

| The content is... | Store as | Where |
|---|---|---|
| A single fact, decision, or preference | Memory | this skill, step 4 |
| Detailed analysis or a guide (>300 words) | Document + entry memories | this skill, step 4 |
| Reusable code | Code artifact | this skill, step 4 |
| A person, org, device, product, component | Entity | `forgetful-entities` |
| Step-by-step procedural knowledge | Skill | `forgetful-procedures` |
| Binary content (image, PDF, asset) | File | `forgetful-files` |
| A goal decomposing into steps / a work item | Plan / Task | feature-flagged; check discovery |

Done when: exactly one type is chosen, and routed-away types are handled by their skill.

## Step 2 — Resolve the project

Every write needs a deliberate project decision. Derive the candidate from the repo:
`git remote get-url origin` → `owner/repo` → `list_projects` with `repo_name`. When no
project matches, create one or ask the user; when several could apply, ask.

Done when: a real `project_id` is confirmed — discovered or user-chosen, never assumed.

## Step 3 — Query before create

Search for overlapping knowledge using the candidate's own essence as the query
(`query_memory` with `query` and `query_context`). Classify every relevant hit:

| Existing memory is... | Action |
|---|---|
| Still accurate and covers the point | Link to it if related; skip creating a duplicate |
| Right but missing the new detail | Update it — confirm with the user first |
| Contradicted by the new knowledge | Mark obsolete (confirm first) + create replacement |
| Overlapping but a distinct concept | Create new, then `link_memories` both |

Create and link freely; `update_memory` and `mark_memory_obsolete` rewrite history, so those
two always get user confirmation before executing.

Done when: every hit is classified and the create/update/skip decision is explicit.

## Step 4 — Create atomically

The atomicity test, before writing: Can the title say it in ~10 words? Is it self-contained
without reading other memories? Is it ONE decision, fact, or pattern? A sprawling "Project X
overview" fails the test — split it.

- Ideal content is 200–400 words. Limits: title ≤200 chars, content ≤2000, context ≤500,
  keywords ≤10, tags ≤10.
- Set `importance` from the rubric below. About 70% of memories belong at 7–8; reserve 9–10.

| Band | Use for |
|---|---|
| 9–10 | Foundational: personal facts, architectural principles in constant use |
| 8–9 | Critical solutions, major decisions |
| 7–8 | Useful patterns, strong preferences, tool choices, standard implementations |
| 6–7 | Milestones, minor context |
| 5 | Noise floor: bulk/automated captures meant to stay out of normal recall |

- Stamp provenance when derived from source material: `source_repo`, `source_files`,
  `source_url`.

Long-form variant: content over ~300 words becomes `create_document`, then 3–7 atomic
memories as entry points, each linked to the document via `document_ids`. Reusable code
becomes `create_code_artifact`, with a memory pointing at it when the *decision* behind the
code matters too.

Done when: the object exists, atomic, scored, and provenance-stamped where applicable.

## Step 5 — Link

Auto-linking connects each new memory to its nearest neighbours (similarity ≥ 0.7 by default).
Review what it picked up, then add `link_memories` manually only for the four kinds embeddings
miss: cross-domain connections, prerequisite chains, contrast (this-not-that), and evolution
(old approach → new approach).

Done when: auto-links reviewed and any of the four manual kinds added.

## Step 6 — Announce

This skill is the single source of truth for the announcement convention. After saving with
importance ≥ 7:

```
💾 Saved to memory: "<title>"
   Tags: <tags>
   Related: <linked memory titles>
```

Done when: the user can see what was saved and how it connected.
