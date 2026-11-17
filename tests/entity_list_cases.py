"""Entity list API contracts exercised unchanged against SQLite and PostgreSQL."""


async def create_entity(
    http_client,
    name: str,
    *,
    entity_type: str = "Individual",
    aka: list[str] | None = None,
    tags: list[str] | None = None,
) -> dict:
    payload: dict = {
        "name": name,
        "entity_type": entity_type,
    }
    if aka is not None:
        payload["aka"] = aka
    if tags is not None:
        payload["tags"] = tags
    response = await http_client.post("/api/v1/entities", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


async def list_entities(http_client, **params) -> dict:
    """Snapshot entities through the list endpoint."""
    query = {"limit": 100, **params}
    response = await http_client.get("/api/v1/entities", params=query)
    assert response.status_code == 200, response.text
    return response.json()


def entity_ids(data: dict) -> list[int]:
    return [entity["id"] for entity in data["entities"]]


class TestEntityListContract:
    """Shared contract for GET /api/v1/entities?q= (Phase 1)."""

    async def test_q_matches_name_with_ascii_fold(self, http_client):
        hit = await create_entity(http_client, "ACME Corp")
        await create_entity(http_client, "Other LLC")

        response = await http_client.get("/api/v1/entities", params={"q": "acme"})
        assert response.status_code == 200, response.text
        data = response.json()
        assert entity_ids(data) == [hit["id"]]
        assert data["total"] == 1

    async def test_q_matches_one_aka_not_across_elements(self, http_client):
        aka_hit = await create_entity(
            http_client,
            "Split Corp",
            aka=["ab", "cd"],
        )
        await create_entity(http_client, "Plain Corp")

        response = await http_client.get("/api/v1/entities", params={"q": "bc"})
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["entities"] == []
        assert data["total"] == 0

        response_alias = await http_client.get("/api/v1/entities", params={"q": "ab"})
        assert response_alias.status_code == 200, response_alias.text
        assert entity_ids(response_alias.json()) == [aka_hit["id"]]

    async def test_q_wildcards_are_literal(self, http_client):
        percent = await create_entity(http_client, "50% off")
        await create_entity(http_client, "axb")

        response_percent = await http_client.get("/api/v1/entities", params={"q": "50%"})
        assert response_percent.status_code == 200, response_percent.text
        assert entity_ids(response_percent.json()) == [percent["id"]]

        response_underscore = await http_client.get("/api/v1/entities", params={"q": "a_b"})
        assert response_underscore.status_code == 200, response_underscore.text
        assert response_underscore.json()["entities"] == []
        assert response_underscore.json()["total"] == 0

    async def test_q_combined_with_entity_type(self, http_client):
        org_hit = await create_entity(
            http_client,
            "Acme Org",
            entity_type="Organization",
        )
        await create_entity(
            http_client,
            "Acme Person",
            entity_type="Individual",
        )

        response = await http_client.get(
            "/api/v1/entities",
            params={"q": "acme", "entity_type": "Organization"},
        )
        assert response.status_code == 200, response.text
        assert entity_ids(response.json()) == [org_hit["id"]]
        assert response.json()["total"] == 1

    async def test_q_pagination_total_counts_filtered_set(self, http_client):
        for index in range(3):
            await create_entity(http_client, f"Pager Match {index}")

        page_one = await http_client.get(
            "/api/v1/entities",
            params={"q": "Pager Match", "limit": 2, "offset": 0},
        )
        assert page_one.status_code == 200, page_one.text
        data_one = page_one.json()
        assert len(data_one["entities"]) == 2
        assert data_one["total"] == 3

        page_two = await http_client.get(
            "/api/v1/entities",
            params={"q": "Pager Match", "limit": 2, "offset": 2},
        )
        assert page_two.status_code == 200, page_two.text
        data_two = page_two.json()
        assert len(data_two["entities"]) == 1
        assert data_two["total"] == 3
        assert {e["id"] for e in data_one["entities"]}.isdisjoint(
            {e["id"] for e in data_two["entities"]},
        )

    async def test_q_empty_string_same_as_absent(self, http_client):
        await create_entity(http_client, "Empty Q Corp")
        unfiltered = await list_entities(http_client)
        empty_q = await list_entities(http_client, q="")
        assert unfiltered["total"] == empty_q["total"]
        assert entity_ids(unfiltered) == entity_ids(empty_q)

    async def test_q_rejects_nul(self, http_client):
        response = await http_client.get("/api/v1/entities", params={"q": "a\x00b"})
        assert response.status_code == 400
        assert response.json() == {"error": "q must not contain NUL"}

    async def test_list_without_q_returns_unfiltered_page(self, http_client):
        first = await create_entity(http_client, "Unfiltered One")
        second = await create_entity(http_client, "Unfiltered Two")

        response = await http_client.get(
            "/api/v1/entities",
            params={"limit": 100},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        ids = entity_ids(data)
        assert first["id"] in ids
        assert second["id"] in ids
        assert data["total"] >= 2

    async def test_q_wildcards_backslash_and_unicode_not_folded(self, http_client):
        backslash = await create_entity(http_client, r"Back\slash")
        await create_entity(http_client, "ab")
        upper_accent = await create_entity(http_client, "É-corp")
        lower_accent = await create_entity(http_client, "é-corp")

        response_backslash = await http_client.get("/api/v1/entities", params={"q": "\\"})
        assert response_backslash.status_code == 200, response_backslash.text
        assert entity_ids(response_backslash.json()) == [backslash["id"]]

        response_e_lower = await http_client.get("/api/v1/entities", params={"q": "é"})
        assert response_e_lower.status_code == 200, response_e_lower.text
        assert entity_ids(response_e_lower.json()) == [lower_accent["id"]]

        response_e_upper = await http_client.get("/api/v1/entities", params={"q": "É"})
        assert response_e_upper.status_code == 200, response_e_upper.text
        assert entity_ids(response_e_upper.json()) == [upper_accent["id"]]

        aka_only = await create_entity(
            http_client,
            "Alias Host",
            aka=[r"a\b", "plain"],
        )
        response_aka_backslash = await http_client.get("/api/v1/entities", params={"q": "\\"})
        assert response_aka_backslash.status_code == 200, response_aka_backslash.text
        assert backslash["id"] in entity_ids(response_aka_backslash.json())
        assert aka_only["id"] in entity_ids(response_aka_backslash.json())

        aka_accent = await create_entity(
            http_client,
            "No match name",
            aka=["é-corp"],
        )
        response_aka_e = await http_client.get("/api/v1/entities", params={"q": "é"})
        assert response_aka_e.status_code == 200, response_aka_e.text
        assert aka_accent["id"] in entity_ids(response_aka_e.json())

    async def test_q_whitespace_is_not_trimmed(self, http_client):
        with_space = await create_entity(http_client, "Acme Corp")
        without_space = await create_entity(http_client, "AcmeCorp")

        spaces_only = await http_client.get(
            "/api/v1/entities",
            params={"q": " "},
        )
        assert spaces_only.status_code == 200, spaces_only.text
        data_spaces = spaces_only.json()
        assert entity_ids(data_spaces) == [with_space["id"]]
        assert without_space["id"] not in entity_ids(data_spaces)

        leading = await http_client.get(
            "/api/v1/entities",
            params={"q": " corp"},
        )
        assert leading.status_code == 200, leading.text
        assert entity_ids(leading.json()) == [with_space["id"]]

        aka_space = await create_entity(
            http_client,
            "AliasOnly",
            aka=["Acme Corp"],
        )
        aka_spaces_only = await http_client.get(
            "/api/v1/entities",
            params={"q": " "},
        )
        assert aka_spaces_only.status_code == 200, aka_spaces_only.text
        assert sorted(entity_ids(aka_spaces_only.json())) == sorted(
            [with_space["id"], aka_space["id"]],
        )

        aka_query = await http_client.get(
            "/api/v1/entities",
            params={"q": " corp"},
        )
        assert aka_query.status_code == 200, aka_query.text
        ids = entity_ids(aka_query.json())
        assert with_space["id"] in ids
        assert aka_space["id"] in ids
