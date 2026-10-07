# Forgetful Development Guide

## Architecture

Before changing code or reasoning about this repository's architecture, read the
[Mycelium class diagram](docs/assets/mycelium_class_diagram.md).

After completing code changes, regenerate the diagram using [Mycelium][mycelium] and its
[`mycelium-mermaid` skill][mycelium-mermaid]. If the skill is not installed, follow the
instructions at that link.
Run a fresh analysis; do not reuse an older map. Keep the JSON map outside the repository.
Export to `docs/assets/mycelium_class_diagram.md` with `--max-classes 1000`,
`--test-path tests`, and `--test-path test_harness/runs`. Verify the diagram is nonempty.

[mycelium]: https://github.com/ScottRBK/mycelium
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
