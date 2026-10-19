# Quality gates

Every check below runs from one orchestrator, `scripts/quality` (`python -m scripts.quality`),
so Git hooks, CI and a developer shell execute identical commands. Tool versions are pinned in
`pyproject.toml` (`dev` dependency group, locked in `uv.lock`); semgrep, trivy and Qodana run
isolated because their dependency trees conflict with the application pins.

```bash
uv sync --locked --all-extras --dev          # install the toolchain
uv run python -m scripts.quality install     # enable .githooks/ (sets core.hooksPath)
uv run python -m scripts.quality list        # gates and stage pipelines
uv run python -m scripts.quality gate mypy   # run one gate on the whole project
uv run python -m scripts.quality gate ruff --staged
uv run python -m scripts.quality gate ruff --files app/bootstrap.py main.py
uv run python -m scripts.quality stage pre-commit   # what the pre-commit hook runs
uv run python -m scripts.quality baseline update mypy   # lock in fixed findings (see below)
uv run python -m scripts.quality uninstall   # unset core.hooksPath
```

Run the gates with the project environment active: prefix commands with `uv run`, as above, or
activate `.venv` first. Some tests start the `forgetful` console script (for example
`tests/e2e_sqlite/test_harness_server.py` boots `forgetful serve`), which only exists on `PATH` inside
that environment; with a bare system `python -m scripts.quality` they fail for that reason alone.

Python 3.12 to 3.14 is the supported range (`requires-python = ">=3.12"`). The gates test the two ends
of it, **3.12 and 3.14**: locally the `compat` gate runs the SQLite suites on 3.14, and CI runs the
matrices described below; 3.13 is only exercised by the wheel smoke test. The mypy and pylint targets
are 3.12; the baselines are identical on both interpreters.

## What the tools are for

| Tool | What it finds that a reviewer or the test suite tends to miss |
|---|---|
| `ruff` | Lint and import order; the existing rule set, kept clean |
| `import-linter` | Layer violations: routes -> services -> protocols -> repositories/adapters, as in [architecture.md](../architecture.md) |
| `mypy` | Type errors: wrong argument types, `None` flowing into non-optional values, attributes that do not exist |
| `bandit` | Insecure calls: subprocess without a vetted argv, SQL built from strings, permissive file modes, binding to all interfaces |
| `semgrep` | Repository-specific rules: `print()` on the MCP stdout path, deprecated asyncio calls, SQL assembled from strings, swallowed exceptions, missing HTTP timeouts, `verify=False` |
| `vulture` | Dead code: unused functions, classes, variables and methods |
| `radon` | Functions that are too complex (cyclomatic complexity, rank C or worse) and files that are hard to maintain (maintainability grade below A), tests included |
| `pylint` | Broader correctness and design checks (score floor), including things ruff and mypy do not look at |
| `syrupy` snapshots | Accidental changes of the public surface: CLI flags, settings defaults, database schema, migrations, MCP tool catalogue, HTTP routes |
| `pytest` + `coverage` | Code that no test executes (SQLite and PostgreSQL runs combined, line and branch) |
| `pytest-memray` | Memory regressions in hot paths (bulk create, query with reranking) |
| `trivy` | Known vulnerabilities in locked dependencies, committed secrets, Dockerfile misconfigurations |
| `Qodana` | JetBrains deep analysis: inspections, taint flows, vulnerable libraries, licences |
| `mutmut` | Tests that pass although the code was changed: weak assertions. Opt-in, slow |
| `GitNexus` | Which callers and execution flows a staged change touches (local index only) |

## Strict and baselined gates

Most gates fail on the existing code the first time they run. Making them all strict at once would
turn CI red for every contributor, so the gates split in two groups.

| Group | Gates | Fails when |
|---|---|---|
| **Strict** | ruff, imports, pylint (score floor), snapshots, tests-fast, tests, e2e-postgres, coverage (floor), compat, memray, trivy | anything is wrong; known and accepted trivy findings sit in `.trivyignore` |
| **Baselined** | mypy, bandit, semgrep, vulture, radon-cc, radon-mi | a finding is **new or worse** than the one recorded in `scripts/quality/baselines/<gate>.json` |
| Informational / opt-in | mutation, qodana (see below), gitnexus | mutation: only with `MUTATION=1`, weekly in CI, never fails the workflow |

A baselined gate runs its tool, turns the findings into line-number-free keys and compares them with
the recorded file (`scripts/quality/baseline.py`). The baselines of mypy, bandit, semgrep, vulture and
radon (and the pylint score floor) mean **no new findings**, not "no findings": the accepted debt in the
JSON files is tolerated, anything beyond it fails. It prints how much accepted debt is left, for
example `PASS  mypy  (491 baselined finding(s) remain, none new)`, and when a finding is new:

```
mypy: 1 finding(s) are new or worse than the baseline
  NEW    app/services/x.py  arg-type  Argument 1 to "f" has incompatible type "int"; expected "str"  (x1)
      at app/services/x.py:42
Fix them. 491 baselined finding(s) are tolerated (scripts/quality/baselines/mypy.json).
```

| Gate | Key (no line numbers, so an edit above a finding does not turn it into a new one) | Regression |
|---|---|---|
| mypy | file, error code, message | a key with a higher count, or an unknown key |
| bandit | file, test id (for example `B603`) | same |
| semgrep | file, rule id | same |
| vulture | file, kind, name (`function`, `variable`, ...) | same |
| radon-cc | file, qualified name (`Class.method`) -> rank | a function not in the baseline rated C or worse, or a baselined one whose rank got worse (C -> D) |
| radon-mi | file -> rank | a file not in the baseline below grade A, or a baselined one whose grade got worse (B -> C) |

A file radon cannot read is a tool error and always fails; it is never baselined. Per-file scoped runs
(`gate <name> --staged`, `--files ...`, the pre-commit hook) compare only the baseline entries of those
files with the same rules, so a commit is never judged by debt in files it does not touch.
mypy and vulture always analyse the whole project (a changed signature breaks unchanged callers) and
compare against the whole baseline.

### Burning debt down

1. Fix findings in the code you touch (or in a dedicated clean-up change).
2. Run the gate: `PASS ... (N baselined finding(s) remain, none new; K fixed since the baseline ...)`.
3. Run `uv run python -m scripts.quality baseline update <gate>` (or `all`) and commit the changed
   JSON with the fix. The diff shows exactly which entries disappeared, and the `total` line at the
   top of the file shrinks.

Fixing a finding without updating the baseline is allowed (the gate stays green), but the old
allowance then remains and the same finding could creep back unnoticed until somebody ratchets.

### Updating a baseline

`baseline update` re-measures the whole project and rewrites the file. **It is expected to shrink or
stay equal.** If the new state contains a finding that is new or worse, the command refuses and prints
it. Passing `--allow-growth` overrides that and *adds* debt: do it only when a reviewer has agreed, for
example after a dependency upgrade changed the wording of mypy messages, and say so in the pull
request. A reviewer reading a pull request that touches `scripts/quality/baselines/` should check that
the number of entries and the `total` did not grow.

If a baseline file is deleted, its gate is strict again (an empty baseline). This is how a gate leaves
the group once its debt is paid: fix the last finding, delete the file.

## Hooks

`install` makes every file in `.githooks/` executable and sets `core.hooksPath` to `.githooks` in the
repository's Git config (shared by all worktrees of the clone). The hooks call
`uv run --frozen python -m scripts.quality stage <name>` (`pre-commit` and `pre-push`), so `uv` must be on `PATH` and the environment
synced as above.

| Hook | Runs | Blocks |
|---|---|---|
| `pre-commit` | stage `pre-commit` on the **staged files** | yes |
| `pre-push` | stage `pre-push` on the **whole project**; only when the pushed commit is the checked-out `HEAD` (the gates read the working tree), pushing any other ref is not gated | yes |
| `post-commit` | refreshes the local GitNexus index in the background (needs `.gitnexus/run.cjs` and `node`) | never |

## Pipeline

Gates in the same group run in parallel; groups run left to right and the first failing group
stops the stage (cheapest checks first). A gate that cannot run (missing tool, no Docker, nothing
relevant staged) reports `SKIP` with the reason and does not fail the stage.

| Stage | Pipeline |
|---|---|
| `pre-commit` (staged files) | ruff, imports, bandit, semgrep, vulture, radon-cc, radon-mi -> mypy, pylint -> snapshots, tests-fast -> gitnexus |
| `pre-push` (whole project) | static group -> mypy, pylint -> tests -> e2e-postgres -> coverage -> compat, memray -> trivy -> qodana -> mutation (opt-in) -> gitnexus |
| `ci` | static group -> mypy, pylint -> tests -> e2e-postgres -> coverage -> memray -> trivy |

`pre-commit` scopes ruff, bandit, semgrep, radon and pylint to the staged files. mypy, vulture,
import-linter and the tests always run over the whole project but are skipped when nothing relevant is
staged. `QUALITY_FULL=1` makes `pre-commit` check the whole project.

CI does not call `stage ci` as one job; `.github/workflows/quality.yml` runs the same gates by name, split
across jobs:

| Workflow | What runs | Python |
|---|---|---|
| `quality.yml` job `static` | ruff, imports, bandit, semgrep, vulture, radon-cc, radon-mi, mypy, pylint, snapshots | 3.12 and 3.14 |
| `quality.yml` job `coverage` | `tests`, `e2e-postgres` (uses the runner's Docker), `coverage` | 3.12 |
| `quality.yml` jobs `memory`, `trivy` | `memray`, `trivy` | 3.12 |
| `quality.yml` job `qodana` | Qodana action with the `QODANA_TOKEN` repository secret; reports a notice and passes when the secret is missing; not run for pull requests from forks | n/a |
| `quality.yml` job `mutation` | `mutation` with `MUTATION=1`, weekly (Mondays 03:17 UTC) and on manual dispatch; **informational** (`continue-on-error`), it never turns the workflow red | 3.12 |
| `ci.yml` | architecture, integration and SQLite e2e suites plus `ruff` on Ubuntu and Windows; wheel build smoke test; offline Docker image test | 3.12 and 3.14 (Ubuntu and Windows), 3.13 for the wheel smoke test |
| `e2e.yml` | `tests/e2e` against PostgreSQL | 3.12 and 3.14 |

## Gates

| Gate | What it enforces | Config |
|---|---|---|
| `ruff` | lint (existing rule set) | `ruff.toml` |
| `imports` | layer contracts routes -> services -> protocols -> repositories | `[tool.importlinter]` |
| `bandit` | security lint on app/main/alembic/harness/scripts (baselined) | `[tool.bandit]` |
| `semgrep` | repository-specific rules (baselined); `SEMGREP_PACKS="p/python p/security-audit"` adds registry packs, which have no baseline and are therefore strict. Uses `semgrep` on `PATH`, else `uvx`, else the pinned Docker image | `.semgrep/forgetful.yml`, `.semgrepignore` |
| `vulture` | dead code, min confidence 60 (baselined) | `[tool.vulture]`, `vulture_whitelist.py` |
| `radon-cc` | no new function or method rated C or worse, tests included (baselined) | `radon.cfg` |
| `radon-mi` | no new file below maintainability grade A (score above 19), tests included (baselined) | `radon.cfg` |
| `mypy` | type check of `app`, `main.py`, `scripts` (baselined) | `[tool.mypy]` |
| `pylint` | score of at least 8.0/10 | `[tool.pylint]` |
| `snapshots` | syrupy snapshot tests (`-m snapshot`): CLI argument tree, settings defaults, SQLite and PostgreSQL schema, migration chain, MCP meta-tool signatures and tool catalogue, HTTP route table | `tests/integration/test_snapshots.py`, `tests/e2e_sqlite/test_snapshots_sqlite.py` |
| `tests-fast` | `tests/architecture` and `tests/integration`, stopping at the first failure | `pytest.ini` |
| `tests` | architecture + integration + SQLite e2e with branch coverage (erases previous coverage data first) | `[tool.coverage.*]` |
| `e2e-postgres` | `tests/e2e` (`-m e2e`) against a real PostgreSQL container, appending to the coverage data (needs Docker). If it fails with `Can't locate revision`, the container's database was migrated by another branch: `cd docker && docker compose down -v` | `tests/e2e/conftest.py` |
| `coverage` | combined line and branch coverage of `app` and `main.py` from the SQLite and PostgreSQL runs together must not fall below `fail_under` (**78 %** today) | `[tool.coverage.report]` |
| `compat` | the SQLite suites on Python 3.14 (`uv run --python 3.14` into `.venv314`; skipped without `uv`) | |
| `memray` | memory budgets (`@pytest.mark.limit_memory`) via pytest-memray, run as `pytest tests/e2e_sqlite -m memory --memray` (Linux/macOS only) | `tests/e2e_sqlite/test_memory_budget_sqlite.py` |
| `trivy` | HIGH/CRITICAL vulnerabilities (fixed ones), secrets and misconfigurations (`fs` scan) | `trivy.yaml`, `.trivyignore` |
| `qodana` | Qodana Ultimate Plus (`jetbrains/qodana-python`), token from `QODANA_TOKEN`; analyses a `git archive` export of `HEAD` (uncommitted changes are not seen) with `--image`; skipped when the `qodana` CLI or the token is missing | `qodana.yaml` |
| `mutation` | mutmut on changed `app/` modules; survivors above `MUTATION_MAX_SURVIVORS` fail. Opt-in (`MUTATION=1`), see below | `[tool.mutmut]` |
| `gitnexus` | `detect-changes` on the staged diff (pre-commit) or against `origin/main` (pre-push); a partial or truncated answer is retried once, then fails. Skipped without a local index or `node` | `.gitnexus/` (local index) |

`radon cc . -a -nc` and `radon mi . -s` work from the repository root and report the same files the
gates check (`radon.cfg` excludes virtualenvs and generated paths).

### pylint

`fail-under` is **8.0**. The code base scores 9.02/10 with the shipped configuration, so the
floor leaves a little room and a change that lowers the score noticeably fails. Raise the floor when
the score rises; never lower it to get a change through. Staged-file runs disable the convention and
refactor messages (`--disable=C,R`) because a score over a few files is meaningless for them; those
count in the project-wide score checked on push and in CI.

### Coverage

`tests` collects branch coverage from `tests/architecture`, `tests/integration` and `tests/e2e_sqlite`;
`e2e-postgres` appends the PostgreSQL run; `coverage` then compares the combined total with
`[tool.coverage.report] fail_under`. The PostgreSQL repositories are only reachable from `tests/e2e`,
so a machine without Docker cannot satisfy the gate: `e2e-postgres` reports `SKIP` and `coverage`
fails, because untested PostgreSQL code cannot be called covered. Branch coverage runs with
`parallel = true` and `concurrency = ["greenlet", "thread"]` (SQLAlchemy's async layer and aiosqlite)
and also follows subprocesses.

**Ratchet.** `fail_under` is the floor of the combined SQLite + PostgreSQL line and branch coverage
measured when the gate was introduced (78.4 to 78.5 % over repeated runs, floored to 78). Coverage may rise and
the floor must follow it: when your change raises the combined total by a full point, raise
`fail_under` in the same change; the target is 100. Never lower the floor to get a change through, add
the missing test instead. Use `# pragma: no cover` only for code that cannot execute in any supported
configuration, with a one-line reason; `[tool.coverage.report]` already excludes `TYPE_CHECKING`
blocks, `@overload`, `raise NotImplementedError`, bare `...` bodies and the `__main__` guard.

### Trivy

Findings that are known and accepted are listed in `.trivyignore`, each group with a reason and an end
date. Today that is the Dockerfile running as root (`AVD-DS-0002`, review by 2026-12-01) and the
vulnerable `pyjwt`, `urllib3` and `fsspec` pins of the base `uv.lock`, which the dependency bump in
pull request #102 replaces: delete those lines when #102 merges. Do not add new IDs without a reason
and a date.

### Qodana

The `qodana` gate (and the `qodana` job in CI) runs Qodana Ultimate Plus with a licence token.
`qodana.yaml` fails the run when a severity has **more** problems than its threshold. The thresholds
are a ratchet: they hold the number of findings measured on the code base when the gate was introduced
(1 Critical, 12 High; the Moderate and weaker findings do not gate), so the existing ones do not block
anybody while a new Critical or High finding does. Lower the numbers in the change that fixes
findings, never raise them to get a change through. What they currently allow: a type hint that is not
a type (`app/config/auth.py`), `except ValueError` ahead of `except ValidationError` in two skill
routes, unreachable statements in the memory service and tools, and a few calls of objects the
analyser believes are not callable. Without the token (or, locally, without the `qodana` CLI) the gate
reports `SKIP` and the CI job reports a notice and passes (see Secrets), so contributors without a
licence are not blocked.

### Snapshots

The snapshot tests pin the public surfaces that must not change by accident. A changed snapshot is a
contract change: review the diff in Git, then refresh deliberately.

| Surface | Test | Snapshot directory |
|---|---|---|
| CLI argument tree, settings defaults (built from code defaults, ignoring the environment and dotenv files; secrets and the build-derived `SERVICE_VERSION` are masked), SQLite and PostgreSQL DDL, Alembic revision chain | `tests/integration/test_snapshots.py` | `tests/integration/__snapshots__/test_snapshots/` |
| MCP meta-tool signatures, discovered tool catalogue, HTTP route table | `tests/e2e_sqlite/test_snapshots_sqlite.py` | `tests/e2e_sqlite/__snapshots__/test_snapshots_sqlite/` |

```bash
uv run pytest -m snapshot                     # what the gate runs
uv run pytest -m snapshot --snapshot-update   # rewrite the snapshots, then review `git diff`
```

Adding a setting, CLI flag, route, tool, table or migration changes a snapshot, which is expected;
commit the refreshed files with the change that caused them.

### Memory budgets

`tests/e2e_sqlite/test_memory_budget_sqlite.py` (marker `memory`) seeds memories through the MCP tools and
holds `@pytest.mark.limit_memory` budgets (bulk create, query with reranking). The ONNX models are loaded
before the measured section. Each budget is **headroom over the measured peak**, not a multiple of it, so
a test fails on a leak or an accidental full-table load and not on noise or a slower CPU:

| Test | Measured peak | Budget |
|---|---|---|
| bulk create (60 memories) | about 15 MB | 64 MB |
| query with reranking (20 memories, 20 queries) | about 175 MB, 132 MB of it inside onnxruntime inference (CPU dependent) | 384 MB |

Without `--memray` the tests run as ordinary smoke tests; on Windows the gate is skipped because memray
is not available there. Change a budget only with the new measurement in a comment next to it.

### Mutation testing

`mutation` runs `mutmut` over the modules a change touched. A run over the whole of `app/` produces roughly
33,000 mutants and is not practical, so the gate always needs a scope:

* the `app/` files that differ from `origin/main` (the default for `pre-push` and a plain
  `gate mutation`), or the `app/` files named with `--staged` or `--files`, or
* an explicit `MUTATION_TARGETS`, a space-separated list of mutmut name patterns such as
  `MUTATION_TARGETS='app.utils.*'`, which wins over both.

With no scope it reports `SKIP`. The gate allows one `mutmut run` two hours; surviving mutants in the
targets above `MUTATION_MAX_SURVIVORS` (default 0) fail it, so a scoped run fails whenever any mutant
survives: `MUTATION_TARGETS='app.utils.provenance.*'` leaves 9 surviving mutants today and therefore
fails until they are killed or tolerated with
`MUTATION_MAX_SURVIVORS=9 MUTATION_TARGETS='app.utils.provenance.*' uv run python -m scripts.quality gate mutation`.

`[tool.mutmut]` selects the SQLite-capable
suites (`tests/architecture`, `tests/integration`) as the tests that must kill a mutant and leaves
`app/repositories/*` (only the e2e suites reach them), `app/_version.py` and the 160 KB data module
`app/routes/mcp/tool_metadata_registry.py` unmutated (mutmut needs hours to generate mutants for it). The scheduled `quality.yml` job is **informational**: it sets `MUTATION=1`
with a fixed target list and a tolerance of 50 survivors, runs with `continue-on-error`, and so reports
survivors in its log without ever blocking a merge. Lower the tolerance as survivors get killed; drop
`continue-on-error` only when a maintainer wants mutation testing to block.

## Secrets

`QODANA_TOKEN` goes into the git-ignored dotenv file in the repository root (see `.env.example` for the
key name) or the environment. The runner reads only the keys a gate declares, takes the process
environment first, and never prints them; CI uses the `QODANA_TOKEN` repository secret. Do not put the
token in `qodana.yaml` or in any tracked file.

## Bypassing, deliberately

```bash
SKIP=qodana,trivy git push            # skip named gates once
ONLY=mypy uv run python -m scripts.quality stage pre-commit
QUALITY_FULL=1 git commit             # pre-commit over the whole project, not just staged files
MUTATION=1 git push                   # include mutation testing
MUTATION_TARGETS='app.utils.*' uv run python -m scripts.quality gate mutation   # one scoped gate
```

`SKIP` and `ONLY` take comma-separated gate names and apply to stages. `ONLY` runs just those gates of the
stage; naming the opt-in `mutation` gate in `ONLY` also selects it. `MUTATION=1` only opts the gate into a
stage: `gate mutation` runs it directly without that variable. Other knobs: `SEMGREP_PACKS` (extra registry packs, needs
network), `TRIVY_BIN` (explicit trivy binary; otherwise `PATH`, then the Docker image) and
`MUTATION_MAX_SURVIVORS`.

A skipped gate is a decision to record in the PR description, not a default. A gate whose tool is
missing (for example no Docker for `e2e-postgres`) reports `SKIP` with the reason and the
`coverage` gate then fails, because untested Postgres code cannot be called covered.

## Maintaining the thresholds

* Never raise a baseline or lower a floor to make a gate pass; see "Updating a baseline" above.
* Coverage: keep `fail_under` equal to the floor of the measured total and move it up with the code.
* New vulture false positives go into `vulture_whitelist.py` with a comment naming the consumer
  (framework hook, pydantic field, route registration). Run `uv run python -m scripts.quality gate vulture`
  (or `uv run vulture`) to list them as `file:line: unused name (NN% confidence)`, delete genuinely dead
  code instead of listing it, and put names that apply to a whole class of code (validators, route
  decorators, alembic or SQLAlchemy hooks) into `[tool.vulture]` `ignore_decorators` / `ignore_names`
  rather than the whitelist. The whitelist is only parsed by vulture, never imported or executed, and
  vulture does not scan `tests/`.
* New semgrep rules live in `.semgrep/forgetful.yml` (rule ids are prefixed `forgetful-`).
* Fix a bandit or semgrep finding when the code can be made safe. Suppress only code that is safe
  by construction, inline and with the reason on the same line: `# nosec B603 - argv list from
  constants, no shell` or `# nosemgrep: <rule-id> - reason`. Keep the matching `ruff.toml`
  per-file `S` ignore in step, and never add file-level skips to `[tool.bandit]`.
* The same convention applies to the other linters: `# noqa: <code> - reason` for ruff,
  `# type: ignore[<code>]` with a reason for mypy (`warn_unused_ignores` flags stale ones).
* New code should be clean: the scripts and the quality tests are rated B or better for complexity and
  grade A for maintainability, and are not in any baseline.
* Raise the Python matrix (`quality.yml`, `ci.yml`, `e2e.yml`, the `compat` gate's `COMPAT_PYTHON`)
  together.
