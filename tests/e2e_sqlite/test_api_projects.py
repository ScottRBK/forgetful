"""E2E tests for Project REST API endpoints.

Uses in-memory SQLite for test isolation.
Tests the /api/v1/projects endpoints.
"""
import pytest

from app.config.settings import settings


class TestProjectAPIList:
    """Test GET /api/v1/projects endpoint."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("query", [
        "github.com/ScottRBK/forgetful",
        " https://GITHUB.COM/ScottRBK/forgetful.git/ ",
        "git@github.com:ScottRBK/forgetful.git",
        "ssh://git@github.com/ScottRBK/forgetful.git",
    ])
    async def test_lookup_equivalent_repositories(self, http_client, monkeypatch, query):
        """Lookup finds every equivalent address and still respects the status filter."""
        repositories = [
            ("github.com/ScottRBK/forgetful", "active"),
            ("https://github.com/ScottRBK/forgetful.git", "active"),
            ("git@github.com:ScottRBK/forgetful.git", "active"),
            ("ssh://git@github.com/ScottRBK/forgetful.git", "archived"),
            ("gitlab.com/ScottRBK/forgetful", "active"),
            ("github.com/ScottRBK/forgetful-plugin", "active"),
            ("github.com/ScottRBK/subgroup/forgetful", "active"),
            ("github.com/scottrbk/forgetful", "active"),
            ("ssh://git@github.com:2222/ScottRBK/forgetful.git", "active"),
            ("ScottRBK/forgetful", "active"),
        ]
        created_ids = []
        for repo_name, status in repositories:
            created = await http_client.post("/api/v1/projects", json={
                "name": "Repository lookup",
                "description": "Check repository identity",
                "project_type": "development",
                "repo_name": repo_name,
                "status": status,
            })
            assert created.status_code == 201
            created_ids.append(created.json()["id"])

        # A matching repository belonging to another user must stay private.
        with monkeypatch.context() as other_user:
            other_user.setattr(settings, "DEFAULT_USER_ID", "repository-lookup-other-user")
            other_user.setattr(settings, "DEFAULT_USER_EMAIL", "other-repo-user@example.test")
            private = await http_client.post("/api/v1/projects", json={
                "name": "Private project",
                "description": "Another user's repository",
                "project_type": "development",
                "repo_name": "github.com/ScottRBK/forgetful",
            })
            assert private.status_code == 201

        result = await http_client.get("/api/v1/projects", params={"repo_name": query})
        active = await http_client.get("/api/v1/projects", params={
            "repo_name": query, "status": "active",
        })

        assert result.status_code == active.status_code == 200
        assert {p["id"] for p in result.json()["projects"]} == set(created_ids[:4])
        assert result.json()["total"] == 4
        assert {p["id"] for p in active.json()["projects"]} == set(created_ids[:3])

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("stored", "query", "different"), [
        ("group/subgroup/repo.git", "group/subgroup/repo/", "group/repo"),
        ("local project", "local project", "local-project"),
        ("https://git.test:bad/team/repo", "https://git.test:bad/team/repo",
         "https://git.test/team/repo"),
        ("git.test/team//repo", "git.test/team//repo", "git.test/team/repo"),
    ])
    async def test_lookup_hostless_and_opaque_repositories(
        self, http_client, stored, query, different,
    ):
        """Hostless paths and uninterpreted values stay searchable without false matches."""
        created_ids = []
        for repo_name in (stored, different):
            created = await http_client.post("/api/v1/projects", json={
                "name": "Other repository formats",
                "description": "Hostless and opaque lookup",
                "project_type": "development",
                "repo_name": repo_name,
            })
            assert created.status_code == 201
            created_ids.append(created.json()["id"])

        result = await http_client.get("/api/v1/projects", params={"repo_name": query})

        assert result.status_code == 200
        assert [p["id"] for p in result.json()["projects"]] == [created_ids[0]]

    @pytest.mark.asyncio
    async def test_list_projects_empty(self, http_client):
        """GET /api/v1/projects returns empty list initially."""
        response = await http_client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert data["projects"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_projects_with_data(self, http_client):
        """GET /api/v1/projects returns created projects."""
        # Create a project first
        payload = {
            "name": "Test Project",
            "description": "A test project",
            "project_type": "development",
        }
        create_response = await http_client.post("/api/v1/projects", json=payload)
        assert create_response.status_code == 201

        # Now list
        response = await http_client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert len(data["projects"]) >= 1
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_projects_filter_by_status(self, http_client):
        """GET /api/v1/projects filters by status."""
        # Create projects with different statuses
        await http_client.post("/api/v1/projects", json={
            "name": "Active Project",
            "description": "An active project",
            "project_type": "development",
            "status": "active",
        })

        # Filter by active status
        response = await http_client.get("/api/v1/projects?status=active")
        assert response.status_code == 200
        data = response.json()
        for project in data["projects"]:
            assert project["status"] == "active"

    @pytest.mark.asyncio
    async def test_list_projects_invalid_status(self, http_client):
        """GET /api/v1/projects returns 400 for invalid status."""
        response = await http_client.get("/api/v1/projects?status=invalid")
        assert response.status_code == 400


class TestProjectAPICrud:
    """Test Project CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_project(self, http_client):
        """POST /api/v1/projects creates a new project."""
        payload = {
            "name": "New Project",
            "description": "A new development project",
            "project_type": "development",
        }
        response = await http_client.post("/api/v1/projects", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] > 0
        assert data["name"] == "New Project"
        assert data["project_type"] == "development"
        assert data["status"] == "active"  # Default status

    @pytest.mark.asyncio
    @pytest.mark.parametrize("repo_name", [
        "owner/repo",
        "group/subgroup/repo",
        "git.example.test/team/repo",
        "dev.azure.com/contoso/widgets/_git/api",
        "https://github.com/ScottRBK/forgetful.git",
        "git@github.com:ScottRBK/forgetful.git",
        "local project",
    ])
    async def test_repository_round_trip(self, http_client, repo_name):
        """Repository identifiers survive creation, clearing, and linking an existing project."""
        payload = {
            "name": "Repository project",
            "description": "A project linked to a repository",
            "project_type": "development",
            "repo_name": f"  {repo_name}  ",
        }

        created = await http_client.post("/api/v1/projects", json=payload)
        assert created.status_code == 201
        project_url = f"/api/v1/projects/{created.json()['id']}"
        retrieved = await http_client.get(project_url)
        assert retrieved.json()["repo_name"] == repo_name

        cleared = await http_client.put(project_url, json={"repo_name": ""})
        assert cleared.status_code == 200
        assert cleared.json()["repo_name"] is None

        linked = await http_client.put(project_url, json={"repo_name": repo_name})
        assert linked.status_code == 200
        retrieved = await http_client.get(project_url)
        assert retrieved.json()["repo_name"] == repo_name

    @pytest.mark.asyncio
    @pytest.mark.parametrize("method", ["POST", "PUT"])
    @pytest.mark.parametrize(("invalid", "field", "message"), [
        ({"name": "   "}, "name", "cannot be empty or whitespace only"),
        ({"repo_name": "x" * 256}, "repo_name", "at most 255 characters"),
    ])
    async def test_project_validation_error(self, http_client, method, invalid, field, message):
        """Create and update return useful JSON for custom validators and length limits."""
        payload = {
            "name": "Validation project",
            "description": "Check error responses",
            "project_type": "development",
        }
        url = "/api/v1/projects"
        if method == "PUT":
            created = await http_client.post(url, json=payload)
            assert created.status_code == 201
            url = f"{url}/{created.json()['id']}"

        response = await http_client.request(method, url, json={**payload, **invalid})

        assert response.status_code == 400
        error = response.json()["error"][0]
        assert error["loc"] == [field]
        assert message in error["msg"]

    @pytest.mark.asyncio
    async def test_get_project(self, http_client):
        """GET /api/v1/projects/{id} returns the project."""
        # Create first
        create_response = await http_client.post("/api/v1/projects", json={
            "name": "Get Test Project",
            "description": "Testing get endpoint",
            "project_type": "documentation",
        })
        project_id = create_response.json()["id"]

        # Get
        response = await http_client.get(f"/api/v1/projects/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == "Get Test Project"

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, http_client):
        """GET /api/v1/projects/{id} returns 404 for missing project."""
        response = await http_client.get("/api/v1/projects/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_project(self, http_client):
        """PUT /api/v1/projects/{id} updates the project."""
        # Create first
        create_response = await http_client.post("/api/v1/projects", json={
            "name": "Update Test Project",
            "description": "Original description",
            "project_type": "development",
        })
        project_id = create_response.json()["id"]

        # Update
        update_payload = {
            "name": "Updated Project Name",
            "description": "Updated description",
            "status": "completed",
        }
        response = await http_client.put(f"/api/v1/projects/{project_id}", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Project Name"
        assert data["description"] == "Updated description"
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_update_project_not_found(self, http_client):
        """PUT /api/v1/projects/{id} returns 404 for missing project."""
        response = await http_client.put("/api/v1/projects/99999", json={"name": "Test"})
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_project(self, http_client):
        """DELETE /api/v1/projects/{id} deletes the project."""
        # Create first
        create_response = await http_client.post("/api/v1/projects", json={
            "name": "Delete Test Project",
            "description": "Will be deleted",
            "project_type": "infrastructure",
        })
        project_id = create_response.json()["id"]

        # Delete
        response = await http_client.delete(f"/api/v1/projects/{project_id}")
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify deleted
        get_response = await http_client.get(f"/api/v1/projects/{project_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, http_client):
        """DELETE /api/v1/projects/{id} returns 404 for missing project."""
        response = await http_client.delete("/api/v1/projects/99999")
        assert response.status_code == 404


class TestProjectAPILastEncodingPoint:
    """Test last_encoding_point REST round trip."""

    @pytest.mark.asyncio
    async def test_last_encoding_point_round_trip(self, http_client):
        """POST with field, GET returns it, PUT clears it."""
        checkpoint = "5d41402abc4b2a76b9719d911017c592"
        payload = {
            "name": "REST Encoding Point Project",
            "description": "REST round trip for last_encoding_point",
            "project_type": "development",
            "last_encoding_point": checkpoint,
        }

        create_response = await http_client.post("/api/v1/projects", json=payload)
        assert create_response.status_code == 201
        created = create_response.json()
        assert created["last_encoding_point"] == checkpoint
        project_id = created["id"]

        get_response = await http_client.get(f"/api/v1/projects/{project_id}")
        assert get_response.status_code == 200
        assert get_response.json()["last_encoding_point"] == checkpoint

        clear_response = await http_client.put(
            f"/api/v1/projects/{project_id}",
            json={"last_encoding_point": ""},
        )
        assert clear_response.status_code == 200
        assert clear_response.json()["last_encoding_point"] is None


class TestProjectTypes:
    """Test different project types."""

    @pytest.mark.asyncio
    async def test_create_project_all_types(self, http_client):
        """POST /api/v1/projects supports all project types."""
        project_types = ["personal", "work", "learning", "development", "infrastructure", "template", "product", "documentation", "open-source"]

        for ptype in project_types:
            response = await http_client.post("/api/v1/projects", json={
                "name": f"Project Type {ptype}",
                "description": f"Testing {ptype} type",
                "project_type": ptype,
            })
            assert response.status_code == 201, f"Failed for type: {ptype}"
            assert response.json()["project_type"] == ptype
