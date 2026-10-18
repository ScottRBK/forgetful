"""E2E tests for entity search and project name matching on SQLite.

Uses in-memory SQLite for test isolation. Covers how ``search_entities`` and the
``list_projects`` name filter match text: literal LIKE wildcards, per-alias matching,
Unicode case folding, and the project ids reported in search results.
"""
import pytest


async def _create_entity(http_client, name, **extra):
    response = await http_client.post(
        "/api/v1/entities",
        json={"name": name, "entity_type": "System", "notes": "matching test", **extra},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _search(http_client, query):
    response = await http_client.post("/api/v1/entities/search", json={"query": query})
    assert response.status_code == 200, response.text
    return sorted(e["name"] for e in response.json()["entities"])


async def _create_project(mcp_client, name):
    result = await mcp_client.call_tool(
        "execute_forgetful_tool",
        {
            "tool_name": "create_project",
            "arguments": {
                "name": name,
                "description": "matching test",
                "project_type": "development",
            },
        },
    )
    return result.data["id"]


async def _project_names(mcp_client, name):
    result = await mcp_client.call_tool(
        "execute_forgetful_tool",
        {"tool_name": "list_projects", "arguments": {"name": name}},
    )
    return sorted(p["name"] for p in result.data["projects"])


class TestSearchEntitiesProjectIds:
    """search_entities must report the same project membership as list_entities."""

    @pytest.mark.asyncio
    async def test_search_results_include_project_ids(self, http_client, mcp_client):
        project_id = await _create_project(mcp_client, "membership-project")
        await _create_entity(http_client, "Alice", project_ids=[project_id])
        await _create_entity(http_client, "Alicia")

        listed = await http_client.get("/api/v1/entities")
        listed_ids = {e["name"]: e["project_ids"] for e in listed.json()["entities"]}
        assert listed_ids["Alice"] == [project_id]

        response = await http_client.post(
            "/api/v1/entities/search", json={"query": "Ali"},
        )
        assert response.status_code == 200
        searched = {e["name"]: e["project_ids"] for e in response.json()["entities"]}
        assert searched == {"Alice": [project_id], "Alicia": []}

    @pytest.mark.asyncio
    async def test_search_tool_reports_project_ids(self, http_client, mcp_client):
        first = await _create_project(mcp_client, "first-project")
        second = await _create_project(mcp_client, "second-project")
        await _create_entity(http_client, "Bob", project_ids=[first, second])

        result = await mcp_client.call_tool(
            "execute_forgetful_tool",
            {"tool_name": "search_entities", "arguments": {"query": "Bob"}},
        )
        entities = result.data["entities"]
        assert [e["name"] for e in entities] == ["Bob"]
        assert sorted(entities[0]["project_ids"]) == sorted([first, second])


class TestEntitySearchWildcards:
    """LIKE wildcards in the query are matched literally."""

    @pytest.mark.asyncio
    async def test_underscore_is_literal(self, http_client):
        for name in ("auth_service", "auth-service", "authXservice"):
            await _create_entity(http_client, name)
        assert await _search(http_client, "auth_service") == ["auth_service"]

    @pytest.mark.asyncio
    async def test_percent_is_literal(self, http_client):
        for name in ("alpha", "beta", "100% done"):
            await _create_entity(http_client, name)
        assert await _search(http_client, "%") == ["100% done"]

    @pytest.mark.asyncio
    async def test_backslash_is_literal(self, http_client):
        for name in ("back\\slash", "backslash", "back/slash"):
            await _create_entity(http_client, name)
        assert await _search(http_client, "back\\slash") == ["back\\slash"]

    @pytest.mark.asyncio
    async def test_wildcards_are_literal_in_aliases(self, http_client):
        await _create_entity(http_client, "Underscore", aka=["svc_main"])
        await _create_entity(http_client, "Dash", aka=["svc-main"])
        await _create_entity(http_client, "Percent", aka=["50% off"])
        await _create_entity(http_client, "Plain", aka=["fifty"])

        assert await _search(http_client, "svc_main") == ["Underscore"]
        assert await _search(http_client, "%") == ["Percent"]

    @pytest.mark.asyncio
    async def test_partial_and_case_insensitive_matches_still_work(self, http_client):
        await _create_entity(http_client, "Microsoft Corporation", aka=["MSFT"])
        await _create_entity(http_client, "Other")

        assert await _search(http_client, "microsoft") == ["Microsoft Corporation"]
        assert await _search(http_client, "msf") == ["Microsoft Corporation"]
        assert await _search(http_client, "ROSOFT CORP") == ["Microsoft Corporation"]


class TestEntitySearchAliases:
    """Each alias is matched on its own, not against the serialized alias list."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("query", ["[", "]", '"', ","])
    async def test_json_punctuation_does_not_match(self, http_client, query):
        await _create_entity(http_client, "Alpha", aka=["Bravo", "Delta"])
        await _create_entity(http_client, "Charlie")

        assert await _search(http_client, query) == []

    @pytest.mark.asyncio
    @pytest.mark.parametrize("query", ["Big Corp", 'Big","Corp', "BigCorp"])
    async def test_match_cannot_span_two_aliases(self, http_client, query):
        await _create_entity(http_client, "e", aka=["Big", "Corp"])

        assert await _search(http_client, query) == []

    @pytest.mark.asyncio
    async def test_each_alias_matches_individually(self, http_client):
        await _create_entity(http_client, "e", aka=["Big", "Corp"])
        await _create_entity(http_client, "empty", aka=[])

        assert await _search(http_client, "Big") == ["e"]
        assert await _search(http_client, "corp") == ["e"]

    @pytest.mark.asyncio
    async def test_name_and_alias_matches_are_combined(self, http_client):
        await _create_entity(http_client, "Zephyr", aka=["Quartz"])
        await _create_entity(http_client, "Quartz Labs")

        assert await _search(http_client, "quartz") == ["Quartz Labs", "Zephyr"]


class TestNonAsciiCaseInsensitivity:
    """Name and alias matching ignores case for non-ASCII letters too."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("query", ["émile", "ÉMILE", "Émile", "mile Z"])
    async def test_entity_name(self, http_client, query):
        await _create_entity(http_client, "Émile Zola")

        assert await _search(http_client, query) == ["Émile Zola"]

    @pytest.mark.asyncio
    async def test_entity_name_upper_query(self, http_client):
        await _create_entity(http_client, "Zoë")

        assert await _search(http_client, "ZOË") == ["Zoë"]

    @pytest.mark.asyncio
    async def test_entity_alias(self, http_client):
        await _create_entity(http_client, "Rhea", aka=["Ñandú"])

        assert await _search(http_client, "ñANDÚ") == ["Rhea"]

    @pytest.mark.asyncio
    async def test_non_matching_non_ascii_still_excluded(self, http_client):
        await _create_entity(http_client, "Émile Zola")

        assert await _search(http_client, "ömile") == []


class TestListProjectsNameFilter:
    """The list_projects name filter is a literal, case-insensitive substring match."""

    @pytest.mark.asyncio
    async def test_underscore_is_literal(self, mcp_client):
        for name in ("my_proj", "myXproj"):
            await _create_project(mcp_client, name)

        assert await _project_names(mcp_client, "my_proj") == ["my_proj"]

    @pytest.mark.asyncio
    async def test_percent_is_literal(self, mcp_client):
        for name in ("plain", "100% project"):
            await _create_project(mcp_client, name)

        assert await _project_names(mcp_client, "%") == ["100% project"]

    @pytest.mark.asyncio
    async def test_backslash_is_literal(self, mcp_client):
        for name in ("back\\slash", "backslash"):
            await _create_project(mcp_client, name)

        assert await _project_names(mcp_client, "back\\slash") == ["back\\slash"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("query", ["ünïcode", "ÜNÏCODE", "Ünïcode"])
    async def test_non_ascii_is_case_insensitive(self, mcp_client, query):
        await _create_project(mcp_client, "Ünïcode Project")

        assert await _project_names(mcp_client, query) == ["Ünïcode Project"]

    @pytest.mark.asyncio
    async def test_ascii_partial_match_still_works(self, mcp_client):
        for name in ("Forgetful", "forgetful-ui", "other"):
            await _create_project(mcp_client, name)

        assert await _project_names(mcp_client, "FORGET") == ["Forgetful", "forgetful-ui"]
