"""Memory read/search tracking contracts shared by SQLite and PostgreSQL."""

from tests.memory_list_cases import (
    create_memory,
    iso_utc,
    list_memories,
    list_memory,
    parse_timestamp_utc,
    response_updated_at_utc,
)


def content_fields(memory: dict) -> dict:
    return {field: memory[field] for field in ("title", "content", "context")}


class TestMemoryUsageTracking:
    async def test_repeated_get_preserves_updated_at_and_content(
        self, http_client, wait_for_events,
    ):
        created = await create_memory(
            http_client,
            "Tracking repeated get",
            content="Repeated read content must stay unchanged",
            context="Repeated read context",
        )
        baseline = await list_memory(http_client, created["id"])

        first_read = await http_client.get(f"/api/v1/memories/{created['id']}")
        assert first_read.status_code == 200, first_read.text
        await wait_for_events()
        after_first = await list_memory(http_client, created["id"])

        second_read = await http_client.get(f"/api/v1/memories/{created['id']}")
        assert second_read.status_code == 200, second_read.text
        await wait_for_events()
        after_second = await list_memory(http_client, created["id"])

        assert after_first["access_count"] == baseline["access_count"] + 1
        assert after_second["access_count"] == baseline["access_count"] + 2
        assert after_first["last_accessed_at"] is not None
        assert (
            parse_timestamp_utc(after_second["last_accessed_at"])
            > parse_timestamp_utc(after_first["last_accessed_at"])
        )
        assert after_first["updated_at"] == baseline["updated_at"]
        assert after_second["updated_at"] == baseline["updated_at"]
        assert content_fields(after_first) == content_fields(baseline)
        assert content_fields(after_second) == content_fields(baseline)

    async def test_read_does_not_change_updated_sort_or_date_membership(
        self, http_client, wait_for_events,
    ):
        await create_memory(http_client, "Tracking sort oldest")
        await create_memory(http_client, "Tracking sort middle")
        await create_memory(http_client, "Tracking sort newest")

        baseline = await list_memories(
            http_client, sort_by="updated_at", sort_order="asc",
        )
        assert len(baseline["memories"]) == 3
        baseline_ids = [memory["id"] for memory in baseline["memories"]]
        baseline_updates = [memory["updated_at"] for memory in baseline["memories"]]

        older = baseline["memories"][0]
        bound = iso_utc(response_updated_at_utc(older))
        before_bound = await list_memories(
            http_client, updated_from=bound, updated_to=bound,
        )
        before_member_ids = [memory["id"] for memory in before_bound["memories"]]
        assert older["id"] in before_member_ids

        read_response = await http_client.get(f"/api/v1/memories/{older['id']}")
        assert read_response.status_code == 200, read_response.text
        await wait_for_events()

        after_sort = await list_memories(
            http_client, sort_by="updated_at", sort_order="asc",
        )
        after_bound = await list_memories(
            http_client, updated_from=bound, updated_to=bound,
        )
        assert [memory["id"] for memory in after_sort["memories"]] == baseline_ids
        assert [memory["updated_at"] for memory in after_sort["memories"]] == baseline_updates
        assert [memory["id"] for memory in after_bound["memories"]] == before_member_ids
        assert after_bound["total"] == before_bound["total"]

    async def test_query_preserves_updated_at_for_primary_and_linked(
        self, http_client, wait_for_events,
    ):
        primary = await create_memory(
            http_client,
            "Tracking query primary",
            content="Unique primary content for query access tracking",
            context="Query primary context",
        )
        linked = await create_memory(
            http_client,
            "Tracking query linked",
            content="Linked content that must not become the primary result",
            context="Query linked context",
        )
        link_response = await http_client.post(
            f"/api/v1/memories/{primary['id']}/links",
            json={"related_ids": [linked["id"]]},
        )
        assert link_response.status_code == 200, link_response.text

        primary_before = await list_memory(http_client, primary["id"])
        linked_before = await list_memory(http_client, linked["id"])

        search_response = await http_client.post("/api/v1/memories/search", json={
            "query": "Unique primary content for query access tracking",
            "query_context": "Tracking query access regression",
            "k": 1,
            "include_links": True,
            "max_links_per_primary": 5,
        })
        assert search_response.status_code == 200, search_response.text
        result = search_response.json()
        assert len(result["primary_memories"]) == 1
        assert result["primary_memories"][0]["id"] == primary["id"]
        linked_ids = [item["memory"]["id"] for item in result["linked_memories"]]
        assert linked["id"] in linked_ids

        await wait_for_events()
        primary_after = await list_memory(http_client, primary["id"])
        linked_after = await list_memory(http_client, linked["id"])

        for before, after in ((primary_before, primary_after), (linked_before, linked_after)):
            assert after["access_count"] == before["access_count"] + 1
            assert after["last_accessed_at"] is not None
            assert after["updated_at"] == before["updated_at"]
            assert content_fields(after) == content_fields(before)

    async def test_real_edit_still_advances_updated_at(self, http_client, wait_for_events):
        created = await create_memory(http_client, "Tracking edit baseline")
        baseline = await list_memory(http_client, created["id"])

        read_response = await http_client.get(f"/api/v1/memories/{created['id']}")
        assert read_response.status_code == 200, read_response.text
        await wait_for_events()

        edit_response = await http_client.put(
            f"/api/v1/memories/{created['id']}",
            json={"title": "Tracking edit applied"},
        )
        assert edit_response.status_code == 200, edit_response.text
        await wait_for_events()

        after = await list_memory(http_client, created["id"])
        assert after["access_count"] == baseline["access_count"] + 1
        assert response_updated_at_utc(after) > response_updated_at_utc(baseline)
