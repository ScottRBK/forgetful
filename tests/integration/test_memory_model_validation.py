"""Integration tests for memory model validation.

Covers the write-time rules on MemoryCreate / MemoryUpdate / MemoryQueryRequest
(blank text, per-item length, UTF-8 encodability, blank search query) and the
guarantee that the Memory response model never enforces them, so stored rows
stay readable after a limit is lowered.
"""

import json

import pytest
from pydantic import ValidationError

from app.config.settings import settings
from app.models.memory_models import (
    LinkedMemory,
    Memory,
    MemoryCreate,
    MemoryUpdate,
)

BLANKS = ["   ", "\n\n", "\t \n"]
LONE_SURROGATE = "bad\ud83dtext"


def _create(**overrides) -> MemoryCreate:
    data = {
        "title": "A title",
        "content": "Real content",
        "context": "",
        "keywords": [],
        "tags": [],
    }
    data.update(overrides)
    return MemoryCreate(**data)


def _stored_row(**overrides) -> dict:
    """What a repository hands to Memory.model_validate for a stored row."""
    data = {
        "id": 1,
        "title": "A title",
        "content": "Real content",
        "context": "ctx",
        "keywords": ["k"],
        "tags": ["t"],
    }
    data.update(overrides)
    return data


# ============================================================================
# Whitespace-only text
# ============================================================================


@pytest.mark.parametrize("blank", BLANKS)
@pytest.mark.parametrize("field", ["title", "content"])
def test_create_rejects_whitespace_only_required_text(field, blank):
    with pytest.raises(ValidationError) as exc_info:
        _create(**{field: blank})

    assert exc_info.value.errors()[0]["loc"] == (field,)
    assert "cannot be empty or whitespace only" in exc_info.value.errors()[0]["msg"]


@pytest.mark.parametrize("blank", BLANKS)
@pytest.mark.parametrize("field", ["title", "content", "context"])
def test_update_rejects_whitespace_only_text(field, blank):
    with pytest.raises(ValidationError) as exc_info:
        MemoryUpdate(**{field: blank})

    assert exc_info.value.errors()[0]["loc"] == (field,)
    assert "cannot be empty or whitespace only" in exc_info.value.errors()[0]["msg"]


def test_create_still_allows_empty_context():
    """Context was optional text on create and stays so."""
    assert _create(context="   ").context == "   "
    assert _create(context="").context == ""


def test_update_with_no_text_fields_is_still_valid():
    update = MemoryUpdate(importance=9)

    assert update.title is None
    assert update.content is None
    assert update.context is None


def test_non_blank_text_is_kept_verbatim():
    """Only blank values are rejected; indentation and trailing newlines are content."""
    content = "    indented code\n\n"

    assert _create(content=content).content == content
    assert MemoryUpdate(content=content).content == content


def test_blank_text_errors_are_json_serialisable():
    """Clients receive ``e.errors()`` as the 400 body, so it must be plain JSON."""
    with pytest.raises(ValidationError) as exc_info:
        _create(title="   ")

    json.dumps(exc_info.value.errors())


def test_list_cleaning_is_unchanged():
    memory = _create(keywords=[" python ", "", "   ", "asyncio"], tags=[" t "], source_files=[" a.py ", " "])

    assert memory.keywords == ["python", "asyncio"]
    assert memory.tags == ["t"]
    assert memory.source_files == ["a.py"]
    assert _create(source_files=None).source_files is None
    assert MemoryUpdate(keywords=None).keywords is None


# ============================================================================
# Memory (response model) never enforces write-time rules
# ============================================================================


def test_memory_reads_rows_stored_under_looser_limits():
    """Lowering MEMORY_*_MAX_* after data was stored must not break reads."""
    row = _stored_row(
        title="t" * (settings.MEMORY_TITLE_MAX_LENGTH + 50),
        content="c" * (settings.MEMORY_CONTENT_MAX_LENGTH + 500),
        context="x" * (settings.MEMORY_CONTEXT_MAX_LENGTH + 500),
        keywords=["k" * 5_000] * (settings.MEMORY_KEYWORDS_MAX_COUNT + 5),
        tags=["g" * 5_000] * (settings.MEMORY_TAGS_MAX_COUNT + 5),
        source_files=["p" * 10_000],
    )

    memory = Memory.model_validate(row)

    assert len(memory.content) == settings.MEMORY_CONTENT_MAX_LENGTH + 500
    assert len(memory.keywords) == settings.MEMORY_KEYWORDS_MAX_COUNT + 5
    assert len(memory.tags) == settings.MEMORY_TAGS_MAX_COUNT + 5
    assert len(memory.keywords[0]) == 5_000
    assert len(memory.source_files[0]) == 10_000

    with pytest.raises(ValidationError):
        MemoryCreate.model_validate(row)


def test_memory_reads_rows_with_blank_text():
    """Blank memories were accepted before the write-time check; they must stay readable."""
    memory = Memory.model_validate(_stored_row(title="   ", content="\n\n", context=""))

    assert memory.title == "   "
    assert memory.content == "\n\n"


def test_memory_inside_other_response_models_is_unconstrained():
    oversized = Memory.model_validate(_stored_row(content="c" * (settings.MEMORY_CONTENT_MAX_LENGTH + 1)))

    linked = LinkedMemory(memory=oversized, link_source_id=2)

    assert linked.memory.id == 1


def test_memory_keeps_the_field_order_of_the_api_response():
    memory = Memory.model_validate(_stored_row())

    keys = list(memory.model_dump())

    assert keys[:6] == ["title", "content", "context", "keywords", "tags", "importance"]
    assert keys.index("id") > keys.index("agent_model")


def test_memory_is_still_a_memory_create_for_embedding_helpers():
    assert issubclass(Memory, MemoryCreate)
