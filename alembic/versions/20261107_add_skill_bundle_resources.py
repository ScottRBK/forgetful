"""Preserve portable skill package membership and paths on both databases."""
import sqlalchemy as sa

from alembic import op

revision = "20261107_skill_bundle_resources"
down_revision = "20261008_plan_external_ref"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "skill_bundle_resources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("skill_id", sa.Integer(), sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("path", sa.String(500), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="SET NULL")),
        sa.Column("code_artifact_id", sa.Integer(), sa.ForeignKey("code_artifacts.id", ondelete="SET NULL")),
        sa.Column("file_id", sa.Integer(), sa.ForeignKey("files.id", ondelete="SET NULL")),
        sa.UniqueConstraint("skill_id", "path", name="uq_skill_bundle_path"),
        sa.CheckConstraint(
            "(kind = 'document' AND code_artifact_id IS NULL AND file_id IS NULL) OR (kind = 'code_artifact' AND document_id IS NULL AND file_id IS NULL) OR (kind = 'file' AND document_id IS NULL AND code_artifact_id IS NULL)",
            name="ck_skill_bundle_resource_kind",
        ),
    )


def downgrade() -> None:
    op.drop_table("skill_bundle_resources")
