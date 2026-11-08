"""Add Postgres tsvector column and trigger for hybrid keyword search.

Revision ID: 20261103_memory_search_tsv
Revises: 20261008_plan_external_ref
"""

from sqlalchemy import text

from alembic import op
from app.config.settings import settings

revision = "20261103_memory_search_tsv"
down_revision = "20261008_plan_external_ref"
branch_labels = None
depends_on = None

# Dual to_tsvector: keep the simple-parser lexemes and also index the
# punctuation/underscore-split form so search_tsv agrees with
# app.utils.keyword_query (_RUN = [^\W_]+).
_CREATE_FIELD_TSV = """
CREATE OR REPLACE FUNCTION memory_search_field_tsv(raw text) RETURNS tsvector
LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$
  SELECT to_tsvector('simple', coalesce(raw, ''))
      || to_tsvector(
           'simple',
           regexp_replace(coalesce(raw, ''), '[^[:alnum:]]+', ' ', 'g')
         );
$$;
"""

_CREATE_FUNCTION = """
CREATE OR REPLACE FUNCTION memories_search_tsv_update() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  NEW.search_tsv :=
    memory_search_field_tsv(NEW.title)
    || memory_search_field_tsv(NEW.content)
    || memory_search_field_tsv(NEW.context)
    || memory_search_field_tsv(array_to_string(coalesce(NEW.keywords, '{}'), ' '))
    || memory_search_field_tsv(array_to_string(coalesce(NEW.tags, '{}'), ' '));
  RETURN NEW;
END $$;
"""

_BACKFILL = """
UPDATE memories SET search_tsv =
  memory_search_field_tsv(title)
  || memory_search_field_tsv(content)
  || memory_search_field_tsv(context)
  || memory_search_field_tsv(array_to_string(coalesce(keywords, '{}'), ' '))
  || memory_search_field_tsv(array_to_string(coalesce(tags, '{}'), ' '))
"""


def upgrade() -> None:
    if settings.DATABASE != "Postgres":
        return

    op.execute(text("ALTER TABLE memories ADD COLUMN IF NOT EXISTS search_tsv tsvector"))
    op.execute(text(_CREATE_FIELD_TSV))
    op.execute(text(_CREATE_FUNCTION))
    op.execute(text("DROP TRIGGER IF EXISTS memories_search_tsv_trg ON memories"))
    op.execute(
        text(
            """
            CREATE TRIGGER memories_search_tsv_trg
            BEFORE INSERT OR UPDATE OF title, content, context, keywords, tags
            ON memories FOR EACH ROW
            EXECUTE FUNCTION memories_search_tsv_update()
            """,
        ),
    )
    op.execute(
        text("CREATE INDEX IF NOT EXISTS ix_memories_search_tsv ON memories USING gin (search_tsv)"),
    )
    op.execute(text(_BACKFILL))


def downgrade() -> None:
    if settings.DATABASE != "Postgres":
        return

    op.execute(text("DROP INDEX IF EXISTS ix_memories_search_tsv"))
    op.execute(text("DROP TRIGGER IF EXISTS memories_search_tsv_trg ON memories"))
    op.execute(text("DROP FUNCTION IF EXISTS memories_search_tsv_update()"))
    op.execute(text("DROP FUNCTION IF EXISTS memory_search_field_tsv(text)"))
    op.execute(text("ALTER TABLE memories DROP COLUMN IF EXISTS search_tsv"))
