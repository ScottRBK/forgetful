# Forgetful Skills

Canonical agent-facing skills for using Forgetful. This directory is the single source of
truth — per-client packagings (Claude Code plugin, OpenCode, Copilot CLI) derive from these
files rather than maintaining their own copies.

## Design rules

- **Skills carry judgment, the product carries schemas.** No tool schema is ever embedded in
  a skill. Discovery is part of the product: `discover_forgetful_tools` /
  `how_to_use_forgetful_tool` on MCP, `forgetful tools list` / `forgetful tools info` on the
  CLI — both served fresh from the same registry at runtime.
- **Surface-neutral bodies.** Operations are referenced by registry name (`query_memory`,
  `create_entity`). Each skill opens with the same two-line invocation mapping for MCP and
  CLI. Only the two setup skills are surface-specific.
- **Single-file skills.** Every skill is one SKILL.md with no sibling files, so the set
  round-trips through Forgetful's own `import_skill` / `export_skill` and can be seeded into
  the skill store.
- **Descriptions do double duty.** They are the model-invocation trigger in Claude Code and
  the only embedded text for `search_skills` inside Forgetful — written for both.

## Catalog

| Skill | Invocation | Fires when |
|---|---|---|
| `forgetful-remember` | model | Knowledge worth keeping appears; routes to the right store |
| `forgetful-recall` | model | Context needed: task start, "have we solved this before" |
| `forgetful-explore` | model | Flat search isn't enough; the connected picture matters |
| `forgetful-entities` | model | A thing (person, system, component) needs modelling |
| `forgetful-procedures` | model | A how-to worth storing or finding |
| `forgetful-files` | model | Binary content (screenshot, PDF, asset) worth keeping |
| `forgetful-context-gather` | user | Deep pre-work sweep producing a cited context pack |
| `forgetful-encode-repo` | user | Bootstrap or refresh a repository in the knowledge base |
| `forgetful-update-encoding` | user | Sync an existing encoding to a git range after development work |
| `forgetful-cli-setup` | user | Connect a terminal/headless agent; operate a local server |
| `forgetful-mcp-setup` | user | Wire an MCP client and verify the connection |

Plans and tasks are feature-flagged and roadmap-in-motion; they get skills when the flags
graduate.
