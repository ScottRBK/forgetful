# Forgetful Development Guide

## Architecture

Before changing code or reasoning about this repository's architecture, read the
[architecture overview](architecture.md).

Consult the [detailed class map](docs/assets/mycelium_class_diagram.md) only as needed,
using the overview's reading advisories. Do not load the entire map into context by default.

After major code changes, check whether the architecture diagram or explanations are still
accurate and update them if needed. Small changes do not require diagram regeneration.
Preserve reviewed explanations that remain accurate. Keep the overview at most 500 lines;
it has no column-width limit, including Mermaid statements.

Mycelium is optional tooling, not a prerequisite for contributing or updating the overview.
Its [architecture skill][mycelium-architecture] and [map-generation skill][mycelium-mermaid]
are available in [ScottRBK/mycelium][mycelium] if useful. If refreshing the generated backup,
use fresh analysis, keep the JSON outside the repository, and export full detail with
`--max-classes 1000`, `--test-path tests`, and `--test-path test_harness/runs`.

[mycelium]: https://github.com/ScottRBK/mycelium
[mycelium-architecture]:
  https://github.com/ScottRBK/mycelium/blob/master/skills/mycelium-architecture/SKILL.md
[mycelium-mermaid]:
  https://github.com/ScottRBK/mycelium/blob/master/skills/mycelium-mermaid/SKILL.md

Layered architecture:
 routes -> services -> protocols -> repositories/adapters 
No pollution of service layer with integration/implementation details

## Testing Philosophy
We focus on **integration and E2E tests** over unit tests. Tests should cover critical workflows without exhaustive edge case coverage.

Aim for each test to finish in under 15 seconds; this is advisory, with no enforced timing checks.

### Integration Tests
**Location**: `tests/integration/`
**Purpose**: Test business logic with stubbed I/O (no real database required)
**Run locally**:
```bash
uv run pytest tests/integration/
```
These tests use in-memory stubs and run fast (~seconds). They form the bulk of our test suite and catch 90% of issues.

### End-to-End Tests

#### SQLite E2E Tests
**Location**: `tests/e2e_sqlite/`
**Purpose**: Test complete stack with in-memory SQLite
**Requirements**: None (no Docker required)
**Run locally**:
```bash
uv run pytest tests/e2e_sqlite/
```
These tests use an in-memory SQLite database for test isolation. Fast execution with automatic cleanup. 

#### PostgreSQL E2E Tests
**Location**: `tests/e2e/`
**Purpose**: Test complete stack with real PostgreSQL
**Requirements**: PostgreSQL running in Docker
**Run locally**:
```bash
cd docker && docker compose down -v  
uv run pytest -m e2e
```
**Remember**: rebuild docker image if running local container service, not required however for e2e tests.


## Linting
Ensure that you run ruff following any changes and address any issues raised
```bash
uv tool run ruff check .
```

**Note**: Ruff UP006 rule enforces Python 3.12+ built-in generics (`list` instead of `typing.List`, `dict` instead of `typing.Dict`, etc.). This catches legacy type hint syntax automatically.

## Skills 
The solution has a [catalogue of skills](./skills/) that is used to help drive agent behaviour, 
whenever adding or modifying behaviour around tools or the system, you should look to review these 
and consider whether these need updating as part of the changes you have made to the solution as well.
