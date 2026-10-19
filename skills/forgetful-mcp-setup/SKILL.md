---
name: forgetful-mcp-setup
description: >-
  Set up an MCP client for Forgetful — wire Claude Code, Cursor, Copilot, Codex, Gemini, or
  OpenCode to the server and verify the connection behaves. Covers stdio vs HTTP transport,
  auth and scopes, the three meta-tools every client sees, and delegation to subagents.
license: MIT
disable-model-invocation: true
tags: [mcp, setup, clients, transport, auth]
allowed-tools:
  - mcp__forgetful__discover_forgetful_tools
  - mcp__forgetful__how_to_use_forgetful_tool
  - mcp__forgetful__execute_forgetful_tool
---

# Setting up an MCP client

Every MCP client sees the same three tools fronting the full registry:
`discover_forgetful_tools` (what exists, by category), `how_to_use_forgetful_tool` (one
tool's docs and schema), `execute_forgetful_tool` (invoke by name with a JSON arguments
object). Roughly 500 tokens of surface, with everything else disclosed at runtime.

## Pick a transport

- **stdio** — the client spawns the server per session: command `uvx forgetful-ai`
  (equivalently `forgetful serve --transport stdio`). Right for a personal, local setup.
- **HTTP** — the client connects to a running server at `<server>/mcp`, e.g.
  `http://localhost:8020/mcp`. Right for a shared or deployed instance.

Claude Code, as the worked example:

```bash
claude mcp add forgetful -- uvx forgetful-ai                          # stdio
claude mcp add --transport http forgetful http://localhost:8020/mcp  # HTTP
```

Other clients follow the same two shapes (spawn command, or HTTP endpoint) in their own
config format — full per-client walkthroughs live in `docs/connectivity_guide.md` in the
Forgetful repo.

## Optional feature discovery over HTTP

`GET <application-base>/.well-known` publicly reports enabled planning, skills, files, and activity
streaming without creating a user. Keep any deployment prefix: for a server at
`https://host/forgetful/mcp`, use `https://host/forgetful/.well-known`. These settings are not a
health or permission check. Treat missing keys or unsupported schema versions as unknown, not
disabled. See `docs/api_reference.md` for the capability document. MCP tool discovery is unchanged.

## Auth and scopes

A local server defaults to no-auth single-user mode. Deployed servers use bearer tokens or OAuth.
`FASTMCP_SERVER_AUTH_*_REQUIRED_SCOPES` controls IdP admission requirements.
`FORGETFUL_SCOPES` sets the server's MCP/local CLI tool limit.
Recognised scopes in verified token `scope`/`scp` claims
can narrow MCP access further; they also apply to the remote CLI's MCP calls.

For JWT/introspection tokens, `api:read api:write read` can satisfy IdP requirements while allowing
only read tools. `openid read` also stays read-only. Accepted Forgetful labels are `*`, `read`,
`write`, `read:<category>` and `write:<category>`. A nonempty claim with no recognised label denies
all MCP tools. Absent/empty claims retain server permissions after successful authentication.

After upgrading, api-only token users must add appropriate tool scopes at the issuer and obtain new
tokens or update introspection responses. Changing `REQUIRED_SCOPES` alone does not change a token.
Built-in GitHub/Google OAuth logins normally expose no scope claim to this resolver and retain the
server permissions; do not request arbitrary Forgetful API scopes from those providers.
See `docs/configuration.md`, "Authentication scopes and Forgetful tool permissions", for examples
and upgrade steps. Do not assume MCP scope restrictions also protect REST endpoints.

## Verify — the completion criterion

Behavioural, not configurational:

1. `discover_forgetful_tools` returns categories, and they match the server's enabled
   feature flags (skills/files/plans appear only when enabled).
2. One `execute_forgetful_tool` round-trip returns real data — `get_current_user` or
   `list_projects` both work as smoke calls.

Done when: both pass in the client that was just wired, in a fresh session.

## Delegation boundary

Run Forgetful MCP calls in the main conversation — subagents do not inherit MCP tool
access. When work must be delegated to a subagent, give it the CLI surface instead
(`Bash` with the `forgetful` command travels into subagents; see `forgetful-cli-setup`).
