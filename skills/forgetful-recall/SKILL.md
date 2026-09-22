---
name: forgetful-recall
description: >-
  Recall past knowledge before working — prior decisions, solved problems, preferences,
  project history. Use at the start of any task, when the user references earlier work, when
  re-entering a project after time away, or before proposing an approach that may already
  have history. Covers query shaping, scoping, session-start catch-up, and when to escalate
  to graph exploration.
license: MIT
tags: [memory, retrieval, search, context]
allowed-tools:
  - mcp__forgetful__discover_forgetful_tools
  - mcp__forgetful__how_to_use_forgetful_tool
  - mcp__forgetful__execute_forgetful_tool
  - Bash(forgetful:*)
---

# Recalling knowledge from Forgetful

Retrieval quality is decided by how the query is shaped and scoped, and by treating coverage
as something to judge rather than assume. Recall before proposing; history usually exists.

## Invoking operations

Operations are named by registry name (`query_memory`, `get_recent_memories`, ...). Invoke
via whichever surface this agent has:

- **MCP**: `execute_forgetful_tool(tool_name="query_memory", arguments={...})`
- **CLI**: `forgetful call query_memory --args '{"query": "..."}' --json`

Get any operation's schema at runtime: `how_to_use_forgetful_tool` (MCP) or
`forgetful tools info <operation>` (CLI) — schemas are deliberately not repeated here.

## Step 1 — Shape the query

`query_context` is a required parameter alongside `query`; the call errors without it.
The vector search embeds `query` alone. When cross-encoder reranking runs, it also uses
`query_context` to refine the ranking. Include exact identifiers in `query` when they
matter, but search does not guarantee literal matches.

Done when: both `query` and `query_context` are written, not just a bare keyword.

## Step 2 — Scope deliberately

Reads are cross-project by default, and usually should stay that way — knowledge transfers.
Narrow with `project_ids` when the task is project-bound; add `strict_project_filter=True`
to also keep linked memories inside those projects (the default `False` lets links cross
them). Use `importance_threshold` to cut noise — it excludes anything scored below the value
given, pairing naturally with `forgetful-remember`'s rubric, where 5 is the noise floor for
bulk/automated captures. Adjust `k` to trade breadth for focus. These are filters layered on
top of semantic search, which stays the primary retrieval mechanism throughout.

Done when: the scope is a choice, not a default accident.

## Step 3 — Judge coverage

Results are budgeted (about 8000 tokens / 20 memories), so assess coverage rather than
non-emptiness:

- `truncated: true` → narrow the query (raise the threshold, scope the project) instead of
  accepting silent loss.
- A miss on the first angle → re-query from a different facet (the feature area, the
  technology, the error text) before concluding the knowledge doesn't exist.

Done when: results are judged sufficient, or absence is confirmed from more than one angle.

## Step 4 — Expand or escalate

Promising hits get `get_memory` for full content and links. When hits arrive as fragments,
reference entities, or trail across domains, the flat list is the wrong shape — switch to
`forgetful-explore` and walk the graph instead.

Done when: enough context is in hand, or the exploration skill has taken over.

## Step 5 — Report

This skill is the single source of truth for the retrieval reporting convention:

- Found context: "Found N memories about X" with the load-bearing ones named.
- Nothing relevant: say so explicitly — "No existing memories about X."
- Off-target results: flag them — "Retrieved some context but it seems tangential."

A clean miss is also a signal: note the gap as a `forgetful-remember` candidate once the
task resolves it.

Done when: the user knows what memory contributed, even when the answer is "nothing".

## Session-start catch-up

Re-entering a project after time away: `get_recent_memories` scoped to that project's ID is
the catch-up move — recent decisions and milestones without guessing queries. Run it as a
deliberate step, then continue into normal recall as the task demands.
