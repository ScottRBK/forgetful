"""E2E test for the harness's throwaway Forgetful server (test_harness/server.py).

Boots the real `forgetful serve` console script as an OS subprocess (the harness's agent
is a separate process, so in-process shortcuts prove nothing here), file-backed SQLite,
all feature flags on, no auth. Readiness is /health -> 200; seeding goes through the CLI's
own RemoteExecutor against the meta-tool path.
"""
import httpx
import pytest

from test_harness.config import HarnessConfig
from test_harness.server import ThrowawayForgetful


@pytest.mark.asyncio
async def test_throwaway_server_boots_seeds_skills_and_tears_down(tmp_path):
    # Arrange
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    skills_dir = HarnessConfig().skills_dir
    reference_names = ["first-encode.md", "refresh.md"]
    expected_references = {
        f"forgetful-encode-repo/references/{name}": (
            skills_dir / "forgetful-encode-repo" / "references" / name
        ).read_text(encoding="utf-8").strip()
        for name in reference_names
    }

    server = ThrowawayForgetful(run_dir=run_dir)

    # Act
    server.start()
    try:
        health = httpx.get(f"{server.url}/health", timeout=5)
        seeded = await server.seed_skills(
            skills_dir, ["forgetful-recall", "forgetful-encode-repo"],
        )
        found = await server.execute(
            "search_skills", {"query": "recall knowledge from forgetful memory"},
        )
        links = {
            skill["name"]: await server.execute("get_skill_links", {"skill_id": skill["id"]})
            for skill in seeded
        }
        references = [
            await server.execute("get_document", {"document_id": document_id})
            for document_id in links["forgetful-encode-repo"]["document_ids"]
        ]
        actual_references = {document["title"]: document["content"] for document in references}
    finally:
        server.stop()

    # Assert
    assert health.status_code == 200
    assert [skill["name"] for skill in seeded] == ["forgetful-recall", "forgetful-encode-repo"]
    assert any(skill["name"] == "forgetful-recall" for skill in found["skills"])
    assert links["forgetful-recall"]["document_ids"] == []
    assert len(references) == len(expected_references)
    assert actual_references == expected_references
    assert server.process.poll() is not None, "server process must be gone after stop()"
    assert (run_dir / "forgetful.db").exists()
    assert (run_dir / "server.log").read_text()
