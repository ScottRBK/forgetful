"""Unit tests for skill frontmatter scalar quoting helper."""
import yaml

from app.services.skill_service import _quote_unquoted_frontmatter_scalars


def test_quotes_unquoted_scalar_with_colon():
    raw = "description: Use when X. Keywords: foo, bar."
    quoted = _quote_unquoted_frontmatter_scalars(raw)
    parsed = yaml.safe_load(quoted)
    assert parsed["description"] == "Use when X. Keywords: foo, bar."


def test_leaves_already_quoted_scalar_unchanged():
    raw = 'description: "Use when X. Keywords: foo, bar."'
    assert _quote_unquoted_frontmatter_scalars(raw) == raw


def test_escapes_internal_double_quotes():
    raw = 'description: Say "hello" here: done.'
    quoted = _quote_unquoted_frontmatter_scalars(raw)
    parsed = yaml.safe_load(quoted)
    assert parsed["description"] == 'Say "hello" here: done.'


def test_skips_block_scalar_starter():
    raw = "summary: |\n  line one: value\n  line two"
    assert _quote_unquoted_frontmatter_scalars(raw) == raw


def test_skips_flow_sequence_starter():
    raw = "allowed-tools:\n  - Read"
    assert _quote_unquoted_frontmatter_scalars(raw) == raw


def test_skips_bracket_scalar_starter():
    raw = "tags: [one, two: three]"
    assert _quote_unquoted_frontmatter_scalars(raw) == raw


def test_preserves_indented_nested_mapping_lines():
    raw = (
        "description: Use when X. Keywords: foo, bar.\n"
        "metadata:\n"
        "  author: scottesh"
    )
    quoted = _quote_unquoted_frontmatter_scalars(raw)
    parsed = yaml.safe_load(quoted)
    assert parsed["description"] == "Use when X. Keywords: foo, bar."
    assert parsed["metadata"] == {"author": "scottesh"}
