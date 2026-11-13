---
name: forgetful-explore
description: >-
  Explore the Forgetful knowledge graph when flat search isn't enough — cross-project
  investigations, "what do we know about X", entity-centred questions, tracing how decisions
  connect. Use when recall returns fragments that reference entities or trail across
  domains. Walks memories, entities, and relationships into one synthesized picture.
license: MIT
tags: [knowledge-graph, traversal, entities, investigation]
allowed-tools:
  - mcp__forgetful__discover_forgetful_tools
  - mcp__forgetful__how_to_use_forgetful_tool
  - mcp__forgetful__execute_forgetful_tool
  - Bash(forgetful:*)
---

# Exploring the knowledge graph

A flat query answers "what matches"; exploration answers "how it connects". The output is a
synthesized picture that states the path taken — never a raw dump of hops.

## Invoking operations

Operations are named by registry name (`search_entities`, `get_entity_memories`, ...).
Invoke via whichever surface this agent has:

- **MCP**: `execute_forgetful_tool(tool_name="search_entities", arguments={...})`
- **CLI**: `forgetful call search_entities --args '{"query": "..."}' --json`

Get any operation's schema at runtime: `how_to_use_forgetful_tool` (MCP) or
`forgetful tools info <operation>` (CLI) — schemas are deliberately not repeated here.

## Choose a depth first

- **Shallow** (phases 1–2): confirm or refresh something specific.
- **Medium** (phases 1–4): understand a topic and its immediate neighbourhood.
- **Deep** (all phases): cross-project investigation or "everything we know about X".

Track visited memory and entity IDs throughout — a revisited ID means that branch is done.

## Phase 1 — Semantic entry

Broad `query_memory` on the topic (with `query_context` stating the investigation's intent).
The goal is entry points, so favour breadth over precision here — raise `k` above its
default of 3 (max 20) rather than settle for a narrow first pass.

Done when: a handful of strong entry memories are identified.

## Phase 2 — Expand the strongest hits

`get_memory` on each entry point for full content and linked memory IDs; follow the links
that bear on the question.

Done when: each entry point's local cluster is understood.

## Phase 3 — Discover the entities

Collect entities referenced by the expanded memories, and `search_entities` for the topic's
obvious actors (systems, people, components) that memories may not name directly.

Done when: the cast of relevant entities is listed.

## Phase 4 — Walk the relationships

`get_entity_relationships` on each relevant entity; follow the relationship types that
answer the question (depends_on for impact, part_of for structure, owns for responsibility).

Done when: the connections between entities are mapped, cycles skipped via the visited set.

## Phase 5 — Harvest entity-linked memories

`get_entity_memories` on the entities that emerged as central — this surfaces knowledge
attached to the *thing* that topic-based queries miss. It returns linked memory IDs paired
with titles, not full content: scan the titles for relevance, then `get_memory` per chosen
ID for the text itself.

Done when: central entities have had their attached knowledge collected.

## Synthesize

Report the picture, not the walk: what is known, how it connects, where knowledge is thin.
Cite memory and entity IDs so the user can jump in, and state the traversal path in one
line (e.g. "query → 3 memories → AuthService entity → 2 dependent components → 5 linked
memories").

Done when: the user gets a connected answer with cited IDs and visible gaps.


When manually linking or unlinking, inspect a configured Memory Link Plugin's transient
`link_outcomes` and nonempty `plugin_warnings`. A rejected manual batch changes no links;
missing/foreign targets remain indistinguishable skips. `removed` and `noop` unlink outcomes
are authoritative, while memory reads do not retain these response-only fields.
