"""Re-embedding service for batch migration of memory embeddings.

Orchestrates the workflow of re-embedding all memories with the currently
configured embedding provider. Knows nothing about SQLite/PostgreSQL specifics.
"""
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from uuid import UUID

from app.protocols.memory_protocol import MemoryRepository, ValidationResult
from app.repositories.embeddings.embedding_adapter import EmbeddingsAdapter
from app.repositories.helpers import build_embedding_text

logger = logging.getLogger(__name__)


@dataclass
class ReEmbedResult:
    """Result of a re-embedding operation"""
    total_processed: int
    total_memories: int
    validation: ValidationResult | None = None


@dataclass
class TargetedRebuildResult:
    """Outcome of a user-scoped, targeted `rebuild_embeddings` call.

    Distinguishes successful rebuilds from skipped (not owned / no-op) and
    failed (embedding generation or write error) memories so callers can
    surface partial success without re-running the whole rebuild.
    """
    total_candidates: int = 0
    rebuilt_ids: list[int] = field(default_factory=list)
    skipped_ids: list[int] = field(default_factory=list)
    failed: list[dict] = field(default_factory=list)


class ReEmbeddingService:
    """Orchestrates batch re-embedding of all memories"""

    def __init__(
        self,
        memory_repository: MemoryRepository,
        embedding_adapter: EmbeddingsAdapter,
        batch_size: int = 20,
    ):
        self.memory_repository = memory_repository
        self.embedding_adapter = embedding_adapter
        self.batch_size = batch_size

    async def re_embed_all(
        self,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> ReEmbedResult:
        """Orchestrate: count -> reset schema -> batch re-embed -> validate

        Args:
            progress_callback: Optional callback(processed, total) called after each batch

        Returns:
            ReEmbedResult with counts and validation status
        """
        total = await self.memory_repository.count_all_memories()
        logger.info("Starting re-embedding", extra={"total_memories": total})

        if total == 0:
            logger.info("No memories to re-embed")
            return ReEmbedResult(
                total_processed=0,
                total_memories=0,
                validation=ValidationResult(count_ok=True, dimensions_ok=True, search_ok=True),
            )

        # Reset vector storage for new dimensions
        await self.memory_repository.reset_embedding_storage()

        processed = 0
        for offset in range(0, total, self.batch_size):
            memories = await self.memory_repository.get_memories_for_reembedding(
                limit=self.batch_size, offset=offset,
            )

            if not memories:
                break

            # Generate embeddings for this batch
            updates: list[tuple[int, list[float]]] = []
            for memory in memories:
                embedding_text = build_embedding_text(memory)
                embedding = await self.embedding_adapter.generate_embedding(embedding_text)
                updates.append((memory.id, embedding))

            # Write batch
            await self.memory_repository.bulk_update_embeddings(updates)

            processed += len(memories)
            if progress_callback:
                progress_callback(processed, total)

            logger.info("Batch complete", extra={
                "processed": processed,
                "total": total,
                "batch_size": len(memories),
            })

        # Validate
        validation = await self.validate()

        return ReEmbedResult(
            total_processed=processed,
            total_memories=total,
            validation=validation,
        )

    async def rebuild_targeted(
        self,
        user_id: UUID,
        memory_ids: list[int] | None = None,
        project_id: int | None = None,
        only_missing: bool = True,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> TargetedRebuildResult:
        """User-scoped, *non-destructive* embedding rebuild for a memory subset.

        Unlike `re_embed_all`, this method:
        - never calls `reset_embedding_storage()`,
        - operates only on memories owned by `user_id`,
        - reuses the existing embedding pipeline (`build_embedding_text` +
          `EmbeddingsAdapter.generate_embedding`) so embeddings stay
          dimensionally consistent with the rest of the corpus.

        Args:
            user_id: Authenticated user id; ownership filter, never optional.
            memory_ids: Restrict to explicit memory ids (already user-scoped).
            project_id: Restrict to a single project owned by `user_id`.
            only_missing: When True (default), only memories without an
                embedding are touched; when False, every matching memory is
                rebuilt with a fresh embedding.
            progress_callback: Optional `(processed, total)` callback per batch.

        Returns:
            `TargetedRebuildResult` with per-memory outcome lists.
        """
        total = await self.memory_repository.count_memories_for_targeted_rebuild(
            user_id=user_id,
            memory_ids=memory_ids,
            project_id=project_id,
            only_missing=only_missing,
        )
        result = TargetedRebuildResult(total_candidates=total)
        if total == 0:
            logger.info(
                "rebuild_embeddings: no candidates",
                extra={
                    "user_id": str(user_id),
                    "memory_ids": memory_ids,
                    "project_id": project_id,
                    "only_missing": only_missing,
                },
            )
            return result

        processed = 0
        for offset in range(0, total, self.batch_size):
            memories = await self.memory_repository.get_memories_for_targeted_rebuild(
                user_id=user_id,
                limit=self.batch_size,
                offset=offset,
                memory_ids=memory_ids,
                project_id=project_id,
                only_missing=only_missing,
            )
            if not memories:
                break

            updates: list[tuple[int, list[float]]] = []
            for memory in memories:
                try:
                    embedding_text = build_embedding_text(memory)
                    embedding = await self.embedding_adapter.generate_embedding(embedding_text)
                    updates.append((memory.id, embedding))
                except Exception as exc:  # noqa: BLE001 - intentional broad capture
                    logger.exception("rebuild_embeddings: embedding failed", extra={
                        "memory_id": memory.id,
                        "user_id": str(user_id),
                    })
                    result.failed.append({"memory_id": memory.id, "reason": str(exc)})

            if updates:
                try:
                    written_ids = await self.memory_repository.upsert_targeted_embeddings(
                        user_id=user_id,
                        updates=updates,
                    )
                    written_set = set(written_ids)
                    result.rebuilt_ids.extend(written_ids)
                    for memory_id, _ in updates:
                        if memory_id not in written_set:
                            result.skipped_ids.append(memory_id)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("rebuild_embeddings: persistence failed", extra={
                        "user_id": str(user_id),
                        "batch_size": len(updates),
                    })
                    for memory_id, _ in updates:
                        result.failed.append({"memory_id": memory_id, "reason": str(exc)})

            processed += len(memories)
            if progress_callback:
                progress_callback(processed, total)

        logger.info(
            "rebuild_embeddings: done",
            extra={
                "user_id": str(user_id),
                "rebuilt": len(result.rebuilt_ids),
                "skipped": len(result.skipped_ids),
                "failed": len(result.failed),
                "total_candidates": result.total_candidates,
                "only_missing": only_missing,
            },
        )
        return result

    async def validate(self) -> ValidationResult:
        """Post-migration validation checks delegated to repository"""
        count_ok = await self.memory_repository.validate_embedding_count()
        dims_ok = await self.memory_repository.validate_embedding_dimensions()
        search_ok = await self.memory_repository.validate_search_works()

        result = ValidationResult(
            count_ok=count_ok,
            dimensions_ok=dims_ok,
            search_ok=search_ok,
        )

        if result.all_passed:
            logger.info("Validation passed", extra={
                "count_ok": count_ok,
                "dimensions_ok": dims_ok,
                "search_ok": search_ok,
            })
        else:
            logger.error("Validation failed", extra={
                "count_ok": count_ok,
                "dimensions_ok": dims_ok,
                "search_ok": search_ok,
            })

        return result
