"""Shared canonical Agent Skills Markdown parsing and formatting."""
import json
import re

import yaml

from app.models.skill_models import Skill, SkillCreate


class _SkillFrontmatterLoader(yaml.SafeLoader):
    """Keep safe YAML construction without references that expand during JSON storage."""

    def compose_node(
        self, parent: yaml.Node | None, index: int | yaml.Node | None,
    ) -> yaml.Node:
        if self.check_event(yaml.AliasEvent):
            raise ValueError(
                "YAML references are not supported in skill frontmatter. "
                "Write the values directly instead.",
            )
        return super().compose_node(parent, index)


def _quote_unquoted_frontmatter_scalars(raw: str) -> str:
    """Quote scalar frontmatter values that contain unescaped colons."""
    quoted_lines: list[str] = []
    for line in raw.splitlines():
        match = re.match(r"^([A-Za-z0-9_-]+):\s+(.*)$", line)
        if not match:
            quoted_lines.append(line)
            continue

        key, value = match.group(1), match.group(2)
        if not value:
            quoted_lines.append(line)
            continue

        stripped = value.lstrip()
        if stripped.startswith(("[", "{", "|", ">", '"', "'")):
            quoted_lines.append(line)
            continue

        if ":" in value:
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            quoted_lines.append(f'{key}: "{escaped}"')
        else:
            quoted_lines.append(line)

    return "\n".join(quoted_lines)



def parse_skill_markdown(skill_md_content: str, project_id: int | None, importance: int) -> SkillCreate:
    # Parse YAML frontmatter between --- delimiters
    parts = skill_md_content.split("---", 2)
    if len(parts) < 3:
        raise ValueError(
            "Invalid skill markdown: expected YAML frontmatter between --- delimiters",
        )

    frontmatter_raw = parts[1].strip()
    body = parts[2].strip()

    frontmatter = yaml.load(
        _quote_unquoted_frontmatter_scalars(frontmatter_raw),
        Loader=_SkillFrontmatterLoader,  # noqa: S506 - SafeLoader subclass rejects aliases.
    )
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

    return skill_data


def format_skill_markdown(skill: Skill | SkillCreate) -> str:
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



def _sorted_metadata(value):
    """Sort JSON-compatible mappings without changing list order."""
    if isinstance(value, dict):
        return {key: _sorted_metadata(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_sorted_metadata(item) for item in value]
    return value


def format_bundle_skill_markdown(skill: Skill | SkillCreate) -> str:
    """Canonical bundle output independent of JSON/JSONB ordering and defaults."""
    metadata = _sorted_metadata(json.loads(json.dumps(skill.metadata)))
    canonical = skill.model_copy(update={
        "metadata": metadata,
        "allowed_tools": skill.allowed_tools or None,
    })
    return format_skill_markdown(canonical)
