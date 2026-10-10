"""Exercise a built image through its default command and public HTTP API.

FORGETFUL_TEST_IMAGE must name an image already present in the Docker daemon.
Model preparation needs internet; the application containers have no network.
"""

import json
import os
import shutil
import subprocess
import time
from uuid import uuid4

import pytest


def docker(*args, check=True, timeout=60):
    executable = shutil.which("docker")
    assert executable is not None, "The Docker CLI is required for image tests"
    result = subprocess.run(  # noqa: S603 - test-controlled arguments, no shell
        [executable, *args], capture_output=True, text=True, timeout=timeout,
    )
    if check:
        assert result.returncode == 0, result.stdout + result.stderr
    return result


@pytest.fixture
def offline_image():
    image = os.environ.get("FORGETFUL_TEST_IMAGE")
    if not image:
        pytest.skip("Set FORGETFUL_TEST_IMAGE to run the Docker image regression test")

    # Resolve the tag once so all preparation and checks use the same local image.
    image_id = docker("image", "inspect", "--format", "{{.Id}}", image).stdout.strip()
    suffix = uuid4().hex
    container = f"forgetful-offline-{suffix}"
    cache = f"{container}-cache"
    data = f"{container}-data"
    environment = [
        "-e", "DATABASE=SQLite",
        "-e", "SQLITE_PATH=/data/forgetful.db",
        "-e", "FASTEMBED_CACHE_DIR=/cache/fastembed",
        "-e", "TIKTOKEN_CACHE_DIR=/cache/tiktoken",
        "-e", "RERANKING_ENABLED=true",
        "-e", "SERVER_HOST=0.0.0.0",
        "-e", "SERVER_PORT=8020",
    ]

    try:
        docker("volume", "create", cache)
        docker("volume", "create", data)
        # Use Python directly: preparation must not populate a uv build cache.
        docker(
            "run", "--rm", "--pull", "never", "--name", f"{container}-prepare",
            "-v", f"{cache}:/cache", *environment,
            "--entrypoint", "/app/.venv/bin/python", image_id, "-c",
            "from app.bootstrap import get_embedding_adapter, get_reranker_adapter; "
            "from app.utils.token_counter import TokenCounter; "
            "get_embedding_adapter(); get_reranker_adapter(); TokenCounter()",
            timeout=600,
        )
        yield image_id, container, cache, data, environment
    finally:
        # Keep trying cleanup even if an earlier command times out.
        for command in [
            ("logs", container),
            ("logs", f"{container}-prepare"),
            ("rm", "-f", container, f"{container}-prepare"),
            ("volume", "rm", cache, data),
        ]:
            try:
                result = docker(*command, check=False, timeout=15)
                print(result.stdout + result.stderr)
            except (subprocess.TimeoutExpired, OSError) as error:
                print(f"Docker cleanup failed for {command}: {error}")


def request(container, path, payload=None):
    command = [
        "exec", container, "curl", "--fail-with-body", "--silent", "--show-error",
        "--max-time", "30", f"http://127.0.0.1:8020{path}",
    ]
    if payload is not None:
        command += ["-H", "Content-Type: application/json", "--data", json.dumps(payload)]
    return json.loads(docker(*command).stdout)


def wait_for_health(container, expected_version):
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        running = docker("inspect", "--format", "{{.State.Running}}", container).stdout
        if running.strip() != "true":
            pytest.fail("Container exited before becoming healthy")
        result = docker(
            "exec", container, "curl", "--fail", "--silent", "--max-time", "2",
            "http://127.0.0.1:8020/health", check=False,
        )
        if result.returncode == 0:
            health = json.loads(result.stdout)
            assert health["status"] == "healthy"
            assert health["version"] == expected_version
            return
        time.sleep(0.5)
    pytest.fail("Container did not become healthy within 120 seconds")


def assert_search_works(container, memory_ids):
    result = request(container, "/api/v1/memories/search", {
        "query": "What is the team's code word?",
        "query_context": "Recall the team's stored information while offline",
        "k": 1,
        "include_links": 0,
    })
    assert len(result["primary_memories"]) == 1
    assert result["primary_memories"][0]["id"] in memory_ids
    assert result["token_count"] > 0
    # Two candidates with k=1 exercise the local cross-encoder as well.
    assert result["scores"][0]["rerank_score"] is not None


def test_image_starts_and_queries_offline_after_restart_and_recreation(offline_image):
    image_id, container, cache, data, environment = offline_image
    expected_version = os.environ.get("FORGETFUL_TEST_VERSION", "0.0.0+dev")

    # Arrange: model files are ready, but no uv cache or source tree is mounted.
    start = [
        "run", "--detach", "--pull", "never", "--network", "none", "--name", container,
        "-v", f"{cache}:/cache", "-v", f"{data}:/data", *environment,
        "-e", "FASTEMBED_LOCAL_FILES_ONLY=true",
        "-e", "UV_CACHE_DIR=/tmp/empty-uv-cache",
        "-e", "UV_HTTP_TIMEOUT=1", "-e", "UV_HTTP_RETRIES=0",
        image_id,
    ]

    # Act: use the image's actual default command, without a UV_NO_SYNC override.
    docker(*start)
    wait_for_health(container, expected_version)
    installed_version = docker(
        "exec", container, "/app/.venv/bin/python", "-c",
        "from importlib.metadata import version; print(version('forgetful-ai'))",
    ).stdout.strip()
    assert installed_version == expected_version
    memory_ids = set()
    for title, content in [
        ("Team code word", "The team's code word is amber."),
        ("Team meeting notes", "The team archives amber meeting notes on Fridays."),
    ]:
        created = request(container, "/api/v1/memories", {
            "title": title,
            "content": content,
            "context": "Information for the offline container regression test",
            "keywords": ["team", "amber"],
            "tags": ["offline-test"],
            "importance": 7,
        })
        memory_ids.add(created["id"])

    # Assert: inference, reranking, token counting and persisted data survive both.
    assert_search_works(container, memory_ids)
    docker("restart", "--time", "10", container)
    wait_for_health(container, expected_version)
    assert_search_works(container, memory_ids)
    docker("rm", "-f", container)
    docker(*start)
    wait_for_health(container, expected_version)
    assert_search_works(container, memory_ids)
