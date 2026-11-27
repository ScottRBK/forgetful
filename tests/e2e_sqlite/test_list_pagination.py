"""Complete pagination and full-client regressions using real SQLite fixtures."""
import pytest

from tests.list_pagination_cases import (
    FixedPaginationEmbeddings,
    PaginationCases,
    PaginationEnvironment,
)
from tests.list_pagination_compatibility_cases import PaginationCompatibilityCases


@pytest.fixture(scope="module")
def embedding_adapter():
    return FixedPaginationEmbeddings()


@pytest.fixture(scope="module")
def reranker_adapter():
    return None


@pytest.fixture
def pagination_environment(http_client, sqlite_app):
    return PaginationEnvironment(http_client, sqlite_app, "SQLite")


@pytest.mark.parametrize(
    ("case", "expected_error"),
    [
        ("plan-project", "Invalid value for 'project_id': must be an integer"),
        ("task-plan", "Invalid value for 'plan_id': must be an integer"),
        ("task-state", "Invalid state: bogus. Valid: todo, doing, waiting, done, cancelled"),
        ("task-priority", "Invalid priority: bogus. Valid: P0, P1, P2, P3"),
        ("memory-links-limit", "Invalid value for 'limit': must be an integer"),
    ],
)
@pytest.mark.asyncio
async def test_malformed_list_filters_return_400(http_client, case, expected_error):
    """Malformed list filters return 400 instead of escaping the ASGI app."""
    project = await http_client.post("/api/v1/projects", json={
        "name": f"Invalid filter {case}",
        "description": "Invalid list filter regression",
        "project_type": "development",
    })
    assert project.status_code == 201, project.text
    plan = await http_client.post("/api/v1/plans", json={
        "project_id": project.json()["id"],
        "title": f"Invalid filter {case}",
    })
    assert plan.status_code == 201, plan.text
    memory = await http_client.post("/api/v1/memories", json={
        "title": f"Invalid filter {case}",
        "content": "Invalid list filter regression",
        "context": "REST validation",
        "keywords": ["validation"],
        "tags": ["test"],
        "importance": 5,
    })
    assert memory.status_code == 201, memory.text

    urls = {
        "plan-project": "/api/v1/plans?project_id=not-an-int",
        "task-plan": "/api/v1/tasks?plan_id=not-an-int",
        "task-state": f"/api/v1/tasks?plan_id={plan.json()['id']}&state=bogus",
        "task-priority": f"/api/v1/tasks?plan_id={plan.json()['id']}&priority=bogus",
        "memory-links-limit": (
            f"/api/v1/memories/{memory.json()['id']}/links?limit=not-an-int"
        ),
    }
    try:
        response = await http_client.get(urls[case])
    except Exception as error:  # The ASGI test transport re-raises unhandled app errors.
        pytest.fail(f"GET {urls[case]} raised {error!r}")

    assert response.status_code == 400
    assert response.json() == {"error": expected_error}


class TestSQLiteListPagination(PaginationCases, PaginationCompatibilityCases):
    pass
