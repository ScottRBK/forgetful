# PostgreSQL E2E tests

Run from the repository root:

```bash
uv run pytest tests/e2e/ -m e2e
uv run pytest tests/e2e/test_reranking_e2e.py -m e2e
uv run pytest tests/e2e/test_reranking_e2e.py::test_reranking_orders_by_score_e2e -m e2e
```

The fixtures start or reuse the `forgetful-db` Docker container and clear its application tables.
Run these tests sequentially against the test database; concurrent runs share and clear the same
data.

## Isolation pattern

- Create every record the test needs, and use the IDs returned by those create operations.
- All application rows are deleted before each test, including users and activity history.
  Deletion is faster than truncation for these small datasets; sequences keep advancing.
  Add new tables to `ALL_TABLES` in `conftest.py` before their parents when extending the schema.
- Each test gets a fresh app, services, event bus, and clients. The PostgreSQL container,
  migrations, connection pool, embedding model, and reranker stay shared for speed.
- Use `SETTINGS_OVERRIDE` for module defaults and `monkeypatch` for individual test overrides.
  The app fixture restores its overrides after each test, including when setup fails.
- Request `wait_for_events` and call `await wait_for_events()` before checking background activity
  or access tracking through the API. App teardown also waits for pending handlers before the next
  test can clear the tables. Use explicit readiness signals for streaming tests.
- Assert exact counts where the test controls the complete result set. Reranking tests must create
  more candidates than the requested `k` and assert non-null, ordered `rerank_score` values from the
  response; returning memories alone does not prove reranking ran.

Repository operations commit their own database sessions, so wrapping a test in an unrelated
transaction would not isolate its writes. Backup/restore tests also replace database objects and
must recycle the connection pool after restoration.

When changing these fixtures, check affected tests individually, repeat them against the same
container, and run the full suite in both normal and reordered execution. The repeated project-list
test protects against accidentally returning to module-only data cleanup. Runtime guidance remains
advisory in the repository's `AGENTS.md`; there are no timing gates.
