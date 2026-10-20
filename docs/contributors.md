# Contributing to Forgetful

This guide covers contribution expectations, local development, testing, and releases.

## Using AI tools

You're welcome to use coding agents, LLMs, and other AI tools when contributing.
You are responsible for everything you submit. Before opening a pull request,
read the full diff and make sure you understand how the changes work and why
they are needed.

Check the output yourself. Run the relevant tests and checks, inspect their
results, and explain in the PR how you verified the change. Be clear about
anything you couldn't test. You should be able to explain your approach in
your own words and answer questions during review.

The same responsibility applies to issues. Verify claims before posting and
include a reproduction or other concrete evidence. Treat automated audit
findings as leads to investigate before filing them.

## Issues, pull requests, and review capacity

Please keep contributions focused and check existing issues and PRs first.
Each submission takes time to review.

If an audit produces many findings, start with one summary issue containing
the findings you have checked. Agree on scope and priorities with a maintainer
before opening a batch of issues or pull requests.

Flooding the repository with unverified reports, duplicate issues, or bulk
PRs without prior agreement is spam. We will close these submissions in bulk,
without reviewing or responding to each one individually.

## Development setup

You need Python 3.12 or newer and uv. The main CI test jobs use Python 3.13.
These shell examples use Bash, including Bash in WSL.

```bash
git clone https://github.com/ScottRBK/forgetful.git
cd forgetful
uv sync --locked --all-extras --dev
```

Run the remaining commands from the repository root. Use `uv run` to run commands in the
project's Python environment without activating it manually.

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

## Running the source with Docker

You need Docker with the Compose plugin. The development Compose file builds the application
from your checkout and runs PostgreSQL alongside it.

If `docker/.env` does not exist, copy the example:

```bash
cp docker/.env.example docker/.env
```

Edit `docker/.env` before starting the containers. Keep `DATABASE=Postgres` and
`POSTGRES_HOST=forgetful-db` for this setup, and configure the database credentials.
The PostgreSQL container needs a nonempty `POSTGRES_PASSWORD` when creating its database.
See the [configuration guide](configuration.md) for the available settings.

Start the database and wait for it to be healthy, then build and start the application:

```bash
docker compose -f docker/docker-compose.yml up -d --wait forgetful-db
docker compose -f docker/docker-compose.yml up -d --build --wait forgetful-service
```

With the default port, the health endpoint is `http://127.0.0.1:8020/health`.
The first application startup may need to download local embedding and reranking models.
To inspect startup output:

```bash
docker compose -f docker/docker-compose.yml logs -f forgetful-service
```

Re-run the application build command after source changes. The default configuration copies
source into the image; it does not mount your checkout for live updates.

## Testing

We focus on integration and end-to-end tests that cover critical workflows. Add regression
coverage for changed behaviour, including a test that demonstrates a bug before fixing it.

The default embedding and reranking providers use local models. Tests that load these adapters
need network access on first use, or an existing model cache. Shared E2E adapters follow your
provider settings, so configuring a remote provider can make those tests call that service.

### Integration tests

Most tests in `tests/integration/` use in-memory stubs. Some, including the bootstrap and local
CLI tests, use real SQLite databases and local embeddings. This suite does not require Docker.

```bash
uv run pytest tests/integration/
```

### SQLite E2E tests

These tests exercise the application through MCP, HTTP, and CLI entry points using real SQLite.
Most use an in-memory database; tests that need persistence use temporary files.
Docker is not required.

```bash
uv run pytest tests/e2e_sqlite/
```

### PostgreSQL E2E tests

These tests require Docker with Compose and use PostgreSQL 16 with pgvector. The fixtures
start or reuse the container named `forgetful-db`, copying `docker/.env.example` to `docker/.env`
if that file is missing. The application runs inside the test process.

Use a disposable database: the fixtures delete application data before each test. They will
reuse an existing `forgetful-db` container, so check what it contains before running the suite.
Run these tests sequentially; concurrent runs would clear each other's data.

```bash
uv run pytest tests/e2e/ -m e2e
```

The fixtures leave the container running for later test runs. PostgreSQL tests are excluded
by default in `pytest.ini`; `-m e2e` selects them. Backup tests also need the client tools
described below. See the [PostgreSQL test guide](../tests/e2e/README.md) for fixture details.

### Docker image checks

Run these checks against an image already present in your Docker daemon. They prepare model and
tokenizer caches with network access, then test startup and search with networking disabled.
They also check the installed version and that data survives restart and container recreation.

```bash
docker build -f docker/Dockerfile --build-arg VERSION=0.0.0+dev -t forgetful:offline-test .
FORGETFUL_TEST_IMAGE=forgetful:offline-test FORGETFUL_TEST_VERSION=0.0.0+dev \
  uv run pytest tests/docker/ -v
```

The test skips when `FORGETFUL_TEST_IMAGE` is unset. It creates temporary containers and volumes
and removes them during cleanup.

### User creation tests

`test_user_creation_sqlite.py` and `test_user_creation_e2e.py` share cases that check real duplicate
inserts, preservation of the existing user, recovery when another request creates the user first,
and propagation of unrelated database errors; only the timing of the competing lookup is arranged.

### Backup and recovery tests

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

To select a different disposable database on localhost, set `PGPORT`, `POSTGRES_DB`,
`POSTGRES_USER`, and `POSTGRES_PASSWORD` to match it. The PostgreSQL fixtures still check
for the `forgetful-db` Docker container.

## Linting

Run Ruff before submitting changes:

```bash
uv tool run ruff check .
```

## GitHub Actions

The workflow files in [`.github/workflows/`](../.github/workflows/) define the checks and release
jobs. CI and PostgreSQL tests run on branch pushes and pull requests. A push to a branch with an
open PR can start both runs; newer runs cancel older runs for the same workflow and ref.

### CI

[`ci.yml`](../.github/workflows/ci.yml) contains three jobs:

- `test` runs architecture checks, integration tests, SQLite E2E tests, and Ruff on Ubuntu
  and Windows with Python 3.13.
- `smoke-test` runs after the test matrix succeeds. It builds the Python wheel, checks for
  migration files, and verifies installation and the CLI help command.
- `docker-offline` builds an image and runs the Docker image checks described above.

### PostgreSQL tests

[`e2e.yml`](../.github/workflows/e2e.yml) runs the PostgreSQL suite on Ubuntu with Python 3.13.
It installs the PostgreSQL client tools and runs `tests/e2e/` with `-m e2e`, including backup
and recovery checks. It also supports manual runs through `workflow_dispatch`.

Workflow definitions alone do not block merges. Maintainers must configure required status
checks in GitHub branch rules, including the relevant matrix checks.

### Docker image publishing

[`build.yml`](../.github/workflows/build.yml) runs when a tag matching `v*` is pushed. Use a
semantic version such as `v1.2.3`. It builds the image, runs the Docker image checks against
that image, and publishes it to `ghcr.io/scottrbk/forgetful` only after those checks pass.

A stable release such as `v1.2.3` produces `1.2.3`, `1.2`, and `latest` image tags.
Prerelease version tags retain their full version without updating the stable image tags.
The workflow keeps image provenance and does not cancel an in-progress publication.

### Python package publishing

[`publish.yml`](../.github/workflows/publish.yml) runs when a GitHub release is published.
It builds the Python package with `uv build` and publishes to PyPI through the `pypi` GitHub
environment using trusted publishing. This workflow does not run the test suites itself.

## Creating a release

These steps are for maintainers with permission to publish releases.

1. Merge the release changes and check out the commit you intend to release. Confirm that CI
   and the PostgreSQL suite passed for that commit.
2. Choose an unused semantic version, replace `vX.Y.Z` below, then create and push the tag:

   ```bash
   RELEASE_TAG=vX.Y.Z
   git tag "$RELEASE_TAG"
   git push origin "$RELEASE_TAG"
   ```

3. Check that the Build workflow succeeds and publishes the expected container image.
4. Publish a GitHub release for the same tag to trigger PyPI publishing, then check that
   the Publish to PyPI workflow succeeds.

To run a published image, use the [SQLite](../docker/docker-compose.sqlite.yml) or
[PostgreSQL](../docker/docker-compose.postgres.yml) Compose file. The
[README's Docker instructions](../README.md#option-3-docker-deployment-productionscale)
describe their configuration.
