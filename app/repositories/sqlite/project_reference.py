"""Ownership check for project ids referenced by other records (SQLite)."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError
from app.repositories.sqlite.sqlite_tables import ProjectsTable


async def ensure_project_owned(
    session: AsyncSession,
    user_id: UUID,
    project_id: int | None,
) -> None:
    """Raise NotFoundError unless ``project_id`` is None or one of the user's own projects.

    The projects foreign key only proves the id exists, whoever owns it, so the
    ownership filter has to be applied here. A foreign id is reported exactly like
    an unknown id so callers cannot probe which project ids exist.

    Args:
        session: Open session of the repository operation (same transaction as the write)
        user_id: User that must own the project
        project_id: Referenced project id, None when the record has no project

    Raises:
        NotFoundError: If the project does not exist or belongs to another user
    """
    if project_id is None:
        return

    result = await session.execute(
        select(ProjectsTable.id).where(
            ProjectsTable.id == project_id,
            ProjectsTable.user_id == str(user_id),
        ),
    )
    if result.scalar_one_or_none() is None:
        raise NotFoundError(f"Project {project_id} not found")
