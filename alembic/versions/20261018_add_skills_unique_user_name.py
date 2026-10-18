"""Enforce one skill name per user.

Revision ID: 20261018_skill_unique_name
Revises: 20261008_plan_external_ref

Skill names were only checked in the service layer, so concurrent creates or
a rename could leave a user with several skills of the same name. Existing
duplicates are renamed (the oldest skill keeps its name, later ones get a
numeric suffix) so that the unique index can always be created.
"""

import sqlalchemy as sa

from alembic import op

revision = "20261018_skill_unique_name"
down_revision = "20261008_plan_external_ref"
branch_labels = None
depends_on = None

NAME_MAX_LENGTH = 64  # skills.name is String(64)


def _unique_name(connection, skill_id: int, name: str) -> str:
    """First free '<name>-N' (N >= 2) among the names of the skill's owner."""
    suffix = 2
    while True:
        tail = f"-{suffix}"
        candidate = f"{name[: NAME_MAX_LENGTH - len(tail)].rstrip('-')}{tail}"
        taken = connection.execute(
            sa.text(
                "SELECT 1 FROM skills WHERE name = :name AND user_id = "
                "(SELECT user_id FROM skills WHERE id = :id)",
            ),
            {"name": candidate, "id": skill_id},
        ).first()
        if taken is None:
            return candidate
        suffix += 1


def _rename_duplicate_skills(connection) -> None:
    duplicates = connection.execute(
        sa.text(
            "SELECT s.id, s.name FROM skills s WHERE EXISTS ("
            "SELECT 1 FROM skills o "
            "WHERE o.user_id = s.user_id AND o.name = s.name AND o.id < s.id"
            ") ORDER BY s.id",
        ),
    ).all()
    for skill_id, name in duplicates:
        connection.execute(
            sa.text("UPDATE skills SET name = :name WHERE id = :id"),
            {"name": _unique_name(connection, skill_id, name), "id": skill_id},
        )


def upgrade() -> None:
    _rename_duplicate_skills(op.get_bind())
    op.create_index("ix_skills_user_name", "skills", ["user_id", "name"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_skills_user_name", table_name="skills")
