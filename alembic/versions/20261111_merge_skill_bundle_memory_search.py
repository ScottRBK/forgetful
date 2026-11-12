"""Merge skill bundle and memory search migrations.

Revision ID: 20261111_skill_bundle_merge
Revises: 20261107_skill_bundle_resources, 20261103_memory_search_tsv
"""

revision = "20261111_skill_bundle_merge"
down_revision = ("20261107_skill_bundle_resources", "20261103_memory_search_tsv")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
