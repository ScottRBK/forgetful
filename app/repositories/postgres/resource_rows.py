"""Shared native row construction for ordinary and bundled resource creation."""
import base64
from uuid import UUID

from app.models.code_artifact_models import CodeArtifactCreate
from app.models.document_models import DocumentCreate
from app.models.file_models import File, FileCreate
from app.models.skill_models import SkillCreate
from app.repositories.postgres.postgres_tables import (
    CodeArtifactsTable,
    DocumentsTable,
    FilesTable,
    SkillsTable,
)


def build_document_row(user_id: UUID, document_data: DocumentCreate) -> DocumentsTable:
    size_bytes = document_data.size_bytes
    if size_bytes is None:
        size_bytes = len(document_data.content.encode("utf-8"))
    return DocumentsTable(
        user_id=user_id,
        title=document_data.title,
        description=document_data.description,
        content=document_data.content,
        document_type=document_data.document_type,
        filename=document_data.filename,
        size_bytes=size_bytes,
        tags=document_data.tags,
        project_id=document_data.project_id,
        source_repo=document_data.source_repo,
        source_files=document_data.source_files,
        source_url=document_data.source_url,
        confidence=document_data.confidence,
        encoding_agent=document_data.encoding_agent,
        encoding_version=document_data.encoding_version,
        agent_id=document_data.agent_id,
        agent_version=document_data.agent_version,
        agent_model=document_data.agent_model,
    )


def build_code_artifact_row(user_id: UUID, artifact_data: CodeArtifactCreate) -> CodeArtifactsTable:
    return CodeArtifactsTable(
        user_id=user_id,
        title=artifact_data.title,
        description=artifact_data.description,
        code=artifact_data.code,
        language=artifact_data.language.lower(),  # Ensure lowercase
        tags=artifact_data.tags,
        project_id=artifact_data.project_id,
        source_repo=artifact_data.source_repo,
        source_files=artifact_data.source_files,
        source_url=artifact_data.source_url,
        confidence=artifact_data.confidence,
        encoding_agent=artifact_data.encoding_agent,
        encoding_version=artifact_data.encoding_version,
        agent_id=artifact_data.agent_id,
        agent_version=artifact_data.agent_version,
        agent_model=artifact_data.agent_model,
    )


def build_file_row(user_id: UUID, file_data: FileCreate) -> FilesTable:
    decoded_data = base64.b64decode(file_data.data)
    size_bytes = len(decoded_data)
    return FilesTable(
        user_id=user_id,
        filename=file_data.filename,
        description=file_data.description,
        data=decoded_data,
        mime_type=file_data.mime_type,
        size_bytes=size_bytes,
        tags=file_data.tags,
        project_id=file_data.project_id,
        source_repo=file_data.source_repo,
        source_files=file_data.source_files,
        source_url=file_data.source_url,
        confidence=file_data.confidence,
        encoding_agent=file_data.encoding_agent,
        encoding_version=file_data.encoding_version,
        agent_id=file_data.agent_id,
        agent_version=file_data.agent_version,
        agent_model=file_data.agent_model,
    )


def build_skill_row(user_id: UUID, skill_data: SkillCreate, embedding) -> SkillsTable:
    return SkillsTable(
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


def file_model(file_table: FilesTable) -> File:
    return File(
        id=file_table.id,
        filename=file_table.filename,
        description=file_table.description,
        data=base64.b64encode(file_table.data).decode("utf-8"),
        mime_type=file_table.mime_type,
        size_bytes=file_table.size_bytes,
        tags=file_table.tags,
        project_id=file_table.project_id,
        created_at=file_table.created_at,
        updated_at=file_table.updated_at,
        source_repo=file_table.source_repo,
        source_files=file_table.source_files,
        source_url=file_table.source_url,
        confidence=file_table.confidence,
        encoding_agent=file_table.encoding_agent,
        encoding_version=file_table.encoding_version,
        agent_id=file_table.agent_id,
        agent_version=file_table.agent_version,
        agent_model=file_table.agent_model,
    )
