"""Skill Service - Business logic for skill operations

This service implements functionality for managing skills:
    - CRUD operations (create, read, update, delete)
    - Semantic search
    - Import/export in Agent Skills markdown format
    - Project association
"""
import re
from typing import TYPE_CHECKING
from uuid import UUID

import yaml

from app.config.logging_config import logging
from app.config.settings import settings
from app.exceptions import NotFoundError
from app.models.activity_models import (
    ActionType,
    ActivityEvent,
    ActorType,
    EntityType,
)
from app.models.skill_models import (
    Skill,
    SkillCreate,
    SkillLinks,
    SkillSummary,
    SkillUpdate,
)
from app.protocols.skill_protocol import SkillRepository
from app.utils.provenance import (
    apply_provenance_defaults,
    apply_provenance_defaults_for_update,
)
from app.utils.pydantic_helper import get_changed_fields

if TYPE_CHECKING:
    from app.events import EventBus

logger = logging.getLogger(__name__)

# Frontmatter is a handful of short fields; the cap only bounds hostile input.
_FRONTMATTER_MAX_CHARS = 16_384

_FRONTMATTER_OPEN_RE = re.compile(r"---[ \t]*\r?\n")
_FRONTMATTER_CLOSE_RE = re.compile(r"^---[ \t]*(?:\r?\n|\Z)", re.MULTILINE)
# YAML line breaks only; str.splitlines() also splits on U+2028, U+2029, U+0085, ...
_YAML_LINE_BREAK_RE = re.compile(r"\r\n|\r|\n")
_YAML_COMMENT_RE = re.compile(r"\s#")


class _FrontmatterLoader(yaml.SafeLoader):
    """SafeLoader for untrusted SKILL.md frontmatter.

    Aliases are rejected: they turn a few hundred bytes into billions of nodes
    once the value is serialised.
    """

    def compose_node(
        self,
        parent: yaml.Node | None,
        index: yaml.Node | int | None,
    ) -> yaml.Node | None:
        if self.check_event(yaml.AliasEvent):
            raise yaml.composer.ComposerError(
                None,
                None,
                "aliases are not supported in skill frontmatter",
                self.peek_event().start_mark,
            )
        return super().compose_node(parent, index)


def _quote_unquoted_frontmatter_scalars(raw: str) -> str:
    """Quote scalar frontmatter values that contain unescaped colons.

    Trailing ``# comments`` are kept out of the quoted value, and the text is
    only split on YAML line breaks so other characters are never altered.
    """
    quoted_lines: list[str] = []
    changed = False
    for line in _YAML_LINE_BREAK_RE.split(raw):
        match = re.match(r"^([A-Za-z0-9_-]+):\s+(.*)$", line)
        if not match:
            quoted_lines.append(line)
            continue

        key, value = match.group(1), match.group(2)
        if not value or value.startswith("#"):
            quoted_lines.append(line)
            continue

        comment_match = _YAML_COMMENT_RE.search(value)
        comment_start = comment_match.start() if comment_match else len(value)
        scalar, comment = value[:comment_start].rstrip(), value[comment_start:]

        if scalar.startswith(("[", "{", "|", ">", '"', "'")):
            quoted_lines.append(line)
            continue

        if ":" in scalar:
            escaped = scalar.replace("\\", "\\\\").replace('"', '\\"')
            quoted_lines.append(f'{key}: "{escaped}"{comment}')
            changed = True
        else:
            quoted_lines.append(line)

    return "\n".join(quoted_lines) if changed else raw


def _split_frontmatter(skill_md: str) -> tuple[str, str]:
    """Split SKILL.md text into raw YAML frontmatter and markdown body.

    The delimiters are lines made only of ``---``, so a ``---`` inside a value
    or a horizontal rule in the body never ends the frontmatter. Only the line
    breaks that separate the frontmatter from the body are removed from the body.
    """
    text = skill_md.lstrip("\ufeff").lstrip()
    opening = _FRONTMATTER_OPEN_RE.match(text)
    closing = _FRONTMATTER_CLOSE_RE.search(text, opening.end()) if opening else None
    if opening is None or closing is None:
        raise ValueError(
            "Invalid skill markdown: expected YAML frontmatter between --- delimiters",
        )

    body = text[closing.end():]
    body = re.sub(r"\A\r?\n", "", body, count=1)
    body = re.sub(r"\r?\n\Z", "", body, count=1)
    if not body.strip():
        body = ""
    return text[opening.end():closing.start()].rstrip(" \t\r\n"), body


def _load_frontmatter(raw: str) -> object:
    loader = _FrontmatterLoader(raw)
    try:
        return loader.get_single_data()
    finally:
        loader.dispose()


def _parse_frontmatter(raw: str) -> object:
    """Parse raw frontmatter, raising ValueError when it is not valid YAML.

    Valid YAML is parsed as written. Only when that fails are unquoted colons
    in scalar values quoted, to accept hand-written files such as
    ``description: Use when X. Keywords: a, b``.
    """
    if len(raw) > _FRONTMATTER_MAX_CHARS:
        raise ValueError(
            "Invalid YAML frontmatter: frontmatter is too large "
            f"(max {_FRONTMATTER_MAX_CHARS} characters)",
        )

    try:
        return _load_frontmatter(raw)
    except (yaml.YAMLError, RecursionError) as exc:
        error = exc

    quoted = _quote_unquoted_frontmatter_scalars(raw)
    if quoted != raw:
        try:
            return _load_frontmatter(quoted)
        except (yaml.YAMLError, RecursionError) as exc:
            error = exc

    detail = "nested too deeply" if isinstance(error, RecursionError) else str(error)
    raise ValueError(f"Invalid YAML frontmatter: {detail}") from error


class SkillService:
    """Service layer for skill operations

    Handles business logic for creating, updating, querying, and deleting skills.
    Uses repository protocol for data access.
    """

    def __init__(
        self,
        skill_repo: SkillRepository,
        event_bus: "EventBus | None" = None,
    ):
        """Initialize with repository protocol (not concrete implementation)

        Args:
            skill_repo: Skill repository implementing the protocol
            event_bus: Optional event bus for activity tracking
        """
        self.skill_repo = skill_repo
        self._event_bus = event_bus
        logger.info("Skill service initialized")

    async def _emit_event(
        self,
        user_id: UUID,
        entity_type: EntityType,
        entity_id: int,
        action: ActionType,
        snapshot: dict,
        changes: dict | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Emit an activity event to the event bus.

        This is a no-op if no event bus is configured.

        Args:
            user_id: User ID for the event
            entity_type: Type of entity (skill)
            entity_id: ID of the entity
            action: Action that occurred (created, updated, deleted, etc.)
            snapshot: Full entity state at event time
            changes: Field changes for updates
            metadata: Additional context
        """
        if self._event_bus is None:
            return

        event = ActivityEvent(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            changes=changes,
            snapshot=snapshot,
            actor=ActorType.USER,
            metadata=metadata,
            user_id=str(user_id),
        )

        await self._event_bus.emit(event)

    async def create_skill(
        self,
        user_id: UUID,
        skill_data: SkillCreate,
    ) -> Skill:
        """Create new skill

        Args:
            user_id: User ID for ownership
            skill_data: SkillCreate with name, description, content, etc.

        Returns:
            Created Skill with generated ID and timestamps
        """
        logger.info(
            "creating skill",
            extra={
                "name": skill_data.name,
                "user_id": str(user_id),
            },
        )

        # Enforce unique skill name per user
        if await self.skill_repo.skill_name_exists(user_id, skill_data.name):
            msg = f"A skill named '{skill_data.name}' already exists"
            raise ValueError(msg)

        skill_data = apply_provenance_defaults(skill_data)
        skill = await self.skill_repo.create_skill(
            user_id=user_id,
            skill_data=skill_data,
        )

        logger.info(
            "skill created",
            extra={
                "skill_id": skill.id,
                "user_id": str(user_id),
            },
        )

        # Emit created event
        await self._emit_event(
            user_id=user_id,
            entity_type=EntityType.SKILL,
            entity_id=skill.id,
            action=ActionType.CREATED,
            snapshot=skill.model_dump(mode="json"),
        )

        return skill

    async def get_skill(
        self,
        user_id: UUID,
        skill_id: int,
    ) -> Skill:
        """Get skill by ID with ownership verification

        Args:
            user_id: User ID for ownership verification
            skill_id: Skill ID to retrieve

        Returns:
            Skill with full details

        Raises:
            NotFoundError: If skill not found or not owned by user
        """
        logger.info(
            "getting skill",
            extra={
                "skill_id": skill_id,
                "user_id": str(user_id),
            },
        )

        skill = await self.skill_repo.get_skill_by_id(
            user_id=user_id,
            skill_id=skill_id,
        )

        if not skill:
            raise NotFoundError(f"Skill {skill_id} not found")

        logger.info(
            "skill retrieved",
            extra={
                "skill_id": skill_id,
                "user_id": str(user_id),
            },
        )

        # Emit read event (opt-in via ACTIVITY_TRACK_READS)
        if settings.ACTIVITY_TRACK_READS and self._event_bus:
            await self._emit_event(
                user_id=user_id,
                entity_type=EntityType.SKILL,
                entity_id=skill_id,
                action=ActionType.READ,
                snapshot=skill.model_dump(mode="json"),
            )

        return skill

    async def list_skills(
        self,
        user_id: UUID,
        project_id: int | None = None,
        tags: list[str] | None = None,
        importance_threshold: int | None = None,
    ) -> list[SkillSummary]:
        """List skills with optional filtering

        Args:
            user_id: User ID for ownership filtering
            project_id: Optional filter by project
            tags: Optional filter by tags (returns skills with ANY of these tags)
            importance_threshold: Optional minimum importance level

        Returns:
            List of SkillSummary (lightweight, excludes full content)
        """
        logger.info(
            "listing skills",
            extra={
                "user_id": str(user_id),
                "project_id": project_id,
                "tags": tags,
                "importance_threshold": importance_threshold,
            },
        )

        skills = await self.skill_repo.list_skills(
            user_id=user_id,
            project_id=project_id,
            tags=tags,
            importance_threshold=importance_threshold,
        )

        logger.info(
            "skills retrieved",
            extra={
                "count": len(skills),
                "user_id": str(user_id),
            },
        )

        # Emit queried event (opt-in via ACTIVITY_TRACK_READS)
        if settings.ACTIVITY_TRACK_READS and self._event_bus:
            await self._emit_event(
                user_id=user_id,
                entity_type=EntityType.SKILL,
                entity_id=0,  # Query spans multiple skills
                action=ActionType.QUERIED,
                snapshot={
                    "result_ids": [s.id for s in skills],
                    "total_count": len(skills),
                },
                metadata={
                    "project_id": project_id,
                    "tags": tags,
                    "importance_threshold": importance_threshold,
                },
            )

        return skills

    async def update_skill(
        self,
        user_id: UUID,
        skill_id: int,
        skill_data: SkillUpdate,
    ) -> Skill:
        """Update existing skill (PATCH semantics)

        Only provided fields are updated. None/omitted fields remain unchanged.

        Args:
            user_id: User ID for ownership verification
            skill_id: Skill ID to update
            skill_data: SkillUpdate with fields to change

        Returns:
            Updated Skill

        Raises:
            NotFoundError: If skill not found or not owned by user
        """
        logger.info(
            "updating skill",
            extra={
                "skill_id": skill_id,
                "user_id": str(user_id),
            },
        )

        skill_data = apply_provenance_defaults_for_update(skill_data)

        # Get existing skill for change detection
        existing_skill = await self.skill_repo.get_skill_by_id(
            user_id=user_id,
            skill_id=skill_id,
        )

        if not existing_skill:
            raise NotFoundError(f"Skill {skill_id} not found")

        # Detect changes
        changed_fields = get_changed_fields(
            input_model=skill_data, existing_model=existing_skill,
        )

        skill = await self.skill_repo.update_skill(
            user_id=user_id,
            skill_id=skill_id,
            skill_data=skill_data,
        )

        logger.info(
            "skill updated",
            extra={
                "skill_id": skill_id,
                "user_id": str(user_id),
            },
        )

        # Emit updated event with changes
        if changed_fields:
            changes_dict = {
                field: {"old": old, "new": new}
                for field, (old, new) in changed_fields.items()
            }
            await self._emit_event(
                user_id=user_id,
                entity_type=EntityType.SKILL,
                entity_id=skill_id,
                action=ActionType.UPDATED,
                snapshot=skill.model_dump(mode="json"),
                changes=changes_dict,
            )

        return skill

    async def delete_skill(
        self,
        user_id: UUID,
        skill_id: int,
    ) -> bool:
        """Delete skill

        Args:
            user_id: User ID for ownership verification
            skill_id: Skill ID to delete

        Returns:
            True if deleted, False if not found or not owned by user
        """
        logger.info(
            "deleting skill",
            extra={
                "skill_id": skill_id,
                "user_id": str(user_id),
            },
        )

        # Fetch skill before deletion for snapshot
        existing_skill = await self.skill_repo.get_skill_by_id(
            user_id=user_id,
            skill_id=skill_id,
        )

        success = await self.skill_repo.delete_skill(
            user_id=user_id,
            skill_id=skill_id,
        )

        if success:
            logger.info(
                "skill deleted",
                extra={
                    "skill_id": skill_id,
                    "user_id": str(user_id),
                },
            )

            # Emit deleted event with pre-deletion snapshot
            if existing_skill:
                await self._emit_event(
                    user_id=user_id,
                    entity_type=EntityType.SKILL,
                    entity_id=skill_id,
                    action=ActionType.DELETED,
                    snapshot=existing_skill.model_dump(mode="json"),
                )
        else:
            logger.warning(
                "skill not found for deletion",
                extra={
                    "skill_id": skill_id,
                    "user_id": str(user_id),
                },
            )

        return success

    async def search_skills(
        self,
        user_id: UUID,
        query: str,
        k: int = 5,
        project_id: int | None = None,
    ) -> list[SkillSummary]:
        """Search skills by semantic similarity

        Args:
            user_id: User ID for ownership filtering
            query: Search query string
            k: Number of results to return (default: 5)
            project_id: Optional filter by project

        Returns:
            List of SkillSummary ranked by relevance
        """
        logger.info(
            "searching skills",
            extra={
                "user_id": str(user_id),
                "query": query[:50],
                "k": k,
                "project_id": project_id,
            },
        )

        results = await self.skill_repo.search_skills(
            user_id=user_id,
            query=query,
            k=k,
            project_id=project_id,
        )

        logger.info(
            "skill search completed",
            extra={
                "count": len(results),
                "user_id": str(user_id),
            },
        )

        return results

    async def import_skill(
        self,
        user_id: UUID,
        skill_md_content: str,
        project_id: int | None = None,
        importance: int = 7,
    ) -> Skill:
        """Import a skill from Agent Skills markdown format

        Parses YAML frontmatter between --- delimiters and extracts
        standard fields per the Agent Skills specification.

        Args:
            user_id: User ID for ownership
            skill_md_content: Raw SKILL.md content with YAML frontmatter
            project_id: Optional project association (overrides frontmatter)
            importance: Importance level (default: 7)

        Returns:
            Created Skill

        Raises:
            ValueError: If frontmatter is missing, malformed or too large
        """
        logger.info(
            "importing skill from markdown",
            extra={"user_id": str(user_id)},
        )

        frontmatter_raw, body = _split_frontmatter(skill_md_content)
        frontmatter = _parse_frontmatter(frontmatter_raw)
        if not isinstance(frontmatter, dict):
            raise ValueError("Invalid YAML frontmatter: expected a mapping")

        # Extract standard fields
        name = frontmatter.get("name")
        description = frontmatter.get("description")
        skill_license = frontmatter.get("license")
        compatibility = frontmatter.get("compatibility")
        metadata = frontmatter.get("metadata")

        # Map allowed-tools (hyphenated standard) to allowed_tools (underscored)
        allowed_tools = frontmatter.get("allowed-tools")
        tags = frontmatter.get("tags", [])

        if not name:
            raise ValueError("Skill frontmatter must include 'name'")
        if not description:
            raise ValueError("Skill frontmatter must include 'description'")

        skill_data = SkillCreate(
            name=name,
            description=description,
            content=body,
            license=skill_license,
            compatibility=compatibility,
            allowed_tools=allowed_tools,
            metadata=metadata,
            tags=tags,
            importance=importance,
            project_id=project_id,
        )

        return await self.create_skill(user_id=user_id, skill_data=skill_data)

    async def export_skill(
        self,
        user_id: UUID,
        skill_id: int,
    ) -> str:
        """Export a skill to Agent Skills markdown format

        Builds YAML frontmatter from standard fields and appends
        the content as the markdown body.

        Args:
            user_id: User ID for ownership verification
            skill_id: Skill ID to export

        Returns:
            Formatted SKILL.md string with YAML frontmatter

        Raises:
            NotFoundError: If skill not found or not owned by user
        """
        logger.info(
            "exporting skill to markdown",
            extra={
                "skill_id": skill_id,
                "user_id": str(user_id),
            },
        )

        skill = await self.get_skill(user_id=user_id, skill_id=skill_id)

        # Build frontmatter dict with only non-None standard fields
        frontmatter: dict = {}

        frontmatter["name"] = skill.name
        frontmatter["description"] = skill.description

        if skill.license is not None:
            frontmatter["license"] = skill.license
        if skill.compatibility is not None:
            frontmatter["compatibility"] = skill.compatibility
        if skill.metadata is not None:
            frontmatter["metadata"] = skill.metadata
        if skill.tags:
            frontmatter["tags"] = skill.tags
        # Map allowed_tools (underscored) back to allowed-tools (hyphenated)
        if skill.allowed_tools is not None:
            frontmatter["allowed-tools"] = skill.allowed_tools

        frontmatter_str = yaml.dump(
            frontmatter,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        ).strip()

        return f"---\n{frontmatter_str}\n---\n\n{skill.content}\n"

    async def link_skill_to_memory(
        self,
        user_id: UUID,
        skill_id: int,
        memory_id: int,
    ) -> dict:
        """Link a skill to a memory.

        Args:
            user_id: User ID for ownership verification
            skill_id: Skill to link
            memory_id: Memory to link to

        Returns:
            Confirmation dict with linked IDs
        """
        # Verify skill exists
        await self.get_skill(user_id=user_id, skill_id=skill_id)

        return await self.skill_repo.link_skill_to_memory(
            user_id=user_id,
            skill_id=skill_id,
            memory_id=memory_id,
        )

    async def unlink_skill_from_memory(
        self,
        user_id: UUID,
        skill_id: int,
        memory_id: int,
    ) -> dict:
        """Unlink a skill from a memory.

        Args:
            user_id: User ID for ownership verification
            skill_id: Skill to unlink
            memory_id: Memory to unlink from

        Returns:
            Confirmation dict
        """
        # Verify skill exists
        await self.get_skill(user_id=user_id, skill_id=skill_id)

        return await self.skill_repo.unlink_skill_from_memory(
            user_id=user_id,
            skill_id=skill_id,
            memory_id=memory_id,
        )

    async def link_skill_to_file(
        self,
        user_id: UUID,
        skill_id: int,
        file_id: int,
    ) -> dict:
        """Link a skill to a file.

        Args:
            user_id: User ID for ownership verification
            skill_id: Skill to link
            file_id: File to link to

        Returns:
            Confirmation dict with linked IDs
        """
        await self.get_skill(user_id=user_id, skill_id=skill_id)

        return await self.skill_repo.link_skill_to_file(
            user_id=user_id,
            skill_id=skill_id,
            file_id=file_id,
        )

    async def unlink_skill_from_file(
        self,
        user_id: UUID,
        skill_id: int,
        file_id: int,
    ) -> dict:
        """Unlink a skill from a file.

        Args:
            user_id: User ID for ownership verification
            skill_id: Skill to unlink
            file_id: File to unlink from

        Returns:
            Confirmation dict
        """
        await self.get_skill(user_id=user_id, skill_id=skill_id)

        return await self.skill_repo.unlink_skill_from_file(
            user_id=user_id,
            skill_id=skill_id,
            file_id=file_id,
        )

    async def link_skill_to_code_artifact(
        self,
        user_id: UUID,
        skill_id: int,
        code_artifact_id: int,
    ) -> dict:
        """Link a skill to a code artifact.

        Args:
            user_id: User ID for ownership verification
            skill_id: Skill to link
            code_artifact_id: Code artifact to link to

        Returns:
            Confirmation dict with linked IDs
        """
        await self.get_skill(user_id=user_id, skill_id=skill_id)

        return await self.skill_repo.link_skill_to_code_artifact(
            user_id=user_id,
            skill_id=skill_id,
            code_artifact_id=code_artifact_id,
        )

    async def unlink_skill_from_code_artifact(
        self,
        user_id: UUID,
        skill_id: int,
        code_artifact_id: int,
    ) -> dict:
        """Unlink a skill from a code artifact.

        Args:
            user_id: User ID for ownership verification
            skill_id: Skill to unlink
            code_artifact_id: Code artifact to unlink from

        Returns:
            Confirmation dict
        """
        await self.get_skill(user_id=user_id, skill_id=skill_id)

        return await self.skill_repo.unlink_skill_from_code_artifact(
            user_id=user_id,
            skill_id=skill_id,
            code_artifact_id=code_artifact_id,
        )

    async def link_skill_to_document(
        self,
        user_id: UUID,
        skill_id: int,
        document_id: int,
    ) -> dict:
        """Link a skill to a document.

        Args:
            user_id: User ID for ownership verification
            skill_id: Skill to link
            document_id: Document to link to

        Returns:
            Confirmation dict with linked IDs
        """
        await self.get_skill(user_id=user_id, skill_id=skill_id)

        return await self.skill_repo.link_skill_to_document(
            user_id=user_id,
            skill_id=skill_id,
            document_id=document_id,
        )

    async def unlink_skill_from_document(
        self,
        user_id: UUID,
        skill_id: int,
        document_id: int,
    ) -> dict:
        """Unlink a skill from a document.

        Args:
            user_id: User ID for ownership verification
            skill_id: Skill to unlink
            document_id: Document to unlink from

        Returns:
            Confirmation dict
        """
        await self.get_skill(user_id=user_id, skill_id=skill_id)

        return await self.skill_repo.unlink_skill_from_document(
            user_id=user_id,
            skill_id=skill_id,
            document_id=document_id,
        )

    async def get_skill_links(
        self,
        user_id: UUID,
        skill_id: int,
    ) -> SkillLinks:
        """Get IDs of all content linked to a skill (reverse lookup).

        Args:
            user_id: User ID for ownership verification
            skill_id: Skill to look up links for

        Returns:
            SkillLinks with memory, file, code artifact and document IDs

        Raises:
            NotFoundError: If skill not found or not owned by user
        """
        logger.info(
            "getting links for skill",
            extra={"skill_id": skill_id, "user_id": str(user_id)},
        )

        return await self.skill_repo.get_skill_links(
            user_id=user_id,
            skill_id=skill_id,
        )

    async def get_all_skill_file_links(
        self,
        user_id: UUID,
    ) -> list[tuple[int, int]]:
        """Get all skill-file links for graph visualization."""
        logger.info("getting all skill-file links for graph", extra={"user_id": str(user_id)})
        return await self.skill_repo.get_all_skill_file_links(user_id=user_id)

    async def get_all_skill_code_artifact_links(
        self,
        user_id: UUID,
    ) -> list[tuple[int, int]]:
        """Get all skill-code_artifact links for graph visualization."""
        logger.info("getting all skill-code_artifact links for graph", extra={"user_id": str(user_id)})
        return await self.skill_repo.get_all_skill_code_artifact_links(user_id=user_id)

    async def get_all_skill_document_links(
        self,
        user_id: UUID,
    ) -> list[tuple[int, int]]:
        """Get all skill-document links for graph visualization."""
        logger.info("getting all skill-document links for graph", extra={"user_id": str(user_id)})
        return await self.skill_repo.get_all_skill_document_links(user_id=user_id)
