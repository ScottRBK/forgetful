"""Integration tests for memory model validation.

Covers the write-time rules on MemoryCreate / MemoryUpdate / MemoryQueryRequest
(blank text, per-item length, UTF-8 encodability, blank search query) and the
guarantee that the Memory response model never enforces them, so stored rows
stay readable after a limit is lowered.
"""

import json
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.config.settings import settings
from app.models.memory_models import (
    LinkedMemory,
    Memory,
    MemoryCreate,
    MemoryQueryRequest,
    MemoryUpdate,
)
from app.models.skill_models import SkillCreate

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


# ============================================================================
# Per-item length of keywords, tags and source_files
# ============================================================================

ITEM_LIMITS = [
    ("keywords", settings.MEMORY_KEYWORD_MAX_LENGTH),
    ("tags", settings.MEMORY_TAG_MAX_LENGTH),
    ("source_files", settings.MEMORY_SOURCE_FILE_MAX_LENGTH),
]


@pytest.mark.parametrize(("field", "limit"), ITEM_LIMITS)
def test_create_rejects_item_over_limit(field, limit):
    oversized = "a" * (limit + 1)

    with pytest.raises(ValidationError) as exc_info:
        _create(**{field: [oversized]})

    assert exc_info.value.errors()[0]["loc"][0] == field
    assert oversized not in str(exc_info.value)


@pytest.mark.parametrize(("field", "limit"), ITEM_LIMITS)
def test_update_rejects_item_over_limit(field, limit):
    with pytest.raises(ValidationError) as exc_info:
        MemoryUpdate(**{field: ["a" * (limit + 1)]})

    assert exc_info.value.errors()[0]["loc"][0] == field


@pytest.mark.parametrize(("field", "limit"), ITEM_LIMITS)
def test_item_at_limit_is_accepted_and_padding_does_not_count(field, limit):
    exact = "a" * limit
    padded = f"  {exact}\n"

    assert getattr(_create(**{field: [exact]}), field) == [exact]
    assert getattr(_create(**{field: [padded]}), field) == [exact]
    assert getattr(MemoryUpdate(**{field: [padded]}), field) == [exact]


def test_huge_keyword_is_rejected_before_any_token_counting():
    """A 1 MB keyword used to be accepted and later stalled query_memory."""
    with pytest.raises(ValidationError) as exc_info:
        _create(keywords=["a" * 1_000_000])

    json.dumps(exc_info.value.errors())


def test_list_cleaning_is_unchanged():
    memory = _create(keywords=[" python ", "", "   ", "asyncio"], tags=[" t "], source_files=[" a.py ", " "])

    assert memory.keywords == ["python", "asyncio"]
    assert memory.tags == ["t"]
    assert memory.source_files == ["a.py"]
    assert _create(source_files=None).source_files is None
    assert MemoryUpdate(keywords=None).keywords is None


# ============================================================================
# Strings that cannot be encoded as UTF-8
# ============================================================================

UNENCODABLE_LIST_FIELDS = [
    {"keywords": [LONE_SURROGATE]},
    {"tags": [LONE_SURROGATE]},
    {"source_files": [f"src/{LONE_SURROGATE}.py"]},
]
# Plain str fields are already rejected by pydantic itself; pinned here so the whole
# model keeps rejecting unencodable text if pydantic ever stops doing so.
UNENCODABLE_TEXT_FIELDS = [
    {"title": LONE_SURROGATE},
    {"content": LONE_SURROGATE},
    {"context": LONE_SURROGATE},
    {"source_repo": LONE_SURROGATE},
    {"source_url": LONE_SURROGATE},
    {"encoding_agent": LONE_SURROGATE},
    {"agent_id": LONE_SURROGATE},
]


@pytest.mark.parametrize("overrides", UNENCODABLE_LIST_FIELDS, ids=lambda o: next(iter(o)))
def test_list_items_reject_lone_surrogates(overrides):
    """A lone surrogate in a JSON column used to be stored and then broke every response."""
    field = next(iter(overrides))
    for build in (_create, lambda **kw: MemoryUpdate(**kw)):
        with pytest.raises(ValidationError) as exc_info:
            build(**overrides)

        error = exc_info.value.errors()[0]
        assert error["loc"][0] == field
        assert error["type"] == "unencodable_text"
        assert "cannot be encoded as UTF-8" in error["msg"]
        json.dumps(exc_info.value.errors())


@pytest.mark.parametrize("overrides", UNENCODABLE_TEXT_FIELDS, ids=lambda o: next(iter(o)))
def test_text_fields_reject_lone_surrogates(overrides):
    with pytest.raises(ValidationError):
        _create(**overrides)
    with pytest.raises(ValidationError):
        MemoryUpdate(**overrides)


def test_valid_non_ascii_and_astral_text_is_accepted():
    """Surrogate *pairs* decode to real characters and must keep working."""
    text = "naive cafe é 日本語 \U0001f600"
    memory = _create(title=text, content=text, keywords=[text], tags=["\U0001f600"], source_files=[text])

    assert memory.title == text
    assert memory.keywords == [text]
    assert json.loads('{"v": "\\ud83d\\ude00"}')["v"] == "\U0001f600"
    assert _create(content=json.loads('{"v": "\\ud83d\\ude00"}')["v"]).content == "\U0001f600"


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


# ============================================================================
# Search query
# ============================================================================


def _query(**overrides) -> MemoryQueryRequest:
    data = {"query": "python logging", "query_context": "why I am searching"}
    data.update(overrides)
    return MemoryQueryRequest(**data)


@pytest.mark.parametrize("blank", BLANKS)
def test_query_rejects_whitespace_only(blank):
    with pytest.raises(ValidationError) as exc_info:
        _query(query=blank)

    assert exc_info.value.errors()[0]["loc"] == ("query",)
    assert "cannot be empty or whitespace only" in exc_info.value.errors()[0]["msg"]
    json.dumps(exc_info.value.errors())


def test_query_rejects_lone_surrogates():
    with pytest.raises(ValidationError):
        _query(query=LONE_SURROGATE)
    with pytest.raises(ValidationError):
        _query(query_context=LONE_SURROGATE)


def test_query_accepts_normal_text_verbatim():
    assert _query(query="  python logging  ").query == "  python logging  "


async def test_skill_search_rejects_blank_query(test_skill_service):
    user_id = uuid4()
    await test_skill_service.create_skill(
        user_id,
        SkillCreate(name="pdf-extract", description="Extract text from PDF", content="body", tags=["pdf"]),
    )

    for blank in BLANKS:
        with pytest.raises(ValueError, match="cannot be empty or whitespace only"):
            await test_skill_service.search_skills(user_id, query=blank)

    assert [s.name for s in await test_skill_service.search_skills(user_id, query="PDF")] == ["pdf-extract"]
