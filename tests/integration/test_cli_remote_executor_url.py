"""Integration tests for CLI server URL normalisation.

Covers two regressions in ``normalize_server_url``:

* an upper-case ``HTTP://`` / ``HTTPS://`` scheme passed validation but fastmcp could not
  infer a transport from it;
* ``/mcp`` was appended to the raw string, so URLs with a query or fragment grew a
  doubled mount path every time they were normalised again.

The fastmcp client is stubbed through the client-factory seam where one is needed.
"""

from urllib.parse import urlsplit

import pytest

from app.routes.cli.remote_executor import RemoteExecutor, normalize_server_url

USER = "alice"
SECRET = "s3cretPassw0rd"


class StubClient:
    """Stands in for fastmcp.Client; only constructed, never connected."""


# =============================================================================
# Scheme normalisation
# =============================================================================
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("HTTP://localhost:8020", "http://localhost:8020/mcp"),
        ("HTTPS://example.com", "https://example.com/mcp"),
        ("Http://localhost:8020", "http://localhost:8020/mcp"),
        ("HTTPS://Example.com/custom", "https://Example.com/custom"),
    ],
)
def test_normalize_lowercases_the_scheme(raw, expected):
    assert normalize_server_url(raw) == expected


@pytest.mark.parametrize("raw", ["HTTP://localhost:8020", "HTTPS://example.com"])
def test_remote_executor_builds_a_real_client_for_an_uppercase_scheme(raw):
    # Default factory -> real fastmcp.Client; transport inference happens at construction.
    executor = RemoteExecutor(raw, token="t")

    assert executor.server_url == normalize_server_url(raw)
    assert urlsplit(executor.server_url).scheme in {"http", "https"}


# =============================================================================
# Mount path handling: only the path component is edited
# =============================================================================
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://host.example.com/?key=abc", "https://host.example.com/mcp?key=abc"),
        ("https://host.example.com?x=1", "https://host.example.com/mcp?x=1"),
        ("https://host.example.com/#frag", "https://host.example.com/mcp#frag"),
        ("https://host.example.com?x=1#frag", "https://host.example.com/mcp?x=1#frag"),
        ("host.example.com:8020?x=1", "https://host.example.com:8020/mcp?x=1"),
        ("localhost:8020/?x=1", "http://localhost:8020/mcp?x=1"),
        # An explicit path is kept (minus a trailing slash), query intact.
        ("https://host.example.com/custom/?x=1", "https://host.example.com/custom?x=1"),
        ("https://host.example.com/custom/", "https://host.example.com/custom"),
    ],
)
def test_mount_path_lands_in_the_path_not_the_query_or_fragment(raw, expected):
    assert normalize_server_url(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "https://host.example.com/?key=abc",
        "https://host.example.com?x=1",
        "https://host.example.com/#frag",
        "HTTPS://host.example.com",
        "localhost:8020",
        "https://host.example.com/custom/",
        f"http://{USER}:{SECRET}@host.example.com:8020",
    ],
)
def test_normalize_is_idempotent(raw):
    once = normalize_server_url(raw)

    assert normalize_server_url(once) == once


def test_stored_url_is_not_grown_by_renormalising_in_remote_executor():
    # auth login stores the normalised URL; every later command normalises it again.
    stored = normalize_server_url("https://host.example.com/?key=abc")
    seen = {}

    def factory(url, token):
        seen["url"] = url
        return StubClient()

    RemoteExecutor(stored, token="t", client_factory=factory)

    assert seen["url"] == stored
    assert urlsplit(stored).path == "/mcp"
