"""PostgreSQL repository for Skill data access operations
"""
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, text, update

from app.config.logging_config import logging
from app.config.settings import settings
from app.exceptions import NotFoundError
from app.models.skill_models import (
    Skill,
    SkillCreate,
    SkillLinks,
    SkillSummary,
    SkillUpdate,
)
from app.protocols.embedding_protocol import EmbeddingsAdapter
from app.repositories.embeddings.reranker_adapter import RerankAdapter
from app.repositories.postgres.postgres_adapter import PostgresDatabaseAdapter
from app.repositories.postgres.postgres_tables import (
    CodeArtifactsTable,
    DocumentsTable,
    FilesTable,
    MemoryTable,
    SkillsTable,
    memory_skill_association,
    skill_code_artifact_association,
    skill_document_association,
    skill_file_association,
)
from app.utils.embedding_helpers import build_skill_embedding_text

logger = logging.getLogger(__name__)


class PostgresSkillRepository:
    """Repository for Skill operations in PostgreSQL"""

    def __init__(
        self,
        db_adapter: PostgresDatabaseAdapter,
        embedding_adapter: EmbeddingsAdapter,
        rerank_adapter: RerankAdapter | None = None,
    ):
        """Initialize with database and embedding adapters

        Args:
            db_adapter: PostgreSQL database adapter for session management
            embedding_adapter: Adapter for generating embeddings
            rerank_adapter: Optional cross-encoder reranker for search
        """
        self.db_adapter = db_adapter
        self.embedding_adapter = embedding_adapter
        self.rerank_adapter = rerank_adapter
        logger.info("Postgres skill repository initialized")

    async def create_skill(
        self,
        user_id: UUID,
        skill_data: SkillCreate,
    ) -> Skill:
        """Create a new skill with embedding

        Args:
            user_id: User ID for ownership
            skill_data: SkillCreate with skill details

        Returns:
            Created Skill with generated ID and timestamps
        """
        try:
            embedding_text = build_skill_embedding_text(skill_data)
            embedding = await self.embedding_adapter.generate_embedding(embedding_text)

            async with self.db_adapter.session(user_id) as session:
                skill_table = SkillsTable(
                    user_id=user_id,
                    name=skill_data.name,
                    description=skill_data.description,
                    content=skill_data.content,
                    license=skill_data.license,
                    compatibility=skill_data.compatibility,
                    allowed_tools=skill_data.allowed_tools,
                    skill_metadata=skill_data.metadata,
                    tags=skill_data.tags,
                    importance=skill_data.importance,
                    project_id=skill_data.project_id,
                    embedding=embedding,
                    source_repo=skill_data.source_repo,
                    source_files=skill_data.source_files,
                    source_url=skill_data.source_url,
                    confidence=skill_data.confidence,
                    encoding_agent=skill_data.encoding_agent,
                    encoding_version=skill_data.encoding_version,
                    agent_id=skill_data.agent_id,
                    agent_version=skill_data.agent_version,
                    agent_model=skill_data.agent_model,
                )

                session.add(skill_table)
                await session.commit()
                await session.refresh(skill_table)

                return self._to_skill(skill_table)

        except Exception as e:
            logger.error(
                "Failed to create skill",
                exc_info=True,
                extra={
                    "user_id": str(user_id),
                    "error": str(e),
                },
            )
            raise

    async def skill_name_exists(
        self,
        user_id: UUID,
        name: str,
    ) -> bool:
        """Check if a skill with the given name exists for this user."""
        try:
            async with self.db_adapter.session(user_id) as session:
                stmt = select(SkillsTable.id).where(
                    SkillsTable.user_id == user_id,
                    SkillsTable.name == name,
                ).limit(1)
                result = await session.execute(stmt)
                return result.scalar_one_or_none() is not None
        except Exception:
            logger.exception(
                "Failed to check skill name existence",
                extra={
                    "user_id": str(user_id),
                    "name": name,
                },
            )
            raise

    async def get_skill_by_id(
        self,
        user_id: UUID,
        skill_id: int,
    ) -> Skill | None:
        """Get skill by ID with ownership check

        Args:
            user_id: User ID for ownership verification
            skill_id: Skill ID to retrieve

        Returns:
            Skill if found and owned by user, None otherwise
        """
        try:
            async with self.db_adapter.session(user_id) as session:
                stmt = select(SkillsTable).where(
                    SkillsTable.id == skill_id,
                    SkillsTable.user_id == user_id,
                )

                result = await session.execute(stmt)
                skill_table = result.scalar_one_or_none()

                if not skill_table:
                    return None

                return self._to_skill(skill_table)

        except Exception as e:
            logger.error(
                f"Failed to get skill {skill_id}",
                exc_info=True,
                extra={
                    "user_id": str(user_id),
                    "skill_id": skill_id,
                    "error": str(e),
                },
            )
            raise

    async def list_skills(
        self,
        user_id: UUID,
        project_id: int | None = None,
        tags: list[str] | None = None,
        importance_threshold: int | None = None,
    ) -> list[SkillSummary]:
        """List skills with optional filtering

        Args:
            user_id: User ID for ownership filtering
            project_id: Optional filter by project
            tags: Optional filter by tags (returns skills with ANY of these tags)
            importance_threshold: Optional minimum importance level

        Returns:
            List of SkillSummary (lightweight, excludes full content)
        """
        try:
            async with self.db_adapter.session(user_id) as session:
                stmt = select(SkillsTable).where(
                    SkillsTable.user_id == user_id,
                )

                if project_id is not None:
                    stmt = stmt.where(SkillsTable.project_id == project_id)

                if tags:
                    stmt = stmt.where(SkillsTable.tags.overlap(tags))

                if importance_threshold is not None:
                    stmt = stmt.where(SkillsTable.importance >= importance_threshold)

                stmt = stmt.order_by(SkillsTable.created_at.desc())

                result = await session.execute(stmt)
                skills = result.scalars().all()

                return [SkillSummary.model_validate(s) for s in skills]

        except Exception as e:
            logger.error(
                "Failed to list skills",
                exc_info=True,
                extra={
                    "user_id": str(user_id),
                    "error": str(e),
                },
            )
            raise

    async def update_skill(
        self,
        user_id: UUID,
        skill_id: int,
        skill_data: SkillUpdate,
    ) -> Skill:
        """Update skill (PATCH semantics)

        Only provided fields are updated. None/omitted fields remain unchanged.
        If description changes, the embedding is regenerated.

        Args:
            user_id: User ID for ownership verification
            skill_id: Skill ID to update
            skill_data: SkillUpdate with fields to change

        Returns:
            Updated Skill

        Raises:
            NotFoundError: If skill not found or not owned by user
        """
        try:
            async with self.db_adapter.session(user_id) as session:
                stmt = select(SkillsTable).where(
                    SkillsTable.id == skill_id,
                    SkillsTable.user_id == user_id,
                )

                result = await session.execute(stmt)
                skill_table = result.scalar_one_or_none()

                if not skill_table:
                    raise NotFoundError(f"Skill {skill_id} not found")

                update_data = skill_data.model_dump(exclude_unset=True)

                # Map Pydantic 'metadata' field to ORM 'skill_metadata' column
                if "metadata" in update_data:
                    update_data["skill_metadata"] = update_data.pop("metadata")

                # Regenerate embedding if description changed
                if "description" in update_data:
                    embedding_text = build_skill_embedding_text(skill_data)
                    embedding = await self.embedding_adapter.generate_embedding(embedding_text)
                    update_data["embedding"] = embedding

                for field, value in update_data.items():
                    setattr(skill_table, field, value)

                skill_table.updated_at = datetime.now(UTC)

                await session.commit()
                await session.refresh(skill_table)

                return self._to_skill(skill_table)

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to update skill {skill_id}",
                exc_info=True,
                extra={
                    "user_id": str(user_id),
                    "skill_id": skill_id,
                    "error": str(e),
                },
            )
            raise

    async def delete_skill(
        self,
        user_id: UUID,
        skill_id: int,
    ) -> bool:
        """Delete skill with ownership check

        Args:
            user_id: User ID for ownership verification
            skill_id: Skill ID to delete

        Returns:
            True if deleted, False if not found or not owned by user
        """
        try:
            async with self.db_adapter.session(user_id) as session:
                stmt = select(SkillsTable).where(
                    SkillsTable.id == skill_id,
                    SkillsTable.user_id == user_id,
                )

                result = await session.execute(stmt)
                skill_table = result.scalar_one_or_none()

                if not skill_table:
                    return False

                await session.delete(skill_table)
                await session.commit()

                return True

        except Exception as e:
            logger.error(
                f"Failed to delete skill {skill_id}",
                exc_info=True,
                extra={
                    "user_id": str(user_id),
                    "skill_id": skill_id,
                    "error": str(e),
                },
            )
            raise

    async def search_skills(
        self,
        user_id: UUID,
        query: str,
        k: int = 5,
        project_id: int | None = None,
    ) -> list[SkillSummary]:
        """Search skills by semantic similarity

        Generates a query embedding and uses cosine distance for vector
        similarity search. Optionally applies cross-encoder reranking.

        Args:
            user_id: User ID for ownership filtering
            query: Search query string
            k: Number of results to return (default: 5)
            project_id: Optional filter by project

        Returns:
            List of SkillSummary ranked by relevance
        """
        try:
            query_embedding = await self.embedding_adapter.generate_embedding(query)

            # Fetch more candidates if reranking is enabled
            candidates_k = k * 3 if self.rerank_adapter is not None else k

            async with self.db_adapter.session(user_id) as session:
                stmt = select(SkillsTable).where(
                    SkillsTable.user_id == user_id,
                )

                if project_id is not None:
                    stmt = stmt.where(SkillsTable.project_id == project_id)

                stmt = stmt.order_by(
                    SkillsTable.embedding.cosine_distance(query_embedding),
                )
                stmt = stmt.limit(candidates_k)

                result = await session.execute(stmt)
                skills = result.scalars().all()

                if not skills:
                    return []

                # Apply cross-encoder reranking if available
                if self.rerank_adapter is not None and len(skills) > k:
                    documents = [s.description for s in skills]
                    ranked = await self.rerank_adapter.rerank(
                        query=query, documents=documents,
                    )
                    skills = [skills[idx] for idx, score in ranked[:k]]

                return [SkillSummary.model_validate(s) for s in skills]

        except Exception as e:
            logger.error(
                "Failed to search skills",
                exc_info=True,
                extra={
                    "user_id": str(user_id),
                    "query": query,
                    "error": str(e),
                },
            )
            raise

    async def link_skill_to_memory(
        self,
        user_id: UUID,
        skill_id: int,
        memory_id: int,
    ) -> dict:
        """Link a skill to a memory via the association table.

        Args:
            user_id: User ID for ownership verification.
            skill_id: Skill ID to link.
            memory_id: Memory ID to link.

        Returns:
            Dict confirming the link was created.

        Raises:
            NotFoundError: If skill or memory not found or not owned by user.
        """
        try:
            async with self.db_adapter.session(user_id) as session:
                # Verify skill exists and is owned by user
                skill_stmt = select(SkillsTable).where(
                    SkillsTable.id == skill_id,
                    SkillsTable.user_id == user_id,
                )
                skill_result = await session.execute(skill_stmt)
                if skill_result.scalar_one_or_none() is None:
                    msg = f"Skill {skill_id} not found"
                    raise NotFoundError(msg)

                # Verify memory exists and is owned by user
                memory_stmt = select(MemoryTable).where(
                    MemoryTable.id == memory_id,
                    MemoryTable.user_id == user_id,
                )
                memory_result = await session.execute(memory_stmt)
                if memory_result.scalar_one_or_none() is None:
                    msg = f"Memory {memory_id} not found"
                    raise NotFoundError(msg)

                # Check if link already exists (idempotent)
                existing = await session.execute(
                    select(memory_skill_association).where(
                        memory_skill_association.c.skill_id == skill_id,
                        memory_skill_association.c.memory_id == memory_id,
                    ),
                )
                if existing.first() is None:
                    await session.execute(
                        memory_skill_association.insert().values(
                            skill_id=skill_id,
                            memory_id=memory_id,
                        ),
                    )
                    await session.commit()

                return {
                    "skill_id": skill_id,
                    "memory_id": memory_id,
                    "linked": True,
                }

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to link skill {skill_id} to memory {memory_id}",
                exc_info=True,
                extra={
                    "user_id": str(user_id),
                    "skill_id": skill_id,
                    "memory_id": memory_id,
                    "error": str(e),
                },
            )
            raise

    async def unlink_skill_from_memory(
        self,
        user_id: UUID,
        skill_id: int,
        memory_id: int,
    ) -> dict:
        """Remove the link between a skill and a memory.

        Args:
            user_id: User ID for ownership verification.
            skill_id: Skill ID to unlink.
            memory_id: Memory ID to unlink.

        Returns:
            Dict with unlinked=True if removed, False if link didn't exist.
        """
        try:
            async with self.db_adapter.session(user_id) as session:
                result = await session.execute(
                    memory_skill_association.delete().where(
                        memory_skill_association.c.skill_id == skill_id,
                        memory_skill_association.c.memory_id == memory_id,
                    ),
                )
                await session.commit()

                return {
                    "skill_id": skill_id,
                    "memory_id": memory_id,
                    "unlinked": result.rowcount > 0,
                }

        except Exception as e:
            logger.error(
                f"Failed to unlink skill {skill_id} from memory {memory_id}",
                exc_info=True,
                extra={
                    "user_id": str(user_id),
                    "skill_id": skill_id,
                    "memory_id": memory_id,
                    "error": str(e),
                },
            )
            raise

    async def link_skill_to_file(
        self,
        user_id: UUID,
        skill_id: int,
        file_id: int,
    ) -> dict:
        """Link a skill to a file via the association table.

        Args:
            user_id: User ID for ownership verification.
            skill_id: Skill ID to link.
            file_id: File ID to link.

        Returns:
            Dict confirming the link was created.

        Raises:
            NotFoundError: If skill or file not found or not owned by user.
        """
        try:
            async with self.db_adapter.session(user_id) as session:
                skill_stmt = select(SkillsTable).where(
                    SkillsTable.id == skill_id,
                    SkillsTable.user_id == user_id,
                )
                skill_result = await session.execute(skill_stmt)
                if skill_result.scalar_one_or_none() is None:
                    msg = f"Skill {skill_id} not found"
                    raise NotFoundError(msg)

                file_stmt = select(FilesTable).where(
                    FilesTable.id == file_id,
                    FilesTable.user_id == user_id,
                )
                file_result = await session.execute(file_stmt)
                if file_result.scalar_one_or_none() is None:
                    msg = f"File {file_id} not found"
                    raise NotFoundError(msg)

                # Check if link already exists (idempotent)
                existing = await session.execute(
                    select(skill_file_association).where(
                        skill_file_association.c.skill_id == skill_id,
                        skill_file_association.c.file_id == file_id,
                    ),
                )
                if existing.first() is None:
                    await session.execute(
                        skill_file_association.insert().values(
                            skill_id=skill_id,
                            file_id=file_id,
                        ),
                    )
                    await session.commit()

                return {
                    "skill_id": skill_id,
                    "file_id": file_id,
                    "linked": True,
                }

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to link skill {skill_id} to file {file_id}",
                exc_info=True,
                extra={
                    "user_id": str(user_id),
                    "skill_id": skill_id,
                    "file_id": file_id,
                    "error": str(e),
                },
            )
            raise

    async def unlink_skill_from_file(
        self,
        user_id: UUID,
        skill_id: int,
        file_id: int,
    ) -> dict:
        """Remove the link between a skill and a file.

        Args:
            user_id: User ID for ownership verification.
            skill_id: Skill ID to unlink.
            file_id: File ID to unlink.

        Returns:
            Dict with unlinked=True if removed, False if link didn't exist.
        """
        try:
            async with self.db_adapter.session(user_id) as session:
                result = await session.execute(
                    skill_file_association.delete().where(
                        skill_file_association.c.skill_id == skill_id,
                        skill_file_association.c.file_id == file_id,
                    ),
                )
                await session.commit()

                return {
                    "skill_id": skill_id,
                    "file_id": file_id,
                    "unlinked": result.rowcount > 0,
                }

        except Exception as e:
            logger.error(
                f"Failed to unlink skill {skill_id} from file {file_id}",
                exc_info=True,
                extra={
                    "user_id": str(user_id),
                    "skill_id": skill_id,
                    "file_id": file_id,
                    "error": str(e),
                },
            )
            raise

    async def link_skill_to_code_artifact(
        self,
        user_id: UUID,
        skill_id: int,
        code_artifact_id: int,
    ) -> dict:
        """Link a skill to a code artifact via the association table.

        Args:
            user_id: User ID for ownership verification.
            skill_id: Skill ID to link.
            code_artifact_id: Code artifact ID to link.

        Returns:
            Dict confirming the link was created.

        Raises:
            NotFoundError: If skill or code artifact not found or not owned by user.
        """
        try:
            async with self.db_adapter.session(user_id) as session:
                skill_stmt = select(SkillsTable).where(
                    SkillsTable.id == skill_id,
                    SkillsTable.user_id == user_id,
                )
                skill_result = await session.execute(skill_stmt)
                if skill_result.scalar_one_or_none() is None:
                    msg = f"Skill {skill_id} not found"
                    raise NotFoundError(msg)

                ca_stmt = select(CodeArtifactsTable).where(
                    CodeArtifactsTable.id == code_artifact_id,
                    CodeArtifactsTable.user_id == user_id,
                )
                ca_result = await session.execute(ca_stmt)
                if ca_result.scalar_one_or_none() is None:
                    msg = f"Code artifact {code_artifact_id} not found"
                    raise NotFoundError(msg)

                # Check if link already exists (idempotent)
                existing = await session.execute(
                    select(skill_code_artifact_association).where(
                        skill_code_artifact_association.c.skill_id == skill_id,
                        skill_code_artifact_association.c.code_artifact_id == code_artifact_id,
                    ),
                )
                if existing.first() is None:
                    await session.execute(
                        skill_code_artifact_association.insert().values(
                            skill_id=skill_id,
                            code_artifact_id=code_artifact_id,
                        ),
                    )
                    await session.commit()

                return {
                    "skill_id": skill_id,
                    "code_artifact_id": code_artifact_id,
                    "linked": True,
                }

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to link skill {skill_id} to code artifact {code_artifact_id}",
                exc_info=True,
                extra={
                    "user_id": str(user_id),
                    "skill_id": skill_id,
                    "code_artifact_id": code_artifact_id,
                    "error": str(e),
                },
            )
            raise

    async def unlink_skill_from_code_artifact(
        self,
        user_id: UUID,
        skill_id: int,
        code_artifact_id: int,
    ) -> dict:
        """Remove the link between a skill and a code artifact.

        Args:
            user_id: User ID for ownership verification.
            skill_id: Skill ID to unlink.
            code_artifact_id: Code artifact ID to unlink.

        Returns:
            Dict with unlinked=True if removed, False if link didn't exist.
        """
        try:
            async with self.db_adapter.session(user_id) as session:
                result = await session.execute(
                    skill_code_artifact_association.delete().where(
                        skill_code_artifact_association.c.skill_id == skill_id,
                        skill_code_artifact_association.c.code_artifact_id == code_artifact_id,
                    ),
                )
                await session.commit()

                return {
                    "skill_id": skill_id,
                    "code_artifact_id": code_artifact_id,
                    "unlinked": result.rowcount > 0,
                }

        except Exception as e:
            logger.error(
                f"Failed to unlink skill {skill_id} from code artifact {code_artifact_id}",
                exc_info=True,
                extra={
                    "user_id": str(user_id),
                    "skill_id": skill_id,
                    "code_artifact_id": code_artifact_id,
                    "error": str(e),
                },
            )
            raise

    async def link_skill_to_document(
        self,
        user_id: UUID,
        skill_id: int,
        document_id: int,
    ) -> dict:
        """Link a skill to a document via the association table.

        Args:
            user_id: User ID for ownership verification.
            skill_id: Skill ID to link.
            document_id: Document ID to link.

        Returns:
            Dict confirming the link was created.

        Raises:
            NotFoundError: If skill or document not found or not owned by user.
        """
        try:
            async with self.db_adapter.session(user_id) as session:
                skill_stmt = select(SkillsTable).where(
                    SkillsTable.id == skill_id,
                    SkillsTable.user_id == user_id,
                )
                skill_result = await session.execute(skill_stmt)
                if skill_result.scalar_one_or_none() is None:
                    msg = f"Skill {skill_id} not found"
                    raise NotFoundError(msg)

                doc_stmt = select(DocumentsTable).where(
                    DocumentsTable.id == document_id,
                    DocumentsTable.user_id == user_id,
                )
                doc_result = await session.execute(doc_stmt)
                if doc_result.scalar_one_or_none() is None:
                    msg = f"Document {document_id} not found"
                    raise NotFoundError(msg)

                # Check if link already exists (idempotent)
                existing = await session.execute(
                    select(skill_document_association).where(
                        skill_document_association.c.skill_id == skill_id,
                        skill_document_association.c.document_id == document_id,
                    ),
                )
                if existing.first() is None:
                    await session.execute(
                        skill_document_association.insert().values(
                            skill_id=skill_id,
                            document_id=document_id,
                        ),
                    )
                    await session.commit()

                return {
                    "skill_id": skill_id,
                    "document_id": document_id,
                    "linked": True,
                }

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to link skill {skill_id} to document {document_id}",
                exc_info=True,
                extra={
                    "user_id": str(user_id),
                    "skill_id": skill_id,
                    "document_id": document_id,
                    "error": str(e),
                },
            )
            raise

    async def unlink_skill_from_document(
        self,
        user_id: UUID,
        skill_id: int,
        document_id: int,
    ) -> dict:
        """Remove the link between a skill and a document.

        Args:
            user_id: User ID for ownership verification.
            skill_id: Skill ID to unlink.
            document_id: Document ID to unlink.

        Returns:
            Dict with unlinked=True if removed, False if link didn't exist.
        """
        try:
            async with self.db_adapter.session(user_id) as session:
                result = await session.execute(
                    skill_document_association.delete().where(
                        skill_document_association.c.skill_id == skill_id,
                        skill_document_association.c.document_id == document_id,
                    ),
                )
                await session.commit()

                return {
                    "skill_id": skill_id,
                    "document_id": document_id,
                    "unlinked": result.rowcount > 0,
                }

        except Exception as e:
            logger.error(
                f"Failed to unlink skill {skill_id} from document {document_id}",
                exc_info=True,
                extra={
                    "user_id": str(user_id),
                    "skill_id": skill_id,
                    "document_id": document_id,
                    "error": str(e),
                },
            )
            raise

    async def get_skill_links(
        self,
        user_id: UUID,
        skill_id: int,
    ) -> SkillLinks:
        """Get IDs of all content linked to a skill (reverse lookup).

        Args:
            user_id: User ID for ownership verification
            skill_id: Skill to look up links for

        Returns:
            SkillLinks with memory, file, code artifact and document IDs

        Raises:
            NotFoundError: If skill not found or not owned by user
        """
        try:
            async with self.db_adapter.session(user_id) as session:
                # First verify the skill exists and is owned by user
                skill_stmt = select(SkillsTable).where(
                    SkillsTable.id == skill_id,
                    SkillsTable.user_id == user_id,
                )
                skill_result = await session.execute(skill_stmt)
                if skill_result.scalar_one_or_none() is None:
                    raise NotFoundError(f"Skill {skill_id} not found")

                memory_stmt = select(
                    memory_skill_association.c.memory_id,
                ).join(
                    MemoryTable,
                    MemoryTable.id == memory_skill_association.c.memory_id,
                ).where(
                    memory_skill_association.c.skill_id == skill_id,
                    MemoryTable.user_id == user_id,
                )
                memory_ids = [row.memory_id for row in await session.execute(memory_stmt)]

                file_stmt = select(
                    skill_file_association.c.file_id,
                ).join(
                    FilesTable,
                    FilesTable.id == skill_file_association.c.file_id,
                ).where(
                    skill_file_association.c.skill_id == skill_id,
                    FilesTable.user_id == user_id,
                )
                file_ids = [row.file_id for row in await session.execute(file_stmt)]

                artifact_stmt = select(
                    skill_code_artifact_association.c.code_artifact_id,
                ).join(
                    CodeArtifactsTable,
                    CodeArtifactsTable.id == skill_code_artifact_association.c.code_artifact_id,
                ).where(
                    skill_code_artifact_association.c.skill_id == skill_id,
                    CodeArtifactsTable.user_id == user_id,
                )
                code_artifact_ids = [
                    row.code_artifact_id for row in await session.execute(artifact_stmt)
                ]

                document_stmt = select(
                    skill_document_association.c.document_id,
                ).join(
                    DocumentsTable,
                    DocumentsTable.id == skill_document_association.c.document_id,
                ).where(
                    skill_document_association.c.skill_id == skill_id,
                    DocumentsTable.user_id == user_id,
                )
                document_ids = [
                    row.document_id for row in await session.execute(document_stmt)
                ]

                return SkillLinks(
                    memory_ids=memory_ids,
                    file_ids=file_ids,
                    code_artifact_ids=code_artifact_ids,
                    document_ids=document_ids,
                )
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(
                "Failed to get skill links",
                exc_info=True,
                extra={
                    "user_id": str(user_id),
                    "skill_id": skill_id,
                    "error": str(e),
                },
            )
            raise

    async def get_all_skill_file_links(
        self,
        user_id: UUID,
    ) -> list[tuple[int, int]]:
        """Get all skill-file associations for a user (for graph visualization)."""
        try:
            async with self.db_adapter.session(user_id) as session:
                stmt = select(
                    skill_file_association.c.skill_id,
                    skill_file_association.c.file_id,
                ).select_from(
                    skill_file_association,
                ).join(
                    SkillsTable,
                    SkillsTable.id == skill_file_association.c.skill_id,
                ).join(
                    FilesTable,
                    FilesTable.id == skill_file_association.c.file_id,
                ).where(
                    SkillsTable.user_id == user_id,
                    FilesTable.user_id == user_id,
                )

                result = await session.execute(stmt)
                return [(row.skill_id, row.file_id) for row in result]
        except Exception:
            logger.exception(
                "Failed to get all skill-file links",
                extra={"user_id": str(user_id)},
            )
            raise

    async def get_all_skill_code_artifact_links(
        self,
        user_id: UUID,
    ) -> list[tuple[int, int]]:
        """Get all skill-code_artifact associations for a user (for graph visualization)."""
        try:
            async with self.db_adapter.session(user_id) as session:
                stmt = select(
                    skill_code_artifact_association.c.skill_id,
                    skill_code_artifact_association.c.code_artifact_id,
                ).select_from(
                    skill_code_artifact_association,
                ).join(
                    SkillsTable,
                    SkillsTable.id == skill_code_artifact_association.c.skill_id,
                ).join(
                    CodeArtifactsTable,
                    CodeArtifactsTable.id == skill_code_artifact_association.c.code_artifact_id,
                ).where(
                    SkillsTable.user_id == user_id,
                    CodeArtifactsTable.user_id == user_id,
                )

                result = await session.execute(stmt)
                return [(row.skill_id, row.code_artifact_id) for row in result]
        except Exception:
            logger.exception(
                "Failed to get all skill-code_artifact links",
                extra={"user_id": str(user_id)},
            )
            raise

    async def get_all_skill_document_links(
        self,
        user_id: UUID,
    ) -> list[tuple[int, int]]:
        """Get all skill-document associations for a user (for graph visualization)."""
        try:
            async with self.db_adapter.session(user_id) as session:
                stmt = select(
                    skill_document_association.c.skill_id,
                    skill_document_association.c.document_id,
                ).select_from(
                    skill_document_association,
                ).join(
                    SkillsTable,
                    SkillsTable.id == skill_document_association.c.skill_id,
                ).join(
                    DocumentsTable,
                    DocumentsTable.id == skill_document_association.c.document_id,
                ).where(
                    SkillsTable.user_id == user_id,
                    DocumentsTable.user_id == user_id,
                )

                result = await session.execute(stmt)
                return [(row.skill_id, row.document_id) for row in result]
        except Exception:
            logger.exception(
                "Failed to get all skill-document links",
                extra={"user_id": str(user_id)},
            )
            raise

    # ============ Re-embedding support methods ============

    async def count_all_skills(self) -> int:
        """Count all skills across all users."""
        async with self.db_adapter.system_session() as session:
            return await session.scalar(select(func.count()).select_from(SkillsTable))

    async def get_skills_for_reembedding(self, limit: int, offset: int) -> list[Skill]:
        """Fetch all skills, across all users, in batches ordered by id."""
        async with self.db_adapter.system_session() as session:
            result = await session.execute(
                select(SkillsTable)
                .order_by(SkillsTable.id.asc())
                .offset(offset)
                .limit(limit),
            )
            return [self._to_skill(row) for row in result.scalars().all()]

    async def reset_embedding_storage(self) -> None:
        """Alter embedding column to match new EMBEDDING_DIMENSIONS.

        pgvector cannot cast vectors across dimensions, so existing embeddings
        must be cleared before resizing the column.
        """
        dims = settings.EMBEDDING_DIMENSIONS
        async with self.db_adapter.system_session() as session:
            # Drop NOT NULL so we can clear embeddings
            await session.execute(text(
                "ALTER TABLE skills ALTER COLUMN embedding DROP NOT NULL",
            ))
            # Clear existing embeddings (can't cast across dimensions)
            await session.execute(text(
                "UPDATE skills SET embedding = NULL",
            ))
            # Resize the column
            await session.execute(text(
                f"ALTER TABLE skills ALTER COLUMN embedding TYPE vector({dims})",
            ))
            logger.info("Altered skills embedding column", extra={
                "dimensions": dims,
            })

    async def finalize_embedding_storage(self) -> None:
        """Restore NOT NULL on the embedding column that reset_embedding_storage dropped.

        Only valid once every skill has an embedding again, otherwise PostgreSQL rejects it.
        """
        async with self.db_adapter.system_session() as session:
            await session.execute(text(
                "ALTER TABLE skills ALTER COLUMN embedding SET NOT NULL",
            ))

    async def bulk_update_embeddings(self, updates: list[tuple[int, list[float]]]) -> None:
        """Write new embeddings for a batch of skill IDs"""
        async with self.db_adapter.system_session() as session:
            for skill_id, embedding in updates:
                await session.execute(
                    update(SkillsTable)
                    .where(SkillsTable.id == skill_id)
                    # Assigning updated_at to itself keeps its onupdate default from
                    # presenting a rebuilt vector as an edit of the skill.
                    .values(embedding=embedding, updated_at=SkillsTable.updated_at),
                )

    async def validate_embedding_count(self) -> bool:
        """Check every skill has an embedding."""
        async with self.db_adapter.system_session() as session:
            skill_count = await session.scalar(
                select(func.count()).select_from(SkillsTable),
            )
            embedding_count = await session.scalar(
                select(func.count()).select_from(SkillsTable).where(
                    SkillsTable.embedding.isnot(None),
                ),
            )
            return skill_count == embedding_count

    async def validate_embedding_dimensions(self) -> bool:
        """Sample embeddings and verify correct dimensions"""
        async with self.db_adapter.system_session() as session:
            result = await session.execute(
                text("""
                    SELECT vector_dims(embedding) as dims
                    FROM skills
                    WHERE embedding IS NOT NULL
                    LIMIT 5
                """),
            )
            for row in result.fetchall():
                if row[0] != settings.EMBEDDING_DIMENSIONS:
                    logger.error("Skill dimension mismatch", extra={
                        "expected": settings.EMBEDDING_DIMENSIONS,
                        "actual": row[0],
                    })
                    return False
            return True

    @staticmethod
    def _to_skill(row: SkillsTable) -> Skill:
        """Convert ORM row to Skill model.

        Handles the skill_metadata -> metadata field name mapping.
        SQLAlchemy models have a class-level .metadata attribute (MetaData),
        so we cannot rely on model_validate(row) for this field.
        """
        return Skill(
            id=row.id,
            name=row.name,
            description=row.description,
            content=row.content,
            license=row.license,
            compatibility=row.compatibility,
            allowed_tools=row.allowed_tools,
            metadata=row.skill_metadata,
            tags=row.tags,
            importance=row.importance,
            project_id=row.project_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
            source_repo=row.source_repo,
            source_files=row.source_files,
            source_url=row.source_url,
            confidence=row.confidence,
            encoding_agent=row.encoding_agent,
            encoding_version=row.encoding_version,
            agent_id=row.agent_id,
            agent_version=row.agent_version,
            agent_model=row.agent_model,
        )
