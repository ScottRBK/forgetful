"""Integration tests for the SKILL.md import/export YAML handling.

Covers frontmatter delimiting, body fidelity, YAML error handling, resource
limits and normalisation of imported values. All tests run against the real
SkillService with the in-memory skill repository.
"""
import time
from uuid import uuid4

import pytest
import yaml

from app.models.skill_models import SkillCreate
from app.services.skill_service import (
    _quote_unquoted_frontmatter_scalars,
)


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


# ---------------------------------------------------------------------------
# Folded / commented / unicode frontmatter values
# ---------------------------------------------------------------------------


async def test_roundtrip_long_description_with_url(test_skill_service):
    description = (
        "See https://example.com/docs/guide for details and use this skill "
        "whenever the user asks about the complete workflow of deployments"
    )
    compatibility = (
        "Requires network access to https://pypi.org/simple and a recent "
        "interpreter with the packaging tools installed locally"
    )

    exported, imported = await _roundtrip(
        test_skill_service, description=description, compatibility=compatibility,
    )

    assert "\n  " in exported  # long plain scalars are folded by the dumper
    assert imported.description == description
    assert imported.compatibility == compatibility


@pytest.mark.parametrize("char", [" ", " "])
async def test_roundtrip_preserves_unicode_line_separators(test_skill_service, char):
    description = f"aa{char}bb"

    _, imported = await _roundtrip(
        test_skill_service,
        description=description,
        tags=[f"t{char}1"],
        metadata={"k": f"v{char}w"},
    )

    assert imported.description == description
    assert imported.tags == [f"t{char}1"]
    assert imported.metadata == {"k": f"v{char}w"}


async def test_import_quoted_value_with_unicode_separator_is_untouched(
    test_skill_service,
):
    skill_md = _md('name: sep-char\ndescription: "line one line two"')

    skill = await test_skill_service.import_skill(uuid4(), skill_md)

    assert skill.description == "line one line two"


async def test_fallback_quoting_keeps_unicode_separator_in_other_lines(
    test_skill_service,
):
    skill_md = _md(
        "name: fallback\n"
        "description: Use when X. Keywords: foo, bar.\n"
        'license: "MIT or Apache"',
    )

    skill = await test_skill_service.import_skill(uuid4(), skill_md)

    assert skill.description == "Use when X. Keywords: foo, bar."
    assert skill.license == "MIT or Apache"


@pytest.mark.parametrize(
    ("frontmatter", "expected"),
    [
        (
            "name: my-skill  # note: slug used in URLs\ndescription: Does things",
            {"name": "my-skill", "description": "Does things"},
        ),
        (
            "name: lic\ndescription: d\nlicense: MIT # see: LICENSE file",
            {"license": "MIT"},
        ),
        (
            "name: meta\ndescription: d\nmetadata: # optional: key-value pairs\n  author: me",
            {"metadata": {"author": "me"}},
        ),
        (
            "name: tools\ndescription: d\nallowed-tools: # tools: whitelisted\n  - Read",
            {"allowed_tools": ["Read"]},
        ),
        (
            "name: both\ndescription: Use when X. Keywords: foo # note: bar",
            {"description": "Use when X. Keywords: foo"},
        ),
    ],
    ids=["name", "license", "metadata", "allowed-tools", "colon-value-and-comment"],
)
async def test_import_ignores_trailing_comments_containing_colons(
    test_skill_service, frontmatter, expected,
):
    skill = await test_skill_service.import_skill(uuid4(), _md(frontmatter))

    for field, value in expected.items():
        assert getattr(skill, field) == value


def test_quoting_helper_keeps_comment_out_of_quoted_value():
    quoted = _quote_unquoted_frontmatter_scalars(
        "description: Use when X. Keywords: foo # trailing: note",
    )

    assert yaml.safe_load(quoted) == {"description": "Use when X. Keywords: foo"}


def test_quoting_helper_leaves_comment_only_values_unchanged():
    raw = "metadata: # optional: key-value pairs\n  author: me"

    assert _quote_unquoted_frontmatter_scalars(raw) == raw


def test_quoting_helper_does_not_split_on_unicode_line_separators():
    raw = "name: x\ndescription: 'aa   bb'\nnote: 'c d\u0085e'"

    assert _quote_unquoted_frontmatter_scalars(raw) == raw


# ---------------------------------------------------------------------------
# YAML errors become ValueError
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "description",
    [
        "[WIP] deploy things",
        "`deploy` things",
        "@deploy things",
        "*bold* deploy things",
        "!important deploy things",
    ],
    ids=["bracket", "backtick", "at", "alias", "tag"],
)
async def test_malformed_yaml_raises_value_error(test_skill_service, description):
    skill_md = _md(f"name: broken\ndescription: {description}")

    with pytest.raises(ValueError, match="Invalid YAML frontmatter"):
        await test_skill_service.import_skill(uuid4(), skill_md)


async def test_malformed_yaml_with_fixable_line_reports_remaining_error(
    test_skill_service,
):
    skill_md = _md("name: broken\ndescription: Keywords: a, b\nlicense: [MIT] or later")

    with pytest.raises(ValueError, match="Invalid YAML frontmatter"):
        await test_skill_service.import_skill(uuid4(), skill_md)


# ---------------------------------------------------------------------------
# Resource limits
# ---------------------------------------------------------------------------


def _alias_bomb(levels: int) -> str:
    lines = [
        "name: alias-bomb",
        "description: harmless looking skill",
        "a0: &a0 [" + ",".join(["x"] * 10) + "]",
    ]
    for i in range(1, levels):
        lines.append(f"a{i}: &a{i} [" + ",".join([f"*a{i - 1}"] * 10) + "]")
    lines.append(f"metadata: {{k: *a{levels - 1}}}")
    return _md("\n".join(lines))


async def test_alias_bomb_is_rejected_quickly(test_skill_service):
    skill_md = _alias_bomb(8)
    assert len(skill_md) < 600

    started = time.perf_counter()
    with pytest.raises(ValueError, match="aliases"):
        await test_skill_service.import_skill(uuid4(), skill_md)

    assert time.perf_counter() - started < 1.0


async def test_oversized_frontmatter_is_rejected(test_skill_service):
    padding = "\n".join(f"    key{i}: {'v' * 60}" for i in range(400))
    skill_md = _md(f"name: huge\ndescription: Too much metadata\nmetadata:\n  pad: |\n{padding}")

    with pytest.raises(ValueError, match="too large"):
        await test_skill_service.import_skill(uuid4(), skill_md)


async def test_deeply_nested_frontmatter_raises_value_error(test_skill_service):
    nested = "[" * 3000 + "]" * 3000
    skill_md = _md(f"name: deep\ndescription: d\nmetadata: {{k: {nested}}}")

    with pytest.raises(ValueError, match="Invalid YAML frontmatter"):
        await test_skill_service.import_skill(uuid4(), skill_md)


async def test_anchor_without_alias_is_still_accepted(test_skill_service):
    skill_md = _md("name: anchored\ndescription: &d Anchor only")

    skill = await test_skill_service.import_skill(uuid4(), skill_md)

    assert skill.description == "Anchor only"


# ---------------------------------------------------------------------------
# Normalisation of imported values
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Read Write", ["Read", "Write"]),
        ("Bash(git:*) Read", ["Bash(git:*)", "Read"]),
        ("Read, Write,Grep", ["Read", "Write", "Grep"]),
        ("Bash(git commit:*) Read", ["Bash(git commit:*)", "Read"]),
        ("Bash(a, b:*)  Read", ["Bash(a, b:*)", "Read"]),
        ("  Read  ", ["Read"]),
        ('""', []),
    ],
    ids=["spaces", "parens", "commas", "space-in-parens", "comma-in-parens", "padding", "empty"],
)
async def test_import_splits_string_form_allowed_tools(
    test_skill_service, value, expected,
):
    skill_md = _md(f"name: at-skill\ndescription: ok\nallowed-tools: {value}")

    skill = await test_skill_service.import_skill(uuid4(), skill_md)

    assert skill.allowed_tools == expected


async def test_import_keeps_list_form_allowed_tools(test_skill_service):
    skill_md = _md("name: at-list\ndescription: ok\nallowed-tools:\n  - Bash(git commit:*)\n  - Read")

    skill = await test_skill_service.import_skill(uuid4(), skill_md)

    assert skill.allowed_tools == ["Bash(git commit:*)", "Read"]


async def test_import_keeps_timestamps_as_text(test_skill_service):
    skill_md = _md(
        "name: sk-date\n"
        "description: 2024-01-15\n"
        "metadata:\n"
        "  updated: 2024-01-15\n"
        "  stamp: 2024-01-15 10:00:00\n"
        "  zulu: 2024-01-15T10:00:00Z\n"
        "  nested:\n"
        "    - 2024-02-01\n"
        "  2024-03-01: key",
    )

    skill = await test_skill_service.import_skill(uuid4(), skill_md)

    assert skill.description == "2024-01-15"
    assert skill.metadata == {
        "updated": "2024-01-15",
        "stamp": "2024-01-15 10:00:00",
        "zulu": "2024-01-15T10:00:00Z",
        "nested": ["2024-02-01"],
        "2024-03-01": "key",
    }


@pytest.mark.parametrize(
    "value",
    ["!!set {a, b}", "!!binary aGVsbG8=", ".nan", ".inf", "-.inf", "[1, .nan]", "{n: .Inf}"],
    ids=["set", "binary", "nan", "inf", "neg-inf", "nan-in-list", "inf-in-mapping"],
)
async def test_import_rejects_non_json_metadata(test_skill_service, value):
    skill_md = _md(f"name: odd-meta\ndescription: d\nmetadata:\n  k: {value}")

    with pytest.raises(ValueError, match="metadata"):
        await test_skill_service.import_skill(uuid4(), skill_md)


async def test_import_export_roundtrip_keeps_native_scalars(test_skill_service):
    _, imported = await _roundtrip(
        test_skill_service,
        metadata={"count": 3, "ratio": 1.5, "flag": True, "none": None, "list": [1, "a"]},
        allowed_tools=["Bash(git commit:*)", "Read"],
        license="MIT",
        compatibility="Python 3.12+",
    )

    assert imported.metadata == {
        "count": 3, "ratio": 1.5, "flag": True, "none": None, "list": [1, "a"],
    }
    assert imported.allowed_tools == ["Bash(git commit:*)", "Read"]
    assert imported.license == "MIT"
    assert imported.compatibility == "Python 3.12+"
