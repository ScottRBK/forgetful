"""Re-embedding service for batch migration of memory embeddings.

Orchestrates the workflow of re-embedding all memories with the currently
configured embedding provider. Knows nothing about SQLite/PostgreSQL specifics.
"""
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from uuid import UUID

from app.config.settings import settings
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
            progress_callback: Optional `(processed, total)` callback per batch.

        Returns:
            `TargetedRebuildResult` with per-memory outcome lists.
        """
        total = await self.memory_repository.count_memories_for_targeted_rebuild(
            user_id=user_id,
            memory_ids=memory_ids,
            project_id=project_id,
        )
        result = TargetedRebuildResult()
        if total == 0:
            self._record_unresolved_memory_ids(
                memory_ids=memory_ids,
                project_id=project_id,
                result=result,
            )
            logger.info(
                "rebuild_embeddings: no candidates",
                extra={
                    "user_id": str(user_id),
                    "memory_ids": memory_ids,
                    "project_id": project_id,
                },
            )
            return result

        processed = 0
        last_seen_id: int | None = None
        while True:
            memories = await self.memory_repository.get_memories_for_targeted_rebuild(
                user_id=user_id,
                limit=self.batch_size,
                after_id=last_seen_id,
                memory_ids=memory_ids,
                project_id=project_id,
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
                    await self._recompute_auto_links(user_id=user_id, memory_ids=written_ids, result=result)
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
            last_seen_id = memories[-1].id

        self._record_unresolved_memory_ids(
            memory_ids=memory_ids,
            project_id=project_id,
            result=result,
        )
        logger.info(
            "rebuild_embeddings: done",
            extra={
                "user_id": str(user_id),
                "rebuilt": len(result.rebuilt_ids),
                "skipped": len(result.skipped_ids),
                "failed": len(result.failed),
                "total_candidates": total,
            },
        )
        return result

    def _record_unresolved_memory_ids(
        self,
        memory_ids: list[int] | None,
        project_id: int | None,
        result: TargetedRebuildResult,
    ) -> None:
        """Surface explicit IDs hidden by user/obsolete filters as failures."""
        if memory_ids is None or project_id is not None:
            return

        resolved_ids = set(result.rebuilt_ids) | set(result.skipped_ids)
        resolved_ids.update(
            failure["memory_id"]
            for failure in result.failed
            if "memory_id" in failure
        )
        for memory_id in dict.fromkeys(memory_ids):
            if memory_id not in resolved_ids:
                result.failed.append({
                    "memory_id": memory_id,
                    "reason": "not_found_or_not_owned",
                })

    async def _recompute_auto_links(
        self,
        user_id: UUID,
        memory_ids: list[int],
        result: TargetedRebuildResult,
    ) -> None:
        """Refresh additive auto-links after new vectors have been written."""
        if settings.MEMORY_NUM_AUTO_LINK <= 0:
            return

        for memory_id in memory_ids:
            try:
                similar_memories = await self.memory_repository.find_similar_memories(
                    user_id=user_id,
                    memory_id=memory_id,
                    max_links=settings.MEMORY_NUM_AUTO_LINK,
                )
                if not similar_memories:
                    continue
                await self.memory_repository.create_links_batch(
                    user_id=user_id,
                    source_id=memory_id,
                    target_ids=[memory.id for memory in similar_memories],
                )
            except Exception as exc:  # noqa: BLE001 - link failures are per-memory partial failures
                logger.exception("rebuild_embeddings: auto-link failed", extra={
                    "memory_id": memory_id,
                    "user_id": str(user_id),
                })
                result.failed.append({
                    "memory_id": memory_id,
                    "phase": "auto_link",
                    "reason": str(exc),
                })

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
