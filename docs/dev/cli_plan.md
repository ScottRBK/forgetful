# Forgetful CLI — Implementation Plan

| | |
|---|---|
| **Status** | Implemented — all 5 phases on `feat/cli` (2026-07-07) |
| **Date** | 2026-07-07 |
| **Decision record** | Forgetful memory 1676 |
| **Reasoning artifact** | https://claude.ai/code/artifact/e5b37787-819b-4b20-b37e-0091e3028f1f |

## 1. Summary

Add a first-party CLI to the existing `forgetful-ai` package so the memory system is usable
from any terminal — against a local database by default, or against a remote deployment
(Docker + Postgres) with full OAuth. The CLI is a fourth front door over the existing
transport-agnostic core: it executes the same `ToolRegistry` the MCP meta-tools use, so the
MCP surface, REST API, and terminal can never drift apart.

**Non-goals:** a TUI, shell completion, a client-only package split, replacing the
`hermes-agent-forgetful` plugin, Typer/rich output. All deferred until a real need appears.

## 2. Locked decisions

| Decision | Choice | Why (short) |
|---|---|---|
| Execution path | In-process `ToolRegistry` (Option B) | One source of truth; ~70 tools day one |
| Remote mode | Core requirement, not optional | Scottesh runs Forgetful remotely |
| Auth | `fastmcp.Client(url, auth="oauth")` | Full code flow ships in fastmcp; server has DCR |
| Command surface | Generic passthrough + curated verbs | Passthrough ≈ free; verbs for daily use |
| Framework | `argparse` | Stdlib; matches `main:cli()`; no audit needed |
| Back-compat | Bare invocation still boots stdio server | README MCP configs must not break |
| New dependencies | **None** | argparse is stdlib; fastmcp already pinned |

## 3. Architecture

### 3.1 The seam: `ToolExecutor` protocol

Every tool command is written once against a protocol; local vs remote is a construction-time
choice. This mirrors the existing routes → services → protocols layering.

```python
# app/protocols/executor.py
class ToolExecutor(Protocol):
    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> Any: ...
    async def list_tools(self, category: str | None = None) -> dict[str, Any]: ...
    async def tool_info(self, tool_name: str) -> dict[str, Any]: ...
    async def close(self) -> None: ...
```

- **`LocalExecutor`** — builds the runtime via the bootstrap factory (§3.2), injects the
  `CliContext` shim (§3.3), applies the `FORGETFUL_SCOPES` ceiling, and calls
  `registry.execute(name, arguments)` — the same call `meta_tools.py` makes.
- **`RemoteExecutor`** — wraps `fastmcp.Client`; `execute()` calls the server's
  `execute_forgetful_tool` meta-tool, `list_tools()`/`tool_info()` proxy
  `discover_forgetful_tools`/`how_to_use_forgetful_tool`, so help text always matches the
  server's version (no doc skew).

### 3.2 Bootstrap factory (composition root)

`main.py::lifespan()` (lines ~208–380) currently owns the only copy of the wiring:
adapters → repos → services → registry → scope resolution. Extract it into
`app/bootstrap.py`:

```python
@dataclass
class Runtime:
    db_adapter: Any
    repos: dict[str, Any]
    services: Services          # small dataclass: user, memory, project, ... (None if flagged off)
    registry: ToolRegistry
    permitted_tools: set[str]   # instance-level FORGETFUL_SCOPES ceiling
    event_bus: EventBus | None

async def build_runtime() -> Runtime: ...
async def dispose_runtime(runtime: Runtime) -> None: ...
```

`lifespan()` becomes a thin consumer (build, attach to `mcp`, yield, dispose). `_run_reembed`
switches to the factory. `tests/e2e_sqlite/conftest.py` duplicates this wiring today — it can
migrate to the factory later (optional cleanup, not required by any phase).

Note: `main.py` constructs the module-level `FastMCP` instance at import. That is cheap
(object + route registration; no DB/model work until `lifespan` runs), so CLI commands accept
the import cost. Revisit only if startup profiling says otherwise.

### 3.3 User identity and scopes

- Adapters take a FastMCP `Context` but read exactly two attributes:
  `ctx.fastmcp.user_service` and `ctx.fastmcp.auth` (`app/middleware/auth.py:106`).
  The shim satisfies them:

  ```python
  # app/routes/cli/context.py  (~15 lines)
  class _CliRuntime:
      def __init__(self, runtime: Runtime):
          self.user_service = runtime.services.user
          self.auth = None          # → get_user_from_auth default-user branch

  class CliContext:
      def __init__(self, runtime: Runtime):
          self.fastmcp = _CliRuntime(runtime)
  ```

- **Local mode**: default user (`DEFAULT_USER_ID`) — identical to today's no-auth stdio
  server. The `FORGETFUL_SCOPES` ceiling still applies: `LocalExecutor` reuses
  `parse_scopes`/`resolve_permitted_tools` (`app/routes/mcp/scope_resolver.py:55,104`) and
  performs the same exists/permitted checks `meta_tools.execute_forgetful_tool` does.
- **Remote mode**: identity and scopes are enforced server-side from the token — no client
  logic beyond presenting it.

### 3.4 Module layout

```
app/
  bootstrap.py                # NEW  composition root extracted from main.lifespan
  protocols/executor.py       # NEW  ToolExecutor protocol
  routes/cli/                 # NEW  the fourth front door
    __init__.py
    parser.py                 # argparse tree + legacy-fallback dispatch
    context.py                # CliContext shim + scope-ceiling helper
    local_executor.py
    remote_executor.py
    auth_commands.py          # login / status / logout
    render.py                 # human output formatting + to_jsonable()
main.py                       # entry point: legacy launcher + dispatch into routes/cli
```

### 3.5 Configuration resolution (highest wins)

1. Flags: `--server URL` / `--local` (per invocation).
2. Shell env: `FORGETFUL_SERVER`; `FORGETFUL_TOKEN` (headless/CI bearer — fastmcp accepts a
   plain token string as `auth`).
3. `~/.config/forgetful/.env` — already in `settings.py`'s `env_file` list (`settings.py:229`);
   `auth login` writes `FORGETFUL_SERVER` here. One mechanism for server and CLI; no TOML.
4. Defaults: local mode, SQLite at the platformdirs data path, FastEmbed embeddings.

New settings: `FORGETFUL_SERVER: str = ""` (pydantic-settings picks it up from all layers).
Token cache: `~/.config/forgetful/tokens/` (0600), owned by the fastmcp OAuth helper's file
storage. CLI code must read `settings` attributes at call time (not import time) so tests can
monkeypatch the singleton.

## 4. Command surface

### 4.1 Commands by phase

| Command | Phase | Notes |
|---|---|---|
| `forgetful serve [--transport stdio\|http] [--host] [--port]` | 2 | canonical launcher |
| `forgetful re-embed [--batch-size N] [--dry-run]` | 2 | migrated from `--re-embed` |
| `forgetful tools list [--category CAT]` | 3 | from registry metadata (local) / discover (remote) |
| `forgetful tools info <tool>` | 3 | detailed schema + examples |
| `forgetful call <tool> --args '<JSON>'` | 3 | generic passthrough, covers all ~70 tools |
| `forgetful auth login --server URL` | 4 | browser OAuth; saves `FORGETFUL_SERVER` |
| `forgetful auth status` | 4 | server, user (`get_current_user`), token expiry |
| `forgetful auth logout` | 4 | clears token cache only |
| `forgetful memory search <query> [-p PROJECT] [-n N] [-c CONTEXT]` | 5 | → `query_memory` |
| `forgetful memory save <content> --title T [--importance N] [-p]` | 5 | → `create_memory` |
| `forgetful memory get <id>` | 5 | → `get_memory` |
| `forgetful memory recent [-n N] [-p]` | 5 | → `get_recent_memories` |
| `forgetful project list` | 5 | → `list_projects` |

Global flags on tool commands: `--server URL`, `--local`, `--json`. Top level: `--version`.
`-p/--project` accepts an id or a name (non-numeric values resolved via `list_projects`).
Exact curated flag→argument mappings are settled test-first in phase 5.

### 4.2 Legacy dispatch (back-compat, permanent)

```python
KNOWN = {"serve", "re-embed", "tools", "call", "auth", "memory", "project"}

def cli():
    argv = sys.argv[1:]
    if not argv or argv[0] not in KNOWN:
        # today's parser: bare → stdio; --transport / --re-embed / --version
        return _legacy_launcher(argv)
    _dispatch(argv)
```

Guaranteed unchanged: `forgetful`, `uvx forgetful-ai`, `forgetful --transport http --port N`,
`forgetful --re-embed [--batch-size] [--dry-run]`, `forgetful --version`.

### 4.3 Output and errors

- `--json`: result to stdout as JSON (`to_jsonable()` handles pydantic models via
  `model_dump(mode="json")`). Passthrough human default = indented JSON (results are
  inherently structured). Curated human default = compact formatted lines (`render.py`),
  e.g. `#1  [8]  WSL2 DNS resolution fix  (memory 812)`.
- Errors → stderr; exit codes: `0` success, `1` runtime/tool error (unknown tool includes
  first-10 suggestions, mirroring `meta_tools`), `2` usage (argparse default). `--json` mode
  emits `{"error": "..."}` on stderr for scriptability.

## 5. Phases

Every phase follows red-green-refactor (see `test-driven-development` skill): write the
failing tests listed below first, verify they fail for the right reason, implement minimally,
then run the full suites + ruff. **Done criteria for every phase:** all existing tests green,
new tests green, `uv tool run ruff check .` clean.

### Phase 1 — Bootstrap factory (S)

Pure refactor; zero behaviour change.

Tests first (`tests/integration/test_bootstrap.py`):
1. `build_runtime()` with `SQLITE_MEMORY=true` returns wired services + registry
   (spot-check: registry tool count > 0, `services.memory` usable end-to-end for one create).
2. Feature flags respected: `SKILLS_ENABLED=false` → `services.skill is None` and no skill
   tools registered.
3. `dispose_runtime()` closes the DB adapter (idempotent).

Implementation: create `app/bootstrap.py`; slim `lifespan()` and `_run_reembed` to consume it.
Regression gate: `uv run pytest tests/integration/ tests/e2e_sqlite/` — the e2e_sqlite suite
exercising the full stack is the real safety net for this refactor.

### Phase 2 — Subcommand skeleton + legacy fallback (S)

Tests first (`tests/integration/test_cli_dispatch.py` — invoke `cli()` with patched
`sys.argv`; inject a recording fake for the serve/re-embed runners):
1. `[]` → legacy stdio serve path.
2. `["--transport", "http", "--port", "9000"]` → legacy http serve with those args.
3. `["serve", "--transport", "http"]` → same runner via new spelling.
4. `["--re-embed", "--dry-run"]` and `["re-embed", "--dry-run"]` → re-embed runner.
5. `["--version"]` exits 0 printing version; unknown subcommand-like token → legacy parser's
   error (exit 2), not a crash.

Implementation: `app/routes/cli/parser.py` with the `KNOWN`-set fallback; `main.cli()`
delegates. `serve`/`re-embed` share the phase-1 factory.

### Phase 3 — Executor protocol + local passthrough (M)

Tests first:
- Integration (`tests/integration/test_cli_local_executor.py`):
  1. `LocalExecutor.execute("create_memory", {...})` → result has an id; follow-up
     `get_memory` roundtrips (in-memory SQLite, single runtime).
  2. Unknown tool → error naming available tools; exit path maps to code 1.
  3. `FORGETFUL_SCOPES=forgetful:read` → `execute("create_memory", ...)` denied with the
     required-scope message (reuses `resolve_permitted_tools`).
- E2E (`tests/e2e_sqlite/test_cli_passthrough.py` — drive `cli()` in-process with patched
  argv + capsys; `SQLITE_PATH` pointed at `tmp_path` so state persists across invocations):
  4. `tools list` prints ≥ 8 categories; `tools list --category memory` filters.
  5. `tools info query_memory` includes parameter schema.
  6. `call create_memory --args '{...}'` then `call query_memory --args '{...}'` finds it.
  7. Malformed `--args` JSON → exit 2 with a pointed message; `--json` emits parseable output.

Implementation: protocol, `CliContext`, `LocalExecutor`, `tools`/`call` commands, `render.py`
(`to_jsonable`, human JSON pretty-print), error/exit-code mapping.

Perf note: measure command latency here. If FastEmbed load makes read-only commands slow,
add lazy embedding-adapter init as a follow-up inside phase 3 — measure first, don't assume.

### Phase 4 — Remote executor + auth commands (M)

Tests first:
- Integration (`tests/integration/test_cli_remote_executor.py` — stub client injected via a
  client-factory seam on `RemoteExecutor`):
  1. `execute()` calls `execute_forgetful_tool` with `{tool_name, arguments}` and unwraps the
     result payload.
  2. `list_tools()`/`tool_info()` proxy the discover/how-to-use meta-tools.
  3. Executor selection: `--server` beats `FORGETFUL_SERVER` env beats config file beats
     local default; `--local` forces local; `FORGETFUL_TOKEN` set → bearer auth used.
  4. `auth login` writes/updates only the `FORGETFUL_SERVER` line in the user config `.env`
     (other lines preserved); `auth logout` deletes the token dir.
- E2E (`tests/e2e_sqlite/test_cli_remote.py`): start the real server in-process on an
  ephemeral HTTP port with **no auth** and a `tmp_path` **file** SQLite (in-memory SQLite is
  per-connection — unusable across server/CLI boundaries); run `--server http://…/mcp`
  passthrough commands against it.
- OAuth browser flow itself: not automatable sensibly. Manual verification checklist against
  the real remote instance (login → status → search → logout), documented in the PR.

Implementation: `RemoteExecutor`, `auth_commands.py`, `FORGETFUL_SERVER` setting, executor
resolution, minimal `.env` line editor.

**Verify at phase start (Context7, fastmcp — repo pins 3.2.2, docs checked at 3.2.4):**
exact `CallToolResult` payload access (`result.data` vs structured content), and the OAuth
helper's file token-storage configuration (docs mention `FileTreeStore`; default may be
in-memory). Budget a pin-bump to 3.2.4 if 3.2.2 lacks needed client APIs.

### Phase 5 — Curated verbs (M)

Tests first (`tests/e2e_sqlite/test_cli_verbs.py`, plus integration tests for flag→argument
mapping including project name→id resolution):
1. `memory save … --title …` prints the new id; `memory get <id>` shows it.
2. `memory search <query>` returns the saved memory in human format; `--json` parses.
3. `memory recent -n 3` ordering; `project list` output.
4. `-p <name>` resolves via `list_projects`; unknown name → exit 1 with available names.

Implementation: verb commands mapping flags → executor arguments (defaults, e.g.
`query_context` defaulting to `"cli search"`); human renderers. Every verb works identically
through both executors by construction.

## 6. Testing strategy

- **Integration** (`tests/integration/`): dispatch, executors, flag mapping — stubbed I/O,
  fast, run on every change.
- **SQLite E2E** (`tests/e2e_sqlite/`): full-stack CLI runs, in-process, no Docker. File-based
  `tmp_path` DBs whenever state must survive multiple `cli()` invocations or cross the
  CLI/server boundary (in-memory SQLite is per-connection).
- **Postgres E2E** (`tests/e2e/`, opt-in `-m e2e`): one smoke test — passthrough
  create/query via `LocalExecutor` against Postgres — to prove DB-agnosticism; no exhaustive
  duplication.
- Real dependencies throughout; the only test double is the fastmcp client stub in remote
  integration tests (external boundary). Bug found later ⇒ reproduce with a failing test in
  the matching layer first (dev philosophy rule 2).

## 7. Risks & watch items

| Risk | Mitigation |
|---|---|
| fastmcp 3.2.2 client API gaps | RESOLVED: verified against installed 3.2.2 source — no bump needed. Caveat found: `auth="oauth"` defaults to in-memory token storage, so the CLI passes `OAuth(token_storage=FileTreeStore(~/.config/forgetful/tokens))` explicitly |
| FastEmbed load slows local commands | RESOLVED: measured ~0.25s per warm command (+~1.0s main import) — no lazy init needed |
| CLI + server share one SQLite file | WAL + `busy_timeout` already set (`sqlite_adapter.py:37`) |
| Env drift: MCP-launched server vs CLI | Shared overrides belong in `~/.config/forgetful/.env` |
| Settings read at import time in new code | Read `settings.X` inside functions; tests enforce |
| Legacy flag regressions | Phase-2 dispatch tests enumerate every documented legacy invocation |

## 8. Documentation & release

- README: new "CLI" section (install via `uv tool install forgetful-ai`, local quick start,
  `auth login` for remote) — keep MCP client config examples untouched.
- `docs/connectivity_guide.md`: remote CLI + OAuth section; `docs/configuration.md`:
  `FORGETFUL_SERVER`, `FORGETFUL_TOKEN`, token-cache location.
- `docs/features_roadmap.md`: add CLI items, tick per phase.
- Changelog/release notes on the next PyPI release; announce `forgetful serve` as canonical
  (legacy flags remain supported indefinitely).
