"""add last_encoding_point to projects

Revision ID: 20260822_project_encoding_point
Revises: 20260704_usage_tracking
Create Date: 2026-08-22

Adds a nullable `last_encoding_point` column to the `projects` table.
This opaque, caller-managed checkpoint records the last point through
which memories were encoded for a project (e.g. a Git commit SHA).
The server never interprets or advances it.
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260822_project_encoding_point"
down_revision: str | Sequence[str] | None = "20260704_usage_tracking"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add last_encoding_point column to projects table."""
    op.add_column(
        "projects",
        sa.Column("last_encoding_point", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    """Remove last_encoding_point column from projects table."""
    op.drop_column("projects", "last_encoding_point")
