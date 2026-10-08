"""Add optional external references to plans.

Revision ID: 20261008_plan_external_ref
Revises: 20260822_project_encoding_point
"""

import sqlalchemy as sa

from alembic import op

revision = "20261008_plan_external_ref"
down_revision = "20260822_project_encoding_point"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("plans", sa.Column("external_ref", sa.String(255), nullable=True))
    # A unique index supports multiple NULLs on both backends without rebuilding SQLite tables.
    op.create_index(
        "ix_plans_user_external_ref", "plans", ["user_id", "external_ref"], unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_plans_user_external_ref", table_name="plans")
    op.drop_column("plans", "external_ref")
