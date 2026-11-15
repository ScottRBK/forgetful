"""Memory list API contracts exercised unchanged against SQLite and PostgreSQL."""

from datetime import UTC, datetime, timedelta, timezone

from app.config.settings import settings


async def create_project(http_client, name: str, description: str = "List contract project") -> int:
    response = await http_client.post("/api/v1/projects", json={
        "name": name,
        "description": description,
        "project_type": "development",
    })
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def create_memory(
    http_client,
    title: str,
    *,
    content: str | None = None,
    context: str = "memory list contract",
    importance: int = 7,
    project_ids: list[int] | None = None,
    tags: list[str] | None = None,
) -> dict:
    payload = {
        "title": title,
        "content": content if content is not None else f"{title} content",
        "context": context,
        "keywords": ["list-contract"],
        "tags": tags if tags is not None else ["list-contract"],
        "importance": importance,
    }
    if project_ids is not None:
        payload["project_ids"] = project_ids
    response = await http_client.post("/api/v1/memories", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def parse_timestamp_utc(value: str) -> datetime:
    """Parse a response timestamp, treating SQLite's naive value as UTC."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def response_updated_at_utc(memory: dict) -> datetime:
    """Parse a memory response's updated_at timestamp as UTC."""
    return parse_timestamp_utc(memory["updated_at"])


async def list_memories(http_client, **params) -> dict:
    """Snapshot memories through the list endpoint; emits no read event."""
    query = {"limit": 100, **params}
    response = await http_client.get("/api/v1/memories", params=query)
    assert response.status_code == 200, response.text
    return response.json()


async def list_memory(http_client, memory_id: int) -> dict:
    """Find one memory in a list snapshot, without a single-record read."""
    data = await list_memories(http_client)
    found = [memory for memory in data["memories"] if memory["id"] == memory_id]
    assert len(found) == 1, found
    return found[0]


def iso_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def iso_offset(value: datetime, hours: int, minutes: int = 0) -> str:
    return value.astimezone(timezone(timedelta(hours=hours, minutes=minutes))).isoformat()


class TestMemoryListContract:
    async def test_title_sort_is_binary_codepoint_order(self, http_client):
        titles = ["Zebra", "_x", "apple", "Éclair", "éclair"]
        for title in titles:
            await create_memory(http_client, title)

        ascending = await http_client.get(
            "/api/v1/memories",
            params={"sort_by": "title", "sort_order": "asc", "limit": 100},
        )
        assert ascending.status_code == 200, ascending.text
        assert [memory["title"] for memory in ascending.json()["memories"]] == titles

        descending = await http_client.get(
            "/api/v1/memories",
            params={"sort_by": "title", "sort_order": "desc", "limit": 100},
        )
        assert descending.status_code == 200, descending.text
        assert [memory["title"] for memory in descending.json()["memories"]] == list(
            reversed(titles),
        )

    async def test_project_name_sort_uses_least_owned_name_and_nulls_last(self, http_client):
        project_b = await create_project(http_client, "b")
        project_a = await create_project(http_client, "a")
        project_c = await create_project(http_client, "c")

        b_and_c = await create_memory(
            http_client, "b and c", project_ids=[project_b, project_c],
        )
        both = await create_memory(http_client, "Both projects", project_ids=[project_b, project_a])
        only_a = await create_memory(http_client, "Only a", project_ids=[project_a])
        only_b = await create_memory(http_client, "Only b", project_ids=[project_b])
        no_project = await create_memory(http_client, "No project")

        ascending = await http_client.get(
            "/api/v1/memories",
            params={"sort_by": "project_name", "sort_order": "asc", "limit": 100},
        )
        assert ascending.status_code == 200, ascending.text
        data = ascending.json()
        actual = [memory["id"] for memory in data["memories"]]
        expected = [both["id"], only_a["id"], b_and_c["id"], only_b["id"], no_project["id"]]
        assert actual == expected, actual
        assert data["total"] == 5

        descending = await http_client.get(
            "/api/v1/memories",
            params={"sort_by": "project_name", "sort_order": "desc", "limit": 100},
        )
        assert descending.status_code == 200, descending.text
        data = descending.json()
        actual = [memory["id"] for memory in data["memories"]]
        expected = [only_b["id"], b_and_c["id"], only_a["id"], both["id"], no_project["id"]]
        assert actual == expected, actual
        assert data["total"] == 5

        filtered = await http_client.get(
            "/api/v1/memories",
            params={
                "project_id": project_b,
                "sort_by": "project_name",
                "sort_order": "asc",
                "limit": 100,
            },
        )
        assert filtered.status_code == 200, filtered.text
        data = filtered.json()
        actual = [memory["id"] for memory in data["memories"]]
        expected = [both["id"], b_and_c["id"], only_b["id"]]
        assert actual == expected, actual
        assert data["total"] == 3

    async def test_project_name_sort_is_binary_codepoint_order_with_ties(self, http_client):
        project_zebra = await create_project(http_client, "Zebra")
        project_underscore = await create_project(http_client, "_x")
        project_apple = await create_project(http_client, "apple")
        project_upper_accent = await create_project(http_client, "Éclair")
        project_lower_accent = await create_project(http_client, "éclair")

        zebra_only = await create_memory(
            http_client, "Zebra only", project_ids=[project_zebra],
        )
        multi = await create_memory(
            http_client,
            "Zebra and apple",
            project_ids=[project_zebra, project_apple],
        )
        underscore_only = await create_memory(
            http_client, "_x only", project_ids=[project_underscore],
        )
        apple_a = await create_memory(
            http_client, "Apple A", project_ids=[project_apple],
        )
        apple_b = await create_memory(
            http_client, "Apple B", project_ids=[project_apple, project_lower_accent],
        )
        upper_accent = await create_memory(
            http_client, "Upper Éclair", project_ids=[project_upper_accent],
        )
        lower_accent = await create_memory(
            http_client, "Lower éclair", project_ids=[project_lower_accent],
        )

        expected_ascending = [
            zebra_only["id"], multi["id"], underscore_only["id"],
            apple_a["id"], apple_b["id"], upper_accent["id"], lower_accent["id"],
        ]
        expected_descending = [
            lower_accent["id"], upper_accent["id"], apple_b["id"], apple_a["id"],
            underscore_only["id"], multi["id"], zebra_only["id"],
        ]

        for sort_order, expected in [
            ("asc", expected_ascending),
            ("desc", expected_descending),
        ]:
            collected = []
            for offset in (0, 3, 6):
                response = await http_client.get(
                    "/api/v1/memories",
                    params={
                        "sort_by": "project_name",
                        "sort_order": sort_order,
                        "limit": 3,
                        "offset": offset,
                    },
                )
                assert response.status_code == 200, response.text
                page = response.json()
                assert page["total"] == 7, (sort_order, offset)
                collected.extend(memory["id"] for memory in page["memories"])
            assert collected == expected, (sort_order, collected)
            assert len(collected) == len(set(collected))

    async def test_q_matches_title_content_and_context_with_ascii_fold(self, http_client):
        title_hit = await create_memory(
            http_client,
            "Needle in title",
            content="plain",
            context="plain",
        )
        content_hit = await create_memory(
            http_client,
            "Plain title",
            content="NEEDLE in content",
            context="plain",
        )
        context_hit = await create_memory(
            http_client,
            "Plain title two",
            content="plain",
            context="needle in context",
        )
        await create_memory(http_client, "Nothing", content="plain", context="plain")

        response = await http_client.get("/api/v1/memories", params={"q": "nEeDlE"})
        assert response.status_code == 200, response.text
        data = response.json()
        actual = [memory["id"] for memory in data["memories"]]
        expected = [context_hit["id"], content_hit["id"], title_hit["id"]]
        assert actual == expected, actual
        assert data["total"] == 3

    async def test_q_wildcards_are_literal_and_unicode_is_not_folded(self, http_client):
        percent = await create_memory(http_client, "Percent 100%")
        underscore = await create_memory(http_client, "Under_score")
        backslash = await create_memory(http_client, "Back\\slash")
        upper_accent = await create_memory(http_client, "CafÉ")
        lower_accent = await create_memory(http_client, "Café")

        for query, expected_id in [
            ("%", percent["id"]),
            ("_", underscore["id"]),
            ("\\", backslash["id"]),
        ]:
            response = await http_client.get("/api/v1/memories", params={"q": query})
            assert response.status_code == 200, response.text
            assert [memory["id"] for memory in response.json()["memories"]] == [expected_id]
            assert response.json()["total"] == 1

        for query, expected_id in [
            ("é", lower_accent["id"]),
            ("É", upper_accent["id"]),
            ("CAFÉ", upper_accent["id"]),
        ]:
            response = await http_client.get("/api/v1/memories", params={"q": query})
            assert response.status_code == 200, response.text
            assert [memory["id"] for memory in response.json()["memories"]] == [expected_id]

        response = await http_client.get("/api/v1/memories", params={"q": "CAFE"})
        assert response.status_code == 200, response.text
        assert response.json()["memories"] == []
        assert response.json()["total"] == 0

    async def test_q_empty_or_whitespace_is_not_trimmed(self, http_client):
        with_space = await create_memory(http_client, "Has spaces", content="a b", context="a b")
        without_space = await create_memory(
            http_client, "NoSpaces", content="NoSpaces", context="NoSpaces",
        )

        unfiltered = await http_client.get("/api/v1/memories", params={"limit": 100})
        empty_q = await http_client.get("/api/v1/memories", params={"q": "", "limit": 100})
        assert unfiltered.status_code == 200
        assert empty_q.status_code == 200
        assert unfiltered.json()["total"] == empty_q.json()["total"]
        assert [m["id"] for m in unfiltered.json()["memories"]] == [
            m["id"] for m in empty_q.json()["memories"]
        ]

        spaces_only = await http_client.get("/api/v1/memories", params={"q": " ", "limit": 100})
        assert spaces_only.status_code == 200, spaces_only.text
        data = spaces_only.json()
        assert [memory["id"] for memory in data["memories"]] == [with_space["id"]]
        assert data["total"] == 1
        assert without_space["id"] not in [memory["id"] for memory in data["memories"]]

    async def test_q_rejects_nul(self, http_client):
        response = await http_client.get("/api/v1/memories", params={"q": "a\x00b"})
        assert response.status_code == 400

    async def test_importance_max_supports_exact_and_range(self, http_client):
        low = await create_memory(http_client, "Low", importance=3)
        middle = await create_memory(http_client, "Middle", importance=5)
        high = await create_memory(http_client, "High", importance=7)
        top = await create_memory(http_client, "Top", importance=9)

        exact = await http_client.get(
            "/api/v1/memories",
            params={"importance_min": 5, "importance_max": 5, "limit": 100},
        )
        assert exact.status_code == 200, exact.text
        data = exact.json()
        assert [memory["id"] for memory in data["memories"]] == [middle["id"]]
        assert data["total"] == 1

        ranged = await http_client.get(
            "/api/v1/memories",
            params={"importance_min": 5, "importance_max": 7, "limit": 100},
        )
        assert ranged.status_code == 200, ranged.text
        data = ranged.json()
        actual = [memory["id"] for memory in data["memories"]]
        assert actual == [high["id"], middle["id"]], actual
        assert data["total"] == 2
        assert low["id"] not in actual
        assert top["id"] not in actual

    async def test_importance_range_errors(self, http_client):
        await create_memory(http_client, "Range errors")
        cases = {
            "inverted": {"importance_min": 8, "importance_max": 5},
            "min zero": {"importance_min": 0},
            "min eleven": {"importance_min": 11},
            "max zero": {"importance_max": 0},
            "max eleven": {"importance_max": 11},
            "max not integer": {"importance_max": "high"},
        }
        for label, params in cases.items():
            response = await http_client.get("/api/v1/memories", params=params)
            assert response.status_code == 400, f"{label}: {response.text}"

    async def test_updated_range_endpoints_are_inclusive_and_offset_equivalent(self, http_client):
        memory = await create_memory(http_client, "Updated bounds")
        later = await create_memory(http_client, "Updated later")
        updated = response_updated_at_utc(await list_memory(http_client, memory["id"]))

        exact = await http_client.get(
            "/api/v1/memories",
            params={
                "updated_from": iso_utc(updated),
                "updated_to": iso_utc(updated),
                "limit": 100,
            },
        )
        assert exact.status_code == 200, exact.text
        data = exact.json()
        assert [item["id"] for item in data["memories"]] == [memory["id"]]
        assert data["total"] == 1
        assert later["id"] not in [item["id"] for item in data["memories"]]

        offset = await http_client.get(
            "/api/v1/memories",
            params={
                "updated_from": iso_offset(updated, 5),
                "updated_to": iso_offset(updated, 5),
                "limit": 100,
            },
        )
        assert offset.status_code == 200, offset.text
        data = offset.json()
        assert [item["id"] for item in data["memories"]] == [memory["id"]]
        assert data["total"] == 1

    async def test_updated_range_rejects_invalid_values(self, http_client):
        await create_memory(http_client, "Updated errors")
        cases = {
            "garbage": {"updated_from": "not-a-date"},
            "date only": {"updated_from": "2026-01-01"},
            "naive": {"updated_from": "2026-01-01T00:00:00"},
            "bad offset": {"updated_from": "2026-01-01T00:00:00+25:00"},
            "reversed": {
                "updated_from": "2026-01-02T00:00:00Z",
                "updated_to": "2026-01-01T00:00:00Z",
            },
            "naive upper": {"updated_to": "2026-01-01T00:00:00"},
            "utc underflow": {"updated_from": "0001-01-01T00:00:00+01:00"},
            "utc overflow": {"updated_to": "9999-12-31T23:59:59-01:00"},
        }
        for label, params in cases.items():
            response = await http_client.get("/api/v1/memories", params=params)
            assert response.status_code == 400, f"{label}: {response.text}"

        raw_plus = await http_client.get(
            "/api/v1/memories?updated_from=2026-01-01T00:00:00+01:00",
        )
        assert raw_plus.status_code == 400, raw_plus.text

    async def test_combined_filters_apply_before_count_and_paging(self, http_client):
        project_a = await create_project(http_client, "combined-a")
        project_b = await create_project(http_client, "combined-b")

        stale = await create_memory(
            http_client, "Alpha stale", importance=8, project_ids=[project_a],
        )
        match_a = await create_memory(
            http_client, "Alpha match A", importance=8, project_ids=[project_a],
        )
        match_b = await create_memory(
            http_client, "Alpha match B", importance=8, project_ids=[project_a],
        )
        await create_memory(http_client, "Beta text", importance=8, project_ids=[project_a])
        await create_memory(
            http_client, "Alpha other project", importance=8, project_ids=[project_b],
        )
        await create_memory(http_client, "Alpha low", importance=5, project_ids=[project_a])
        await create_memory(http_client, "Alpha high", importance=10, project_ids=[project_a])
        await create_memory(
            http_client,
            "Alpha untagged",
            importance=8,
            project_ids=[project_a],
            tags=["other"],
        )
        match_c = await create_memory(
            http_client, "Alpha match C", importance=8, project_ids=[project_a],
        )
        future = await create_memory(
            http_client, "Alpha future", importance=8, project_ids=[project_a],
        )

        snapshot = await list_memories(http_client)
        snapshot_by_id = {memory["id"]: memory for memory in snapshot["memories"]}
        matches = [match_a, match_b, match_c]
        match_times = [
            response_updated_at_utc(snapshot_by_id[memory["id"]]) for memory in matches
        ]
        base = {
            "q": "alpha",
            "project_id": project_a,
            "importance_min": 7,
            "importance_max": 9,
            "updated_from": iso_utc(min(match_times)),
            "updated_to": iso_utc(max(match_times)),
            "tags": "list-contract",
            "sort_by": "title",
            "sort_order": "asc",
        }

        pages = []
        for offset in (0, 2, 4):
            response = await http_client.get(
                "/api/v1/memories",
                params={**base, "limit": 2, "offset": offset},
            )
            assert response.status_code == 200, response.text
            data = response.json()
            assert data["total"] == 3, offset
            pages.append([memory["id"] for memory in data["memories"]])

        assert pages[0] == [match_a["id"], match_b["id"]]
        assert pages[1] == [match_c["id"]]
        assert pages[2] == []
        assert [*pages[0], *pages[1], *pages[2]] == [m["id"] for m in matches]

        without_lower = {**base, "limit": 100}
        without_lower.pop("updated_from")
        response = await http_client.get("/api/v1/memories", params=without_lower)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["total"] == 4
        assert [memory["id"] for memory in data["memories"]] == [
            *[m["id"] for m in matches], stale["id"],
        ]

        without_upper = {**base, "limit": 100}
        without_upper.pop("updated_to")
        response = await http_client.get("/api/v1/memories", params=without_upper)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["total"] == 4
        assert [memory["id"] for memory in data["memories"]] == [
            future["id"], *[m["id"] for m in matches],
        ]

    async def test_title_and_project_paging_concatenates_without_duplicates(self, http_client):
        project_delta = await create_project(http_client, "delta")
        project_alpha = await create_project(http_client, "alpha")
        project_gamma = await create_project(http_client, "gamma")
        project_beta = await create_project(http_client, "beta")

        echo = await create_memory(http_client, "Echo", project_ids=[project_delta])
        alpha = await create_memory(http_client, "Alpha", project_ids=[project_alpha])
        charlie = await create_memory(http_client, "Charlie")
        bravo = await create_memory(http_client, "Bravo", project_ids=[project_gamma])
        delta = await create_memory(http_client, "Delta", project_ids=[project_beta])

        cases = {
            ("title", "asc"): [alpha, bravo, charlie, delta, echo],
            ("title", "desc"): [echo, delta, charlie, bravo, alpha],
            ("project_name", "asc"): [alpha, delta, echo, bravo, charlie],
            ("project_name", "desc"): [bravo, echo, delta, alpha, charlie],
        }
        for (sort_by, sort_order), ordered in cases.items():
            collected = []
            for offset in (0, 2, 4):
                response = await http_client.get(
                    "/api/v1/memories",
                    params={
                        "sort_by": sort_by,
                        "sort_order": sort_order,
                        "limit": 2,
                        "offset": offset,
                    },
                )
                assert response.status_code == 200, response.text
                page = response.json()
                assert page["total"] == 5, (sort_by, sort_order, offset)
                assert page["limit"] == 2
                assert page["offset"] == offset
                collected.extend(memory["id"] for memory in page["memories"])
            expected = [memory["id"] for memory in ordered]
            assert collected == expected, (sort_by, sort_order, collected)
            assert len(collected) == len(set(collected))

    async def test_title_ties_order_by_id_in_sort_direction(self, http_client):
        first = await create_memory(http_client, "Same title")
        second = await create_memory(http_client, "Same title")
        third = await create_memory(http_client, "Same title")

        ascending = await http_client.get(
            "/api/v1/memories",
            params={"sort_by": "title", "sort_order": "asc", "limit": 100},
        )
        assert ascending.status_code == 200, ascending.text
        assert [m["id"] for m in ascending.json()["memories"]] == [
            first["id"], second["id"], third["id"],
        ]

        descending = await http_client.get(
            "/api/v1/memories",
            params={"sort_by": "title", "sort_order": "desc", "limit": 100},
        )
        assert descending.status_code == 200, descending.text
        assert [m["id"] for m in descending.json()["memories"]] == [
            third["id"], second["id"], first["id"],
        ]

    async def test_owner_isolation_obsolete_and_defaults_unchanged(self, http_client, monkeypatch):
        first = await create_memory(http_client, "First visible")
        second = await create_memory(http_client, "Second visible")
        obsolete = await create_memory(http_client, "Obsolete")
        deleted = await http_client.delete(f"/api/v1/memories/{obsolete['id']}")
        assert deleted.status_code == 200, deleted.text

        default = await http_client.get("/api/v1/memories")
        assert default.status_code == 200
        data = default.json()
        assert set(data) == {"memories", "total", "limit", "offset"}
        assert data["limit"] == 20
        assert data["offset"] == 0
        assert data["total"] == 2
        assert [memory["id"] for memory in data["memories"]] == [second["id"], first["id"]]

        with_obsolete = await http_client.get(
            "/api/v1/memories", params={"include_obsolete": "true", "limit": 100},
        )
        assert with_obsolete.status_code == 200
        assert with_obsolete.json()["total"] == 3

        with monkeypatch.context() as other_user:
            other_user.setattr(settings, "DEFAULT_USER_ID", "memory-list-other-user")
            other_user.setattr(settings, "DEFAULT_USER_EMAIL", "list-other@example.test")
            other = await create_memory(http_client, "Other user memory")
            other_list = await http_client.get("/api/v1/memories")
            assert other_list.status_code == 200
            assert [memory["id"] for memory in other_list.json()["memories"]] == [other["id"]]
            assert other_list.json()["total"] == 1

        restored = await http_client.get("/api/v1/memories")
        assert restored.status_code == 200
        assert restored.json()["total"] == 2
        assert other["id"] not in [memory["id"] for memory in restored.json()["memories"]]

    async def test_owner_isolation_with_new_filters_and_project_sort(
        self, http_client, monkeypatch,
    ):
        owner_project = await create_project(http_client, "zzz-owner")
        owner_a = await create_memory(
            http_client, "Owner alpha A", importance=8, project_ids=[owner_project],
        )
        owner_b = await create_memory(
            http_client, "Owner alpha B", importance=8, project_ids=[owner_project],
        )
        owner_low = await create_memory(
            http_client, "Owner alpha low", importance=5, project_ids=[owner_project],
        )

        with monkeypatch.context() as other_user:
            other_user.setattr(settings, "DEFAULT_USER_ID", "memory-list-filter-other")
            other_user.setattr(settings, "DEFAULT_USER_EMAIL", "list-filter-other@example.test")
            other_project = await create_project(http_client, "aaa-other")
            other_a = await create_memory(
                http_client, "Other alpha A", importance=8, project_ids=[other_project],
            )
            other_b = await create_memory(
                http_client, "Other alpha B", importance=8, project_ids=[other_project],
            )
            other_filtered = await http_client.get(
                "/api/v1/memories",
                params={
                    "q": "alpha",
                    "importance_min": 8,
                    "importance_max": 8,
                    "limit": 100,
                },
            )
            assert other_filtered.status_code == 200, other_filtered.text
            assert other_filtered.json()["total"] == 2
            assert [memory["id"] for memory in other_filtered.json()["memories"]] == [
                other_b["id"], other_a["id"],
            ]

        filtered = await http_client.get(
            "/api/v1/memories",
            params={
                "q": "alpha",
                "importance_min": 8,
                "importance_max": 8,
                "limit": 100,
            },
        )
        assert filtered.status_code == 200, filtered.text
        data = filtered.json()
        assert data["total"] == 2
        filtered_ids = [memory["id"] for memory in data["memories"]]
        assert filtered_ids == [owner_b["id"], owner_a["id"]]
        assert other_a["id"] not in filtered_ids
        assert other_b["id"] not in filtered_ids
        assert owner_low["id"] not in filtered_ids

        sorted_by_project = await http_client.get(
            "/api/v1/memories",
            params={"sort_by": "project_name", "sort_order": "asc", "limit": 100},
        )
        assert sorted_by_project.status_code == 200, sorted_by_project.text
        data = sorted_by_project.json()
        assert data["total"] == 3
        sorted_ids = [memory["id"] for memory in data["memories"]]
        assert sorted_ids == [owner_a["id"], owner_b["id"], owner_low["id"]]
        assert other_a["id"] not in sorted_ids
        assert other_b["id"] not in sorted_ids

    async def test_default_and_importance_sorts_unchanged(self, http_client):
        low = await create_memory(http_client, "Low importance", importance=5)
        high_first = await create_memory(http_client, "High first", importance=9)
        high_second = await create_memory(http_client, "High second", importance=9)

        default = await http_client.get("/api/v1/memories", params={"limit": 100})
        assert default.status_code == 200
        assert [m["id"] for m in default.json()["memories"]] == [
            high_second["id"], high_first["id"], low["id"],
        ]

        importance = await http_client.get(
            "/api/v1/memories", params={"sort_by": "importance", "limit": 100},
        )
        assert importance.status_code == 200
        assert [m["id"] for m in importance.json()["memories"]] == [
            high_second["id"], high_first["id"], low["id"],
        ]

        ordered_asc = await http_client.get(
            "/api/v1/memories",
            params={"sort_by": "importance", "sort_order": "asc", "limit": 100},
        )
        assert ordered_asc.status_code == 200
        assert [m["id"] for m in ordered_asc.json()["memories"]] == [
            low["id"], high_second["id"], high_first["id"],
        ]
