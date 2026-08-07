"""add usage tracking columns to memories (decay engine)

Revision ID: 20260704_usage_tracking
Revises: 20260408_provenance_all
Create Date: 2026-07-04

Adds two columns to the `memories` table for the forgetful-hulkito decay
engine (plan `native_memory_decay_engine`):

- `access_count` (INTEGER NOT NULL DEFAULT 0) — incremented each time a
  memory is returned by a real read path (query_memory final results,
  get_memory). Mutated only by the internal `record_memory_access`
  repository method so `updated_at` is not distorted.
- `last_accessed_at` (DATETIME WITH TIME ZONE, nullable) — last time the
  memory was returned by a read path. Nullable because existing rows have
  never been accessed through the new path.

Also adds an index `ix_memories_last_accessed_at` to support the
`get_decay_candidates` query.

Both columns are backwards-compatible: existing rows get `access_count=0`
and `last_accessed_at=NULL`, and the decay formula treats NULL
`last_accessed_at` as `updated_at ?? created_at`.
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260704_usage_tracking"
down_revision: str | Sequence[str] | None = "20260408_provenance_all"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add access_count + last_accessed_at columns and index."""
    op.add_column(
        "memories",
        sa.Column("access_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "memories",
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_memories_last_accessed_at",
        "memories",
        ["last_accessed_at"],
    )


def downgrade() -> None:
    """Remove access_count + last_accessed_at columns and index."""
    op.drop_index("ix_memories_last_accessed_at", table_name="memories")
    op.drop_column("memories", "last_accessed_at")
    op.drop_column("memories", "access_count")
