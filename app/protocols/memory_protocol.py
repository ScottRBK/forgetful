from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from app.models.memory_models import Memory, MemoryCreate, MemoryUpdate


@dataclass
class ValidationResult:
    """Result of post-re-embedding validation checks"""
    count_ok: bool
    dimensions_ok: bool
    search_ok: bool

    @property
    def all_passed(self) -> bool:
        return self.count_ok and self.dimensions_ok and self.search_ok


class MemoryRepository(Protocol):
    """Contract for the Memory Repository"""

    async def search(
            self,
            user_id: UUID,
            query: str,
            query_context: str,
            k: int,
            importance_threshold: int | None,
            project_ids: list[int] | None,
            exclude_ids: list[int] | None,
    ) -> list[Memory]:
        ...
    async def create_memory(
            self,
            user_id: UUID,
            memory: MemoryCreate,
    ) -> Memory:
        ...
    async def create_links_batch(
            self,
            user_id: UUID,
            source_id: int,
            target_ids: list[int],
    ) -> list[int]:
        ...
    async def get_memory_by_id(
            self,
            user_id: UUID,
            memory_id: int,
    ) -> Memory:
        ...
    async def update_memory(
            self,
            user_id: UUID,
            memory_id: int,
            updated_memory: MemoryUpdate,
            existing_memory: Memory,
            search_fields_changed: bool,
    ) -> Memory | None:
        ...
    async def mark_obsolete(
            self,
            user_id: UUID,
            memory_id: int,
            reason: str,
            superseded_by: int,
    ) -> bool:
        ...
    async def get_linked_memories(
            self,
            user_id: UUID,
            memory_id: int,
            project_ids: list[int] | None,
            max_links: int = 5,
    ) -> list[Memory]:
        ...
    async def find_similar_memories(
            self,
            user_id: UUID,
            memory_id: int,
            max_links: int,
    ) -> list[Memory]:
        ...

    async def get_recent_memories(
            self,
            user_id: UUID,
            limit: int,
            offset: int = 0,
            project_ids: list[int] | None = None,
            include_obsolete: bool = False,
            sort_by: str = "created_at",
            sort_order: str = "desc",
            tags: list[str] | None = None,
    ) -> tuple[list[Memory], int]:
        """Get memories with pagination, sorting, and filtering.

        Args:
            user_id: User ID
            limit: Max results to return
            offset: Skip N results for pagination
            project_ids: Filter by project (optional)
            include_obsolete: Include soft-deleted memories
            sort_by: Sort field - created_at, updated_at, importance
            sort_order: Sort direction - asc, desc
            tags: Filter by ANY of these tags (OR logic)

        Returns:
            Tuple of (memories, total_count) where total_count is
            the count BEFORE limit/offset applied (for pagination)
        """
        ...

    async def unlink_memories(
            self,
            user_id: UUID,
            source_id: int,
            target_id: int,
    ) -> bool:
        """Remove bidirectional link between two memories.

        Args:
            user_id: User ID for isolation
            source_id: Source memory ID
            target_id: Target memory ID to unlink

        Returns:
            True if link was removed, False if link didn't exist
        """
        ...

    async def get_subgraph_nodes(
            self,
            user_id: UUID,
            center_type: str,
            center_id: int,
            depth: int,
            include_memories: bool,
            include_entities: bool,
            include_projects: bool,
            include_documents: bool,
            include_code_artifacts: bool,
            max_nodes: int,
    ) -> tuple[list[dict[str, Any]], bool]:
        """Traverse graph using recursive CTE from center node.

        Uses a single recursive CTE query to traverse all edge types:
        - memory_links (memory <-> memory)
        - memory_entity_association (memory <-> entity)
        - entity_relationships (entity <-> entity)
        - memory_project_association (memory <-> project)
        - document.project_id (document -> project)
        - code_artifact.project_id (code_artifact -> project)
        - memory_document_association (memory <-> document)
        - memory_code_artifact_association (memory <-> code_artifact)

        Args:
            user_id: User ID for ownership filtering
            center_type: "memory", "entity", "project", "document", or "code_artifact"
            center_id: ID of the center node
            depth: Maximum traversal depth (1-3)
            include_memories: Whether to include memory nodes in traversal
            include_entities: Whether to include entity nodes in traversal
            include_projects: Whether to include project nodes in traversal
            include_documents: Whether to include document nodes in traversal
            include_code_artifacts: Whether to include code_artifact nodes in traversal
            max_nodes: Maximum nodes to return

        Returns:
            Tuple of (nodes_list, truncated) where nodes_list contains dicts
            with node_id, node_type, and depth fields
        """
        ...

    # Re-embedding support methods

    async def count_all_memories(self) -> int:
        """Count all non-obsolete memories across all users"""
        ...

    async def get_memories_for_reembedding(self, limit: int, offset: int) -> list[Memory]:
        """Fetch memories in batches for re-embedding (all users, ordered by id)"""
        ...

    async def count_memories_for_targeted_rebuild(
            self,
            user_id: UUID,
            memory_ids: list[int] | None = None,
            project_id: int | None = None,
    ) -> int:
        """Count memories eligible for a *user-scoped, targeted* embedding rebuild.

        Used by `rebuild_embeddings` to avoid the destructive global
        `re_embed_all` path. Filters are user-scoped; user_id is mandatory and
        scopes ownership. Matching memories are rebuilt unconditionally.

        Args:
            user_id: Authenticated user id; ownership filter, never optional.
            memory_ids: Restrict to explicit ids (already user-scoped server-side).
            project_id: Restrict to a single project owned by `user_id`.

        Returns:
            Number of non-obsolete memories matching the filters and owned by
            `user_id`.
        """
        ...

    async def get_memories_for_targeted_rebuild(
            self,
            user_id: UUID,
            limit: int,
            after_id: int | None = None,
            memory_ids: list[int] | None = None,
            project_id: int | None = None,
    ) -> list[Memory]:
        """Page through memories selected by `count_memories_for_targeted_rebuild`.

        Same semantics and same filters as the count variant. Uses keyset
        pagination by memory id so callers can process deterministically.
        """
        ...

    async def upsert_targeted_embeddings(
            self,
            user_id: UUID,
            updates: list[tuple[int, list[float]]],
    ) -> list[int]:
        """Idempotently write a batch of new embeddings for `user_id`.

        Unlike `bulk_update_embeddings`, this method:
        - is user-scoped (rejects ids not owned by `user_id`),
        - never resets vector storage,
        - is idempotent for repeated calls on the same memory id.

        Args:
            user_id: Authenticated user id; ownership filter, never optional.
            updates: list of (memory_id, embedding) tuples.

        Returns:
            list of memory ids whose embedding was actually written.
        """
        ...

    async def reset_embedding_storage(self) -> None:
        """Prepare vector storage for new dimensions.
        SQLite: DROP + CREATE vec_memories with new dimensions
        Postgres: ALTER embedding column type
        """
        ...

    async def bulk_update_embeddings(self, updates: list[tuple[int, list[float]]]) -> None:
        """Write new embeddings for a batch of memory IDs"""
        ...

    async def validate_embedding_count(self) -> bool:
        """Check embedding count matches non-obsolete memory count"""
        ...

    async def validate_embedding_dimensions(self) -> bool:
        """Sample embeddings and verify correct dimensions"""
        ...

    async def validate_search_works(self) -> bool:
        """Run a smoke-test semantic search"""
        ...


