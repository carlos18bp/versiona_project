"""
PostgreSQL trigger enforcing I2a/I2 at the database layer (defense in depth —
docs/plan/02 §5, docs/audit/03 C2/C4):

- UPDATE: once a version is READY its frozen identity/content columns cannot
  change (the service-layer guard in DocumentVersion.save() is the first
  line; this survives raw SQL and future internal callers).
- DELETE: physical deletion is rejected unless the row went through the trash
  first (`deleted_at IS NOT NULL`). The 30-day grace window and the
  no-seals/no-approved conditions are enforced by the purge service (the
  seal-existence trigger joins in It3 when the Seal table exists).

No-op on non-PostgreSQL backends.
"""

from django.db import migrations

CREATE = """
CREATE OR REPLACE FUNCTION versiona_version_guard() RETURNS trigger AS $$
BEGIN
  IF TG_OP = 'UPDATE' THEN
    IF OLD.analysis_status = 'ready' AND (
        NEW.document_id IS DISTINCT FROM OLD.document_id OR
        NEW.number IS DISTINCT FROM OLD.number OR
        NEW.sha256 IS DISTINCT FROM OLD.sha256 OR
        NEW.file_key IS DISTINCT FROM OLD.file_key OR
        NEW.size_bytes IS DISTINCT FROM OLD.size_bytes OR
        NEW.page_count IS DISTINCT FROM OLD.page_count OR
        NEW.author_id IS DISTINCT FROM OLD.author_id OR
        NEW.config_version_id IS DISTINCT FROM OLD.config_version_id OR
        NEW.source_scenario IS DISTINCT FROM OLD.source_scenario
    ) THEN
      RAISE EXCEPTION 'I2a: frozen columns of an analyzed version cannot change';
    END IF;
    RETURN NEW;
  ELSIF TG_OP = 'DELETE' THEN
    IF OLD.deleted_at IS NULL THEN
      RAISE EXCEPTION 'I2: physical delete requires the trash flow first';
    END IF;
    RETURN OLD;
  END IF;
  RETURN NULL;
END $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_versiona_version_guard ON documents_documentversion;
CREATE TRIGGER trg_versiona_version_guard
  BEFORE UPDATE OR DELETE ON documents_documentversion
  FOR EACH ROW EXECUTE FUNCTION versiona_version_guard();
"""

DROP = """
DROP TRIGGER IF EXISTS trg_versiona_version_guard ON documents_documentversion;
DROP FUNCTION IF EXISTS versiona_version_guard();
"""


def create_trigger(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    schema_editor.execute(CREATE)


def drop_trigger(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    schema_editor.execute(DROP)


class Migration(migrations.Migration):
    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_trigger, drop_trigger),
    ]
