"""Integration tests for the SKILL.md import/export YAML handling.

Covers frontmatter delimiting, body fidelity, YAML error handling, resource
limits and normalisation of imported values. All tests run against the real
SkillService with the in-memory skill repository.
"""
from uuid import uuid4

import pytest

from app.models.skill_models import SkillCreate


async def _roundtrip(service, **fields) -> tuple[str, object]:
    """Create a skill, export it, delete it, then import the exported markdown."""
    user_id = uuid4()
    payload = {
        "name": "round-trip",
        "description": "Round trip description",
        "content": "body",
        **fields,
    }
    created = await service.create_skill(user_id, SkillCreate(**payload))
    exported = await service.export_skill(user_id, created.id)
    await service.delete_skill(user_id, created.id)
    imported = await service.import_skill(user_id, exported)
    return exported, imported


def _md(frontmatter: str, body: str = "body") -> str:
    return f"---\n{frontmatter}\n---\n\n{body}\n"


# ---------------------------------------------------------------------------
# Frontmatter delimiting
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "description",
    [
        "text --- text",
        "Deploy --- fast: when you need it",
        "---",
    ],
)
async def test_roundtrip_keeps_dashes_inside_frontmatter_values(
    test_skill_service, description,
):
    exported, imported = await _roundtrip(
        test_skill_service,
        description=description,
        content="x",
        tags=["t:1"],
        metadata={"k": "v: w"},
    )

    assert imported.description == description, exported
    assert imported.content == "x"
    assert imported.tags == ["t:1"]
    assert imported.metadata == {"k": "v: w"}


async def test_import_hand_written_dashes_inside_value(test_skill_service):
    skill_md = "---\nname: hand-written\ndescription: Run a --- b step\n---\nbody text\n"

    skill = await test_skill_service.import_skill(uuid4(), skill_md)

    assert skill.description == "Run a --- b step"
    assert skill.content == "body text"


async def test_import_body_may_contain_horizontal_rules(test_skill_service):
    body = "intro\n\n---\n\nmiddle\n\n---\n\nend"

    skill = await test_skill_service.import_skill(
        uuid4(), _md("name: rules\ndescription: Has rules", body),
    )

    assert skill.content == body


@pytest.mark.parametrize(
    "skill_md",
    [
        "preface\n---\nname: x\ndescription: y\n---\nbody",
        "---\nname: x\ndescription: y\n--- not a delimiter\nbody",
        "---\nname: x\ndescription: y\n",
        "# no frontmatter",
        "",
    ],
    ids=["text-before-opening", "inline-closing-dashes", "unterminated", "none", "empty"],
)
async def test_import_requires_delimiter_lines(test_skill_service, skill_md):
    with pytest.raises(ValueError, match="between --- delimiters"):
        await test_skill_service.import_skill(uuid4(), skill_md)


@pytest.mark.parametrize(
    "newline",
    ["\n", "\r\n"],
    ids=["lf", "crlf"],
)
async def test_import_tolerates_bom_leading_blank_lines_and_crlf(
    test_skill_service, newline,
):
    skill_md = (
        "﻿\n  "
        + newline.join(["---", "name: tolerant", "description: Lenient parse", "---", "", "body", ""])
    )

    skill = await test_skill_service.import_skill(uuid4(), skill_md)

    assert skill.name == "tolerant"
    assert skill.description == "Lenient parse"
    assert skill.content == "body"


async def test_import_block_scalar_as_last_field_has_no_trailing_newline(
    test_skill_service,
):
    skill_md = "---\nname: block\ndescription: |\n  line one\n  line two\n---\nbody"

    skill = await test_skill_service.import_skill(uuid4(), skill_md)

    assert skill.description == "line one\nline two"


async def test_import_empty_frontmatter_raises_value_error(test_skill_service):
    with pytest.raises(ValueError, match="expected a mapping"):
        await test_skill_service.import_skill(uuid4(), "---\n---\nbody")


# ---------------------------------------------------------------------------
# Body fidelity
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "content",
    [
        "    code first\nmore",
        "\tindented with tab\nnext",
        "a\r\nb\r\n",
        "# Title\n\nbody\n\n\n",
        "\n\nleading blank lines",
        "plain",
    ],
    ids=["indent", "tab", "crlf", "trailing-newlines", "leading-newlines", "plain"],
)
async def test_roundtrip_preserves_body_exactly(test_skill_service, content):
    _, imported = await _roundtrip(test_skill_service, content=content)

    assert imported.content == content


@pytest.mark.parametrize(
    ("raw_body", "expected"),
    [
        ("body", "body"),
        ("body\n", "body"),
        ("\nbody\n", "body"),
        ("\r\nbody\r\n", "body"),
    ],
)
async def test_import_strips_only_separator_newlines(
    test_skill_service, raw_body, expected,
):
    skill_md = f"---\nname: sep\ndescription: Separator\n---\n{raw_body}"

    skill = await test_skill_service.import_skill(uuid4(), skill_md)

    assert skill.content == expected


async def test_import_whitespace_only_body_is_still_rejected(test_skill_service):
    with pytest.raises(ValueError):
        await test_skill_service.import_skill(
            uuid4(), "---\nname: empty\ndescription: No body\n---\n   \n",
        )
