---
name: forgetful-procedures
description: >-
  Store and find procedural knowledge — reusable step-by-step how-tos — in Forgetful's skill
  store. Use when a workflow worth repeating gets worked out, when the user asks how
  something is done here, or when importing or exporting SKILL.md files. Litmus: a procedure
  someone follows is a skill; a fact someone recalls is a memory.
license: MIT
tags: [skills, procedures, how-to, skill-store]
allowed-tools:
  - mcp__forgetful__discover_forgetful_tools
  - mcp__forgetful__how_to_use_forgetful_tool
  - mcp__forgetful__execute_forgetful_tool
  - Bash(forgetful:*)
---

# Storing and finding procedures

Forgetful's skill store is procedural memory: how-tos that agents retrieve by capability
and follow. All skill operations run through the standard invocation surface below, the
same as every other domain.

## Invoking operations

Operations are named by registry name (`search_skills`, `create_skill`, ...). Invoke via
whichever surface this agent has:

- **MCP**: `execute_forgetful_tool(tool_name="search_skills", arguments={...})`
- **CLI**: `forgetful call search_skills --args '{"query": "..."}' --json`

Get any operation's schema at runtime: `how_to_use_forgetful_tool` (MCP) or
`forgetful tools info <operation>` (CLI) — schemas are deliberately not repeated here.

## Step 1 — Apply the litmus

"How to review pull requests in this project" is a skill; "we use conventional commits" is
a memory (`forgetful-remember`). A procedure has steps someone follows in order; a fact is
recalled and applied.

Done when: the content is confirmed procedural.

## Step 2 — Search before create

`search_skills` for the capability first — search is semantic over skill *descriptions*, so
query by what the procedure achieves ("deploy the API", "rotate credentials"), not its
exact name. An existing skill that covers it gets updated (`update_skill`) rather than
duplicated; names are unique.

Done when: create vs update is an informed decision.

## Step 3 — Create with the description carrying the weight

The description is the only embedded field — content (up to 100KB) is stored but never
searched semantically. Write the description as the retrieval surface: what the procedure
achieves, when to reach for it, capability keywords. Then `create_skill` with kebab-case
name, the full markdown procedure as content, tags, and importance.

Done when: the skill exists and a capability-phrased `search_skills` finds it.

## Step 4 — Import / export SKILL.md

`import_skill` ingests a SKILL.md string: YAML frontmatter needs `name` and `description`;
`license`, `compatibility`, `tags`, `metadata`, and `allowed-tools` (hyphenated on disk,
mapped to `allowed_tools` internally) are honoured. The body after the frontmatter becomes
the content. YAML references (`*name` referring to an `&name` anchor) are rejected in
frontmatter; write the values directly instead. Quoted `"*person"` and body asterisks are valid.
`export_skill` re-emits the SKILL.md, round-trip faithful — tags included.

Done when: imported skills search well (check the description survived intact) and exports
open cleanly in the target platform.

## Step 5 — Link the supporting material

Procedures rarely stand alone: `link_skill_to_memory` for the decisions behind the
procedure, `link_skill_to_document` for long-form background, `link_skill_to_code_artifact`
for the code it operates, `link_skill_to_file` for bundled assets. `get_skill_links` shows
everything attached — it is the reverse lookup, returning linked memory, file, code
artifact, and document IDs.

Done when: following the procedure never requires hunting for its supporting material.
