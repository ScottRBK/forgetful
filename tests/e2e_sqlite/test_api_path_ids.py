"""E2E tests for integer IDs in REST API paths.

A path ID that is not an integer is a client error. Every REST route returns HTTP 400 with
the same JSON error as an invalid integer query parameter, never an unhandled server error.
The cases come from the registered routes, so new routes are checked automatically.
"""
import re

import pytest
from starlette.routing import Route

VALID_NON_ID_VALUES = {"entity_type": "memory"}


def path_id_requests(app):
    """Return (method, url, name) for each integer path ID of each REST route."""
    requests = []
    for route in app.routes:
        if not isinstance(route, Route) or not route.path.startswith("/api/v1/"):
            continue
        names = re.findall(r"{(\w+)}", route.path)
        for name in (item for item in names if item.endswith("_id")):
            values = {item: VALID_NON_ID_VALUES.get(item, "1") for item in names}
            values[name] = "not-an-id"
            url = route.path.format(**values)
            requests.extend((method, url, name) for method in sorted(route.methods - {"HEAD"}))
    return requests


@pytest.mark.asyncio
async def test_non_integer_path_ids_return_400(sqlite_app, http_client):
    """Each route returns HTTP 400 for a non-integer path ID."""
    requests = path_id_requests(sqlite_app.http_app())
    assert ("POST", "/api/v1/entities/not-an-id/memories", "entity_id") in requests

    failures = []
    for method, url, name in requests:
        try:
            response = await http_client.request(method, url, json={})
        except Exception as error:  # The ASGI test transport re-raises unhandled app errors.
            failures.append(f"{method} {url}: raised {error!r}")
            continue
        expected = {"error": f"Invalid value for '{name}': must be an integer"}
        if response.status_code != 400 or response.json() != expected:
            failures.append(f"{method} {url}: {response.status_code} {response.text[:120]}")

    assert failures == [], "\n".join(failures)
