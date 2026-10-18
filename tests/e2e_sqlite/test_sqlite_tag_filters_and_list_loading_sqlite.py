"""E2E tests (service -> repository -> in-memory SQLite) for JSON tag filters.

The SQLite ``tags`` filter of the document, code artifact, file and skill
listings must be an exact, case-sensitive array membership test (the same
contract as the PostgreSQL ``&&`` overlap): non-ASCII tags are found and
``%``/``_``/quote characters in the filter have no special meaning.

Runs fully offline: skills use a deterministic stub embedding adapter.
"""
import base64
import hashlib
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from uuid import uuid4

import pytest

from app.config.settings import settings
from app.models.code_artifact_models import CodeArtifactCreate
from app.models.document_models import DocumentCreate
from app.models.file_models import FileCreate
from app.models.skill_models import SkillCreate
from app.models.user_models import UserCreate
from app.repositories.sqlite.code_artifact_repository import (
    SqliteCodeArtifactRepository,
)
from app.repositories.sqlite.document_repository import SqliteDocumentRepository
from app.repositories.sqlite.file_repository import SqliteFileRepository
from app.repositories.sqlite.skill_repository import SqliteSkillRepository
from app.repositories.sqlite.sqlite_adapter import SqliteDatabaseAdapter
from app.repositories.sqlite.user_repository import SqliteUserRepository
from app.services.code_artifact_service import CodeArtifactService
from app.services.document_service import DocumentService
from app.services.file_service import FileService
from app.services.skill_service import SkillService

EMBEDDING_DIMENSIONS = 384


class StaticEmbeddingAdapter:
    """Deterministic offline embedding adapter (skills embed on create)."""

    async def generate_embedding(self, text: str) -> list[float]:
        seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)  # noqa: S324
        rng = random.Random(seed)  # noqa: S311
        vec = [rng.random() for _ in range(EMBEDDING_DIMENSIONS)]
        magnitude = sum(x * x for x in vec) ** 0.5 or 1.0
        return [x / magnitude for x in vec]


@dataclass
class Stack:
    """Service layer wired to a real in-memory SQLite database."""

    adapter: SqliteDatabaseAdapter
    user_id: object
    documents: DocumentService
    artifacts: CodeArtifactService
    files: FileService
    skills: SkillService


@pytest.fixture
async def stack():
    original = (
        settings.DATABASE,
        settings.SQLITE_MEMORY,
        settings.EMBEDDING_DIMENSIONS,
    )
    settings.DATABASE = "SQLite"
    settings.SQLITE_MEMORY = True
    settings.EMBEDDING_DIMENSIONS = EMBEDDING_DIMENSIONS

    adapter = SqliteDatabaseAdapter()
    await adapter.init_db()
    try:
        user = await SqliteUserRepository(db_adapter=adapter).create_user(
            UserCreate(
                external_id=f"ext-{uuid4()}",
                name="Tag Filter Tester",
                email="tags@example.com",
            ),
        )
        yield Stack(
            adapter=adapter,
            user_id=user.id,
            documents=DocumentService(
                SqliteDocumentRepository(db_adapter=adapter), event_bus=None,
            ),
            artifacts=CodeArtifactService(
                SqliteCodeArtifactRepository(db_adapter=adapter), event_bus=None,
            ),
            files=FileService(
                SqliteFileRepository(db_adapter=adapter), event_bus=None,
            ),
            skills=SkillService(
                SqliteSkillRepository(
                    db_adapter=adapter,
                    embedding_adapter=StaticEmbeddingAdapter(),
                    rerank_adapter=None,
                ),
                event_bus=None,
            ),
        )
    finally:
        try:
            await adapter.dispose()
        except Exception:  # noqa: BLE001
            pass
        (
            settings.DATABASE,
            settings.SQLITE_MEMORY,
            settings.EMBEDDING_DIMENSIONS,
        ) = original


@dataclass
class Kind:
    """Uniform create/list access to one taggable resource type."""

    create: Callable[[str, list[str]], Awaitable[None]]
    list_labels: Callable[[list[str]], Awaitable[set[str]]]


def _build_kind(name: str, stack: Stack) -> Kind:
    uid = stack.user_id

    if name == "document":
        async def create(label: str, tags: list[str]) -> None:
            await stack.documents.create_document(
                uid,
                DocumentCreate(
                    title=label, description="d", content="c", tags=tags,
                ),
            )

        async def list_labels(tags: list[str]) -> set[str]:
            found = await stack.documents.list_documents(uid, tags=tags)
            return {d.title for d in found}

    elif name == "code_artifact":
        async def create(label: str, tags: list[str]) -> None:
            await stack.artifacts.create_code_artifact(
                uid,
                CodeArtifactCreate(
                    title=label,
                    description="d",
                    code="print(1)",
                    language="python",
                    tags=tags,
                ),
            )

        async def list_labels(tags: list[str]) -> set[str]:
            found = await stack.artifacts.list_code_artifacts(uid, tags=tags)
            return {a.title for a in found}

    elif name == "file":
        async def create(label: str, tags: list[str]) -> None:
            await stack.files.create_file(
                uid,
                FileCreate(
                    filename=label,
                    description="d",
                    data=base64.b64encode(b"payload").decode(),
                    mime_type="text/plain",
                    tags=tags,
                ),
            )

        async def list_labels(tags: list[str]) -> set[str]:
            found = await stack.files.list_files(uid, tags=tags)
            return {f.filename for f in found}

    else:
        async def create(label: str, tags: list[str]) -> None:
            await stack.skills.create_skill(
                uid,
                SkillCreate(
                    name=label, description="d", content="c", tags=tags,
                ),
            )

        async def list_labels(tags: list[str]) -> set[str]:
            found = await stack.skills.list_skills(uid, tags=tags)
            return {s.name for s in found}

    return Kind(create=create, list_labels=list_labels)


@pytest.fixture(
    params=["document", "code_artifact", "file", "skill"],
)
def kind(request, stack: Stack) -> Kind:
    return _build_kind(request.param, stack)


# ---------------------------------------------------------------------------
# Tag filter semantics
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("tag", ["café", "日本語", "Zoë"])
async def test_non_ascii_tag_is_found(kind: Kind, tag: str):
    await kind.create("tagged", [tag, "plain"])
    await kind.create("other", ["unrelated"])

    assert await kind.list_labels([tag]) == {"tagged"}


async def test_underscore_in_filter_is_not_a_wildcard(kind: Kind):
    await kind.create("hyphen", ["bug-fix"])
    await kind.create("underscore", ["bug_fix"])

    assert await kind.list_labels(["bug_fix"]) == {"underscore"}


async def test_percent_in_filter_is_not_a_wildcard(kind: Kind):
    await kind.create("a", ["alpha"])
    await kind.create("b", ["beta"])
    await kind.create("pct", ["100%"])

    assert await kind.list_labels(["%"]) == set()
    assert await kind.list_labels(["100%"]) == {"pct"}


async def test_quote_in_filter_cannot_span_array_elements(kind: Kind):
    await kind.create("pair", ["alpha", "beta"])

    assert await kind.list_labels(['alpha","beta']) == set()
    assert await kind.list_labels(["alpha"]) == {"pair"}


async def test_tags_with_quote_and_backslash_are_filterable(kind: Kind):
    await kind.create("pipe", ['5" pipe'])
    await kind.create("path", ["a\\b"])

    assert await kind.list_labels(['5" pipe']) == {"pipe"}
    assert await kind.list_labels(["a\\b"]) == {"path"}


async def test_tag_match_is_case_sensitive_like_postgres(kind: Kind):
    await kind.create("upper", ["Python"])

    assert await kind.list_labels(["python"]) == set()
    assert await kind.list_labels(["Python"]) == {"upper"}


async def test_any_of_several_tags_matches_and_untagged_never_does(kind: Kind):
    await kind.create("one", ["one"])
    await kind.create("two", ["two", "extra"])
    await kind.create("three", ["three"])
    await kind.create("untagged", [])

    assert await kind.list_labels(["one", "two"]) == {"one", "two"}
    assert await kind.list_labels(["missing", "three"]) == {"three"}
    assert await kind.list_labels(["missing"]) == set()
