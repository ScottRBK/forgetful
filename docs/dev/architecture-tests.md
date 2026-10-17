# Architecture checks

The rules live in `pyproject.toml`; [architecture.md](../../architecture.md) explains their scope.
They prevent the imports agreed in the architecture review:

- Models and shared code must not import services, repositories, or entry points.
- Services must not import repositories or entry points.
- Repositories must not import services or entry points.
- Shared code and services must not import the listed database/provider/backup libraries.
- API/MCP handlers must not import repositories or bootstrap.
- CLI code must use services, with two explicit bootstrap imports allowed for startup.

## Run locally

```bash
uv sync --locked --dev
uv run --frozen lint-imports --no-cache
uv run --frozen pytest tests/architecture/ -v
```

The pytest command includes the real repository check, source-file coverage, and rule proofs.
It needs no database, model downloads, or service credentials after dependencies are installed.
CI runs it as a required successful step in the existing `test` job on every push and PR.
Branch protection must separately require that job to block merges.

## How the rules are tested

`tests/architecture/test_contracts.py` creates disposable packages under pytest's temporary path.
Each proof uses one production contract, isolated because the production rules overlap:

1. A clean package passes, including startup wiring and service-to-protocol imports.
2. The forbidden import passes with the target contract removed.
3. The same import fails with the contract enabled, naming the rule and dependency path.
4. Removing the import restores a passing result.

Each of the six rules is tested with a direct import, an indirect import through a neutral
helper, a re-export, a `TYPE_CHECKING` import, and an import inside a function.
The helper is outside both endpoint areas, so it proves indirect checking rather than another
direct violation. Every command uses `--no-cache`, and unexpected checker errors fail the proof.

The coverage test compares every `app/**/*.py` file with Grimp's discovered modules.
Removing a package marker or adding an undiscovered file must fail it.
The CLI rule allows only `local_executor -> bootstrap` and `context -> bootstrap` as startup
imports. Fixtures include both imports so the ignore list matches; a stale exception fails the
real repository check.
A separate proof confirms HTTP/MCP cannot reach bootstrap through either CLI startup path;
these exceptions do not apply to the HTTP/MCP rule.
The coverage check also rejects misspelled internal forbidden module names, which Import Linter
would otherwise silently skip.
`main.py` remains manually reviewed; migrations, tests, and the evaluation harness are outside
these production contracts. Dynamic imports and object attribute access require code review and
behaviour tests.

## Implementation evidence — 2026-10-17

Before refactoring, six new real-database cases passed: duplicate creation and both service
recovery paths, on SQLite and PostgreSQL. After changing the duplicate-error expectation to
`ConflictError`, the repository test failed until error translation was implemented.
An additional case verifies unrelated insert failures are not labelled as duplicates.

The first architecture run exposed 19 unscanned files. Adding package markers exposed the
expected three broken contracts: services, external integrations, and routes. The other two
contracts already passed. All five original rules now pass without ignored imports.
The additional CLI rule passes with only the two explicit startup exceptions above.
The proofs retain the absent-rule, rejection, and recovery checks described above.

The rebuild wiring tests first failed when given an explicit rebuild service; after changing
startup and handlers, bootstrap and actual MCP rebuild tests passed. Existing full/targeted
rebuild tests and real backup recovery tests cover the moved implementation.

Local validation:

- Architecture, integration, and SQLite: 1,317 passed in 255.10 seconds, with 11 existing SQLite
  activity skips (those workflows run in PostgreSQL).
- PostgreSQL: 328 passed in 61.72 seconds against a disposable database.
- After adding the CLI rule: all 39 architecture checks passed in 12.49 seconds; production code
  was unchanged from the full regression run.
- Ruff, whitespace checks, workflow YAML/shell syntax, and wheel packaging passed.
- The first full run exposed a timing-sensitive cache-expiry test; it passed alone and now uses
  controlled time to check just before and exactly at expiry, with no production auth changes.
- A disposable-copy check confirmed that a misspelled forbidden module passes Import Linter but
  fails our module-inventory test; correcting the name restores a passing result.

Opus reviewed the production changes, follow-up fixes, and additional CLI rule with no blocking
findings. Hosted CI must be verified for the pushed commit; local results do not establish hosted
success.

## Checker dependency audit

Import Linter 2.15 and Grimp 3.17 are development-only additions, pinned by `uv.lock`.
Both support Python 3.10+, including this project's Python 3.12+ requirement, and use BSD-2-Clause.
Sources: [Import Linter release metadata](https://pypi.org/pypi/import-linter/2.15/json),
[Grimp release metadata](https://pypi.org/pypi/grimp/3.17/json).

The exact locked dependency set was checked against PyPI release metadata on 2026-10-17:

| Package | Version | License |
| --- | --- | --- |
| import-linter | 2.15 | BSD-2-Clause |
| grimp | 3.17 | BSD-2-Clause |
| click | 8.4.2 | BSD-3-Clause |
| rich | 14.3.2 | MIT |
| markdown-it-py | 4.0.0 | MIT |
| mdurl | 0.1.2 | MIT |
| pygments | 2.20.0 | BSD-2-Clause |
| typing-extensions | 4.15.0 | PSF-2.0 |

PyPI reported no advisories for these versions at that time; this is a point-in-time check,
not a guarantee of future safety. Existing dependency versions and CI action versions were retained.
Configuration was checked against Context7's Import Linter documentation and the installed CLI.

References: [forbidden contracts][forbidden], [configuration][configuration], [Grimp usage][grimp].

[forbidden]: https://import-linter.readthedocs.io/en/stable/contract_types/forbidden/
[configuration]: https://import-linter.readthedocs.io/en/stable/get_started/configure/
[grimp]: https://grimp.readthedocs.io/en/latest/usage.html
