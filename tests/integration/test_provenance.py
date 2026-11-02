"""Integration tests for provenance tracking across all object types

Tests the apply_provenance_defaults() utility and verifies provenance fields
flow through service create methods correctly using in-memory stubs.
"""

from unittest.mock import patch
from uuid import uuid4

import pytest

from app.models.code_artifact_models import CodeArtifactCreate
from app.models.document_models import DocumentCreate
from app.models.entity_models import EntityCreate, EntityRelationshipCreate, EntityType
from app.models.memory_models import MemoryCreate
from app.models.plan_models import PlanCreate, TaskCreate
from app.models.project_models import ProjectCreate, ProjectType, ProjectUpdate
from app.models.skill_models import SkillCreate
from app.utils.provenance import (
    apply_provenance_defaults,
    apply_provenance_defaults_for_update,
)

# ============================================================================
# apply_provenance_defaults() unit tests
# ============================================================================


class TestApplyProvenanceDefaults:
    """Tests for the provenance defaults utility function."""

    def test_no_env_vars_set_returns_unchanged(self):
        """When no env vars configured, provenance fields remain None."""
        data = ProjectCreate(
            name="test", description="test project", project_type=ProjectType.DEVELOPMENT,
        )
        result = apply_provenance_defaults(data)
        assert result.encoding_agent is None
        assert result.encoding_version is None
        assert result.agent_id is None
        assert result.agent_version is None
        assert result.agent_model is None

    def test_env_defaults_fill_none_fields(self):
        """When env vars set and fields are None, defaults are applied."""
        data = ProjectCreate(
            name="test", description="test project", project_type=ProjectType.DEVELOPMENT,
        )
        with patch("app.utils.provenance.settings") as mock_settings:
            mock_settings.ENCODING_AGENT = "OpenCode"
            mock_settings.ENCODING_VERSION = "1.3.13"
            mock_settings.AGENT_ID = "CodeAgentUltra"
            mock_settings.AGENT_VERSION = "1.0"
            mock_settings.AGENT_MODEL = "claude-sonnet-4-6"
            mock_settings.ENFORCE_ENV_OVERWRITE = False

            result = apply_provenance_defaults(data)

        assert result.encoding_agent == "OpenCode"
        assert result.encoding_version == "1.3.13"
        assert result.agent_id == "CodeAgentUltra"
        assert result.agent_version == "1.0"
        assert result.agent_model == "claude-sonnet-4-6"

    def test_agent_values_take_precedence_without_enforce(self):
        """When ENFORCE_ENV_OVERWRITE=False, agent-provided values win."""
        data = ProjectCreate(
            name="test", description="test project", project_type=ProjectType.DEVELOPMENT,
            encoding_agent="MyAgent", agent_id="my-agent-id",
        )
        with patch("app.utils.provenance.settings") as mock_settings:
            mock_settings.ENCODING_AGENT = "EnvAgent"
            mock_settings.ENCODING_VERSION = "2.0"
            mock_settings.AGENT_ID = "EnvAgentId"
            mock_settings.AGENT_VERSION = "2.0"
            mock_settings.AGENT_MODEL = "env-model"
            mock_settings.ENFORCE_ENV_OVERWRITE = False

            result = apply_provenance_defaults(data)

        # Agent-provided values preserved
        assert result.encoding_agent == "MyAgent"
        assert result.agent_id == "my-agent-id"
        # None fields filled by env
        assert result.encoding_version == "2.0"
        assert result.agent_version == "2.0"
        assert result.agent_model == "env-model"

    def test_enforce_overwrite_overrides_agent_values(self):
        """When ENFORCE_ENV_OVERWRITE=True, env values always win."""
        data = ProjectCreate(
            name="test", description="test project", project_type=ProjectType.DEVELOPMENT,
            encoding_agent="MyAgent", agent_id="my-agent-id",
        )
        with patch("app.utils.provenance.settings") as mock_settings:
            mock_settings.ENCODING_AGENT = "EnvAgent"
            mock_settings.ENCODING_VERSION = "2.0"
            mock_settings.AGENT_ID = "EnvAgentId"
            mock_settings.AGENT_VERSION = "2.0"
            mock_settings.AGENT_MODEL = "env-model"
            mock_settings.ENFORCE_ENV_OVERWRITE = True

            result = apply_provenance_defaults(data)

        # Env always wins
        assert result.encoding_agent == "EnvAgent"
        assert result.agent_id == "EnvAgentId"
        assert result.encoding_version == "2.0"
        assert result.agent_version == "2.0"
        assert result.agent_model == "env-model"

    def test_partial_env_vars_only_fills_set_fields(self):
        """Only env vars that are non-empty get applied."""
        data = ProjectCreate(
            name="test", description="test project", project_type=ProjectType.DEVELOPMENT,
        )
        with patch("app.utils.provenance.settings") as mock_settings:
            mock_settings.ENCODING_AGENT = "OpenCode"
            mock_settings.ENCODING_VERSION = ""
            mock_settings.AGENT_ID = ""
            mock_settings.AGENT_VERSION = ""
            mock_settings.AGENT_MODEL = "claude-sonnet-4-6"
            mock_settings.ENFORCE_ENV_OVERWRITE = False

            result = apply_provenance_defaults(data)

        assert result.encoding_agent == "OpenCode"
        assert result.encoding_version is None  # empty env var not applied
        assert result.agent_id is None
        assert result.agent_version is None
        assert result.agent_model == "claude-sonnet-4-6"

    def test_works_with_all_create_model_types(self):
        """Verify apply_provenance_defaults works on every Create model type."""
        models = [
            MemoryCreate(
                title="test", content="test content", context="test context",
                keywords=["k"], tags=["t"], importance=7,
            ),
            ProjectCreate(
                name="test", description="test", project_type=ProjectType.DEVELOPMENT,
            ),
            DocumentCreate(
                title="test", description="test", content="test content",
            ),
            CodeArtifactCreate(
                title="test", description="test", code="print('hello')", language="python",
            ),
            SkillCreate(
                name="test-skill", description="test", content="# test",
            ),
            EntityCreate(
                name="Test Entity", entity_type=EntityType.ORGANIZATION,
            ),
            EntityRelationshipCreate(
                source_entity_id=1, target_entity_id=2, relationship_type="works_at",
            ),
            PlanCreate(title="test plan", project_id=1),
            TaskCreate(title="test task", plan_id=1),
        ]

        with patch("app.utils.provenance.settings") as mock_settings:
            mock_settings.ENCODING_AGENT = "TestAgent"
            mock_settings.ENCODING_VERSION = ""
            mock_settings.AGENT_ID = "test-id"
            mock_settings.AGENT_VERSION = ""
            mock_settings.AGENT_MODEL = ""
            mock_settings.ENFORCE_ENV_OVERWRITE = False

            for model in models:
                result = apply_provenance_defaults(model)
                assert result.encoding_agent == "TestAgent", f"Failed for {type(model).__name__}"
                assert result.agent_id == "test-id", f"Failed for {type(model).__name__}"


# ============================================================================
# Service-level provenance tests (via in-memory stubs)
# ============================================================================


@pytest.mark.asyncio
async def test_project_service_applies_provenance_defaults(test_project_service):
    """Project service should apply env provenance defaults on create."""
    user_id = uuid4()

    with patch("app.services.project_service.apply_provenance_defaults", wraps=apply_provenance_defaults) as mock_apply:
        with patch("app.utils.provenance.settings") as mock_settings:
            mock_settings.ENCODING_AGENT = "TestAgent"
            mock_settings.ENCODING_VERSION = "1.0"
            mock_settings.AGENT_ID = "test-id"
            mock_settings.AGENT_VERSION = "1.0"
            mock_settings.AGENT_MODEL = "test-model"
            mock_settings.ENFORCE_ENV_OVERWRITE = False

            project = await test_project_service.create_project(
                user_id=user_id,
                project_data=ProjectCreate(
                    name="provenance-test",
                    description="Testing provenance defaults",
                    project_type=ProjectType.DEVELOPMENT,
                ),
            )

        mock_apply.assert_called_once()

    assert project.encoding_agent == "TestAgent"
    assert project.agent_id == "test-id"
    assert project.agent_model == "test-model"


@pytest.mark.asyncio
async def test_memory_service_applies_provenance_defaults(test_memory_service):
    """Memory service should apply env provenance defaults on create."""
    user_id = uuid4()

    with patch("app.services.memory_service.apply_provenance_defaults", wraps=apply_provenance_defaults) as mock_apply:
        with patch("app.utils.provenance.settings") as mock_settings:
            mock_settings.ENCODING_AGENT = "TestAgent"
            mock_settings.ENCODING_VERSION = "1.0"
            mock_settings.AGENT_ID = "test-id"
            mock_settings.AGENT_VERSION = "1.0"
            mock_settings.AGENT_MODEL = "test-model"
            mock_settings.ENFORCE_ENV_OVERWRITE = False

            write_result = await test_memory_service.create_memory(
                user_id=user_id,
                memory_data=MemoryCreate(
                    title="provenance test",
                    content="testing provenance",
                    context="integration test",
                    keywords=["test"],
                    tags=["test"],
                ),
            )
            memory = write_result.memory

        mock_apply.assert_called_once()

    assert memory.encoding_agent == "TestAgent"
    assert memory.agent_id == "test-id"


@pytest.mark.asyncio
async def test_document_service_applies_provenance_defaults(test_document_service):
    """Document service should apply env provenance defaults on create."""
    user_id = uuid4()

    with patch("app.services.document_service.apply_provenance_defaults", wraps=apply_provenance_defaults) as mock_apply:
        with patch("app.utils.provenance.settings") as mock_settings:
            mock_settings.ENCODING_AGENT = "DocAgent"
            mock_settings.ENCODING_VERSION = ""
            mock_settings.AGENT_ID = ""
            mock_settings.AGENT_VERSION = ""
            mock_settings.AGENT_MODEL = ""
            mock_settings.ENFORCE_ENV_OVERWRITE = False

            doc = await test_document_service.create_document(
                user_id=user_id,
                document_data=DocumentCreate(
                    title="test doc", description="test", content="content",
                ),
            )

        mock_apply.assert_called_once()

    assert doc.encoding_agent == "DocAgent"


@pytest.mark.asyncio
async def test_entity_service_applies_provenance_defaults(test_entity_service):
    """Entity service should apply env provenance defaults on create."""
    user_id = uuid4()

    with patch("app.services.entity_service.apply_provenance_defaults", wraps=apply_provenance_defaults) as mock_apply:
        with patch("app.utils.provenance.settings") as mock_settings:
            mock_settings.ENCODING_AGENT = "EntityAgent"
            mock_settings.ENCODING_VERSION = ""
            mock_settings.AGENT_ID = ""
            mock_settings.AGENT_VERSION = ""
            mock_settings.AGENT_MODEL = ""
            mock_settings.ENFORCE_ENV_OVERWRITE = False

            entity = (await test_entity_service.create_entity(
                user_id=user_id,
                entity_data=EntityCreate(
                    name="Test Org", entity_type=EntityType.ORGANIZATION,
                ),
            )).entity

        mock_apply.assert_called_once()

    assert entity.encoding_agent == "EntityAgent"


@pytest.mark.asyncio
async def test_code_artifact_service_applies_provenance_defaults(test_code_artifact_service):
    """Code artifact service should apply env provenance defaults on create."""
    user_id = uuid4()

    with patch("app.services.code_artifact_service.apply_provenance_defaults", wraps=apply_provenance_defaults) as mock_apply:
        with patch("app.utils.provenance.settings") as mock_settings:
            mock_settings.ENCODING_AGENT = "CodeAgent"
            mock_settings.ENCODING_VERSION = ""
            mock_settings.AGENT_ID = ""
            mock_settings.AGENT_VERSION = ""
            mock_settings.AGENT_MODEL = ""
            mock_settings.ENFORCE_ENV_OVERWRITE = False

            artifact = await test_code_artifact_service.create_code_artifact(
                user_id=user_id,
                artifact_data=CodeArtifactCreate(
                    title="test", description="test", code="print(1)", language="python",
                ),
            )

        mock_apply.assert_called_once()

    assert artifact.encoding_agent == "CodeAgent"


# ============================================================================
# apply_provenance_defaults_for_update() unit tests
# ============================================================================


class TestApplyProvenanceDefaultsForUpdate:
    """Tests for the update-specific provenance enforcement function."""

    def test_no_change_without_enforce(self):
        """When ENFORCE_ENV_OVERWRITE=False, update models pass through unchanged."""
        data = ProjectUpdate(encoding_agent="AgentFromCaller", agent_id="caller-id")
        with patch("app.utils.provenance.settings") as mock_settings:
            mock_settings.ENCODING_AGENT = "EnvAgent"
            mock_settings.ENCODING_VERSION = "2.0"
            mock_settings.AGENT_ID = "EnvAgentId"
            mock_settings.AGENT_VERSION = "2.0"
            mock_settings.AGENT_MODEL = "env-model"
            mock_settings.ENFORCE_ENV_OVERWRITE = False

            result = apply_provenance_defaults_for_update(data)

        # Agent values preserved — no enforcement
        assert result.encoding_agent == "AgentFromCaller"
        assert result.agent_id == "caller-id"

    def test_enforce_overrides_explicitly_set_fields(self):
        """When ENFORCE_ENV_OVERWRITE=True, env values override agent-provided update fields."""
        data = ProjectUpdate(encoding_agent="AgentFromCaller", agent_id="caller-id")
        with patch("app.utils.provenance.settings") as mock_settings:
            mock_settings.ENCODING_AGENT = "EnvAgent"
            mock_settings.ENCODING_VERSION = "2.0"
            mock_settings.AGENT_ID = "EnvAgentId"
            mock_settings.AGENT_VERSION = "2.0"
            mock_settings.AGENT_MODEL = "env-model"
            mock_settings.ENFORCE_ENV_OVERWRITE = True

            result = apply_provenance_defaults_for_update(data)

        # Env values override agent-provided values
        assert result.encoding_agent == "EnvAgent"
        assert result.agent_id == "EnvAgentId"

    def test_enforce_does_not_inject_unset_fields(self):
        """ENFORCE only overrides fields explicitly in the update, not unset fields."""
        # Only setting encoding_agent, not agent_id
        data = ProjectUpdate(encoding_agent="AgentFromCaller")
        with patch("app.utils.provenance.settings") as mock_settings:
            mock_settings.ENCODING_AGENT = "EnvAgent"
            mock_settings.ENCODING_VERSION = "2.0"
            mock_settings.AGENT_ID = "EnvAgentId"
            mock_settings.AGENT_VERSION = "2.0"
            mock_settings.AGENT_MODEL = "env-model"
            mock_settings.ENFORCE_ENV_OVERWRITE = True

            result = apply_provenance_defaults_for_update(data)

        # encoding_agent was explicitly set → overridden
        assert result.encoding_agent == "EnvAgent"
        # agent_id was NOT in the update → not injected (PATCH semantics preserved)
        assert result.agent_id is None
        assert "agent_id" not in result.model_fields_set

    def test_no_env_vars_returns_unchanged(self):
        """When no env vars configured, update models pass through unchanged even with enforce."""
        data = ProjectUpdate(encoding_agent="AgentFromCaller")
        with patch("app.utils.provenance.settings") as mock_settings:
            mock_settings.ENCODING_AGENT = ""
            mock_settings.ENCODING_VERSION = ""
            mock_settings.AGENT_ID = ""
            mock_settings.AGENT_VERSION = ""
            mock_settings.AGENT_MODEL = ""
            mock_settings.ENFORCE_ENV_OVERWRITE = True

            result = apply_provenance_defaults_for_update(data)

        # No env values to apply, agent value preserved
        assert result.encoding_agent == "AgentFromCaller"


# ============================================================================
# Service-level update enforcement tests
# ============================================================================


@pytest.mark.asyncio
async def test_project_service_enforces_provenance_on_update(test_project_service):
    """Project update with ENFORCE_ENV_OVERWRITE=True should override agent provenance."""
    user_id = uuid4()

    # Create project first
    project = await test_project_service.create_project(
        user_id=user_id,
        project_data=ProjectCreate(
            name="enforce-update-test",
            description="Testing enforce on update",
            project_type=ProjectType.DEVELOPMENT,
            encoding_agent="OriginalAgent",
        ),
    )

    # Update with agent-provided provenance under ENFORCE mode
    with patch("app.services.project_service.apply_provenance_defaults_for_update", wraps=apply_provenance_defaults_for_update) as mock_apply:
        with patch("app.utils.provenance.settings") as mock_settings:
            mock_settings.ENCODING_AGENT = "EnvAgent"
            mock_settings.ENCODING_VERSION = ""
            mock_settings.AGENT_ID = "EnvAgentId"
            mock_settings.AGENT_VERSION = ""
            mock_settings.AGENT_MODEL = ""
            mock_settings.ENFORCE_ENV_OVERWRITE = True

            updated = await test_project_service.update_project(
                user_id=user_id,
                project_id=project.id,
                project_data=ProjectUpdate(
                    encoding_agent="HackerAgent",
                    agent_id="hacker-id",
                ),
            )

        mock_apply.assert_called_once()

    # Env values should win over agent-provided values
    assert updated.encoding_agent == "EnvAgent"
    assert updated.agent_id == "EnvAgentId"


@pytest.mark.asyncio
async def test_project_service_no_enforce_allows_update(test_project_service):
    """Project update with ENFORCE_ENV_OVERWRITE=False should allow agent provenance changes."""
    user_id = uuid4()

    project = await test_project_service.create_project(
        user_id=user_id,
        project_data=ProjectCreate(
            name="no-enforce-update",
            description="Testing no enforce on update",
            project_type=ProjectType.DEVELOPMENT,
        ),
    )

    with patch("app.utils.provenance.settings") as mock_settings:
        mock_settings.ENCODING_AGENT = "EnvAgent"
        mock_settings.ENCODING_VERSION = ""
        mock_settings.AGENT_ID = ""
        mock_settings.AGENT_VERSION = ""
        mock_settings.AGENT_MODEL = ""
        mock_settings.ENFORCE_ENV_OVERWRITE = False

        updated = await test_project_service.update_project(
            user_id=user_id,
            project_id=project.id,
            project_data=ProjectUpdate(
                encoding_agent="CallerAgent",
            ),
        )

    # Without enforce, agent values should go through
    assert updated.encoding_agent == "CallerAgent"


@pytest.mark.asyncio
async def test_provenance_fields_preserved_on_create(test_project_service):
    """Explicit provenance fields should be preserved through create."""
    user_id = uuid4()

    project = await test_project_service.create_project(
        user_id=user_id,
        project_data=ProjectCreate(
            name="provenance-explicit",
            description="Testing explicit provenance",
            project_type=ProjectType.DEVELOPMENT,
            source_repo="owner/repo",
            source_files=["src/main.py", "src/utils.py"],
            source_url="https://example.com",
            confidence=0.95,
            encoding_agent="ExplicitAgent",
            encoding_version="2.0",
            agent_id="explicit-id",
            agent_version="3.0",
            agent_model="claude-opus-4-6",
        ),
    )

    assert project.source_repo == "owner/repo"
    assert project.source_files == ["src/main.py", "src/utils.py"]
    assert project.source_url == "https://example.com"
    assert project.confidence == 0.95
    assert project.encoding_agent == "ExplicitAgent"
    assert project.encoding_version == "2.0"
    assert project.agent_id == "explicit-id"
    assert project.agent_version == "3.0"
    assert project.agent_model == "claude-opus-4-6"
