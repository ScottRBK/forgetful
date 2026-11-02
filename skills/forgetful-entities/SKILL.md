---
name: forgetful-entities
description: >-
  Model the things knowledge attaches to — people, organisations, devices, products, system
  components. Use when a new thing surfaces that memories will reference, when relationships
  between things need recording (owns, depends on, part of), or when another skill routes a
  pointable thing here. Litmus: an entity is a noun you could point at; knowledge about it
  stays a memory.
license: MIT
tags: [entities, knowledge-graph, relationships, modelling]
allowed-tools:
  - mcp__forgetful__discover_forgetful_tools
  - mcp__forgetful__how_to_use_forgetful_tool
  - mcp__forgetful__execute_forgetful_tool
  - Bash(forgetful:*)
---

# Modelling entities in Forgetful

Entities are the graph's nouns. Model the thing once, then let knowledge accrue to it
through links — that is what makes `get_entity_memories` a useful reverse lookup later.

## Invoking operations

Operations are named by registry name (`create_entity`, `link_entity_to_memory`, ...).
Invoke via whichever surface this agent has:

- **MCP**: `execute_forgetful_tool(tool_name="create_entity", arguments={...})`
- **CLI**: `forgetful call create_entity --args '{"name": "..."}' --json`

Get any operation's schema at runtime: `how_to_use_forgetful_tool` (MCP) or
`forgetful tools info <operation>` (CLI) — schemas are deliberately not repeated here.

## Step 1 — Apply the litmus, then dedupe

Can you point at it? "Sarah Chen" is an entity; "Sarah is great at debugging async issues"
is a memory linked to her. The fact stays a memory (`forgetful-remember`); the thing it is
about becomes the entity.

Before creating, `search_entities` for the thing under its likely names — it matches both
`name` and `aka`. Set `aka` at creation time for any alternative names the thing goes by, so
a later dedupe search under a different name still finds it.

Done when: the thing either already exists (use it) or is confirmed new.

## Step 2 — Create with a type

`create_entity` with a name and type: Organization, Individual, Team, Device, System, or
Other (`custom_type` required when Other). Stored Title-case; matched case-insensitively on
input. Check `list_entities` for the types already in use and match them — a graph where
servers are sometimes typed "Device" and sometimes "System" fragments reverse lookups.

Done when: the entity exists once, typed consistently with the existing graph.

## Step 3 — Link knowledge and projects as they accrue

- `link_entity_to_memory` whenever a memory is *about* the entity — done at capture time,
  this is one line; done later, it is an archaeology project.
- `link_entity_to_project` when the entity belongs to a project's world.

Done when: knowledge about the thing is reachable from the thing (`get_entity_memories`).

## Step 4 — Record relationships between entities

`create_entity_relationship` with a direction and a type. Keep the vocabulary small and
consistent — `owns`, `depends_on`, `part_of`, `uses`, `created_by` cover most structure.
Check `get_entity_relationships` on either entity first and reuse the types already in the
graph before coining new ones. Direction carries meaning: A `depends_on` B is a statement
about A.

Done when: the relationships that answer real questions (impact, structure, responsibility)
are recorded, and none duplicate an existing edge.

## Entity Plugin (administrator)

When `ENTITY_WRITE_PLUGIN` is configured, create/update/delete may return `plugin_warnings` or
fail with `WRITE_PLUGIN_REJECTED` / `WRITE_PLUGIN_UNAVAILABLE` before persistence. After-save
warnings are advisory; the mutation already succeeded.
