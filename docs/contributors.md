# Contributing to Forgetful

This guide covers testing and deployment workflows for contributors.

## Architecture

Before changing code, read the [architecture overview](../architecture.md).
The [detailed class map](assets/mycelium_class_diagram.md) is supporting material;
use the overview's advisories to read relevant sections rather than the whole file.

Run `uv run pytest tests/architecture/` before submitting code changes; CI runs the same check.
It checks imports, verifies that every `app` module is scanned, and proves each rule rejects
forbidden dependencies; see [the rules and validation notes](dev/architecture-tests.md).

After major code changes, check whether the architecture diagram or explanations need updating.
Update them when the architecture has changed; small changes do not require regeneration.
Preserve reviewed explanations that remain accurate. Keep the overview at most 500 lines,
with no column-width limit, including Mermaid statements.

You do not need Mycelium to contribute or update the overview. If useful, the optional
[Mycelium architecture skill][mycelium-architecture] and [map-generation skill][mycelium-mermaid]
are published in [ScottRBK/mycelium][mycelium]. When refreshing the generated backup, run fresh
analysis, keep the JSON outside the repository, and export full detail to
`docs/assets/mycelium_class_diagram.md` with `--max-classes 1000`, `--test-path tests`, and
`--test-path test_harness/runs`. Verify nonempty diagrams and repeat-export consistency.

[mycelium]: https://github.com/ScottRBK/mycelium
[mycelium-architecture]:
  https://github.com/ScottRBK/mycelium/blob/master/skills/mycelium-architecture/SKILL.md
[mycelium-mermaid]:
  https://github.com/ScottRBK/mycelium/blob/master/skills/mycelium-mermaid/SKILL.md

## Running with Docker with source 
This will approach will fall back to using the build and as such allow you to check any changes you have made inside of a container. 

```bash
git clone https://github.com/ScottRBK/forgetful.git
cd forgetful
```

```bash
cd docker
docker compose up -d --build
```

**Optional**: Customize configuration by copying the example environment file:

```bash
cd docker
cp .env.example .env
# Edit .env with your custom values
docker compose up -d
```


## Testing Philosophy

We focus on **integration and E2E tests** over unit tests. Tests should cover critical workflows without exhaustive edge case coverage.

### Integration Tests

**Location**: `tests/integration/`

**Purpose**: Test business logic with stubbed I/O (no real database required)

**Run locally**:
```bash
pytest tests/integration/
```

These tests use in-memory stubs and run fast (~seconds). They form the bulk of our test suite and catch 90% of issues.

### End-to-End Tests

#### SQLite E2E Tests

**Location**: `tests/e2e_sqlite/`

**Purpose**: Test complete stack with in-memory SQLite

**Requirements**: None (no Docker required)

**Run locally**:
```bash
pytest tests/e2e_sqlite/
```

**CI Status**: ✅ Runs automatically in CI workflow on every push/PR

These tests use an in-memory SQLite database for test isolation. Fast execution (~30 seconds for 94 tests) with automatic cleanup. They provide full-stack coverage without Docker dependencies, making them ideal for CI.

#### PostgreSQL E2E Tests

**Location**: `tests/e2e/`

**Purpose**: Test complete stack with real PostgreSQL

**Requirements**: PostgreSQL running in Docker

**Run locally**:
```bash
# Start PostgreSQL
docker compose -f docker/docker-compose.yml up -d forgetful-db

# Run E2E tests
pytest -m e2e
```

**CI Status**: Runs on every branch push, pull request, and manual workflow dispatch.

These tests are marked with `@pytest.mark.e2e` and validate the full application stack with
PostgreSQL. Use a disposable database: the E2E fixtures clear its application tables.

#### User creation tests

`test_user_creation_sqlite.py` and `test_user_creation_e2e.py` share cases that check real duplicate
inserts, preservation of the existing user, recovery when another request creates the user first,
and propagation of unrelated database errors; only the timing of the competing lookup is arranged.

#### Backup and recovery tests

These tests use a temporary SQLite file or the PostgreSQL E2E database. They check that a
backup restores memories, metadata, links, obsolete state, and searchable vectors. They also
run the real CLI, fail the embedding provider after a saved batch or during the final search
check, and verify that automatic recovery restores the original data.

The embedding provider returns fixed vectors, so these tests need no model downloads or API keys.
PostgreSQL requires `pg_dump` and `psql` compatible with the PostgreSQL 16 test server. CI installs
the client tools explicitly and fails if either is missing; local runs skip with an explanation.

```bash
uv run pytest tests/e2e_sqlite/test_backup_restore_sqlite.py -q --durations=5
uv run pytest tests/e2e/test_backup_recovery_e2e.py \
  tests/e2e/test_zz_backup_restore_e2e.py -m e2e -q --durations=5
```

To target a disposable database already running on port 55099, prefix the PostgreSQL command
with `PGPORT=55099 POSTGRES_DB=forgetful_backup_tests`. Set `POSTGRES_USER` and
`POSTGRES_PASSWORD` to that test database's credentials as needed.

Both suites run in the existing CI jobs. A push to a branch with an open PR starts both a push
run and a PR run; newer runs cancel older runs for the same workflow and ref.

---
## Linting
linting with ruff and uv
```bash
uv tool run ruff check .
```

## CI/CD Workflows

### `ci.yml` - Continuous Integration

**Triggers**: Every push and pull request

**Purpose**: Fast feedback for contributors

**Steps**:
1. Check architecture boundaries and rule proofs (no database or provider calls).
2. Run integration tests (stubbed, no Docker).
3. Run SQLite E2E tests (real SQLite, full stack).
4. Run linting.

**Merge requirements**: Configure branch rules to require this workflow's `test` check.
The workflow alone does not make it mandatory for merging.

**Test Coverage**: Integration tests validate business logic with stubs. SQLite E2E tests validate the complete application stack including real database interactions, all without Docker dependencies.

### `e2e.yml` - PostgreSQL E2E Validation

**Triggers**: Every branch push, pull request, and manual workflow dispatch

**Purpose**: Validate with real PostgreSQL database

**Steps**:
1. Install PostgreSQL backup client tools.
2. Run PostgreSQL E2E tests (`tests/e2e/` with `-m e2e` marker), including backup recovery.

**Merge requirements**: Configure the repository's branch rules to require the `e2e` check.
The workflow alone does not make a check mandatory for merging.

**Test Coverage**: Validates the full application stack with PostgreSQL, including real
`pg_dump`/`psql` backup and restore.

### `build.yml` - Docker Image Build

**Triggers**: Version tag push only (e.g., `v0.1.0`, `v1.0.0`)

**Purpose**: Build and publish release images

**Steps**:
1. Build Docker image
2. Tag with semver, SHA, and `latest`
3. Push to GitHub Container Registry (`ghcr.io/scottrbk/forgetful`)

**Note**: Only runs when you manually create a release tag

---

## Creating a Release

1. Commit your changes to `main` branch
2. Create and push a version tag:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```
3. Build workflow automatically creates Docker image

---

## Deployment

**Workflow**: `deploy.yml`

**Purpose**: Deploy to staging/production environments

**Method**: Self-hosted runners with sparse checkout

**Environment Selection**: Runners match environment by label (e.g., `staging` runner for staging deployment)
