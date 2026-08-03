"""
MySQL triggers enforcing I2a/I2 at the database layer (defense in depth —
docs/plan/02 §5, docs/audit/03 C2/C4):

- UPDATE: once a version is READY its frozen identity/content columns cannot
  change (the service-layer guard in DocumentVersion.save() is the first
  line; this survives raw SQL and future internal callers).
- DELETE: physical deletion is rejected unless the row went through the trash
  first (`deleted_at IS NOT NULL`). The 30-day grace window and the
  no-seals/no-approved conditions are enforced by the purge service.

Ported from PL/pgSQL when the project moved to MySQL 8. Three syntax facts
drive the shape of this file:

- MySQL cannot bind two events to one trigger, so the single PG trigger becomes
  two.
- There is no `IS DISTINCT FROM`; `NOT (a <=> b)` is the NULL-safe equivalent.
- `RAISE EXCEPTION` becomes `SIGNAL SQLSTATE '45000'`, which surfaces as MySQL
  error 1644 and reaches Django as an OperationalError (a DatabaseError, which
  is what `delete_fake_data` catches).

Each statement goes through its own `schema_editor.execute()` call: mysqlclient
does not enable CLIENT.MULTI_STATEMENTS. The `;` inside `BEGIN … END` is fine —
the server parses the compound body as one statement. Never emit `DELIMITER`,
which is a directive of the `mysql` CLI and not SQL.
"""

from django.db import migrations

FROZEN_COLUMNS = (
    'document_id',
    'number',
    'sha256',
    'file_key',
    'size_bytes',
    'page_count',
    'author_id',
    'config_version_id',
    'source_scenario',
)

_FROZEN_CHANGED = ' OR\n      '.join(
    f'NOT (NEW.{column} <=> OLD.{column})' for column in FROZEN_COLUMNS
)

CREATE_UPDATE_TRIGGER = f"""
CREATE TRIGGER trg_versiona_version_guard_upd
BEFORE UPDATE ON documents_documentversion
FOR EACH ROW
BEGIN
  IF OLD.analysis_status = 'ready' AND (
      {_FROZEN_CHANGED}
  ) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'I2a: frozen columns of an analyzed version cannot change';
  END IF;
END
"""

CREATE_DELETE_TRIGGER = """
CREATE TRIGGER trg_versiona_version_guard_del
BEFORE DELETE ON documents_documentversion
FOR EACH ROW
BEGIN
  IF OLD.deleted_at IS NULL THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'I2: physical delete requires the trash flow first';
  END IF;
END
"""

DROP_UPDATE_TRIGGER = 'DROP TRIGGER IF EXISTS trg_versiona_version_guard_upd'
DROP_DELETE_TRIGGER = 'DROP TRIGGER IF EXISTS trg_versiona_version_guard_del'


def _require_mysql(schema_editor, action):
    """No silent no-op. A backend without these triggers loses I2/I2a with a
    green `migrate`, which is the failure mode this whole port exists to avoid."""
    vendor = schema_editor.connection.vendor
    if vendor != 'mysql':
        raise NotImplementedError(
            f'{action}: the I2/I2a guard is written for MySQL; {vendor} would '
            f'migrate cleanly with the invariant unenforced.'
        )


def create_triggers(apps, schema_editor):
    _require_mysql(schema_editor, 'create_triggers')
    # CREATE OR REPLACE TRIGGER is MariaDB syntax, so drop first.
    schema_editor.execute(DROP_UPDATE_TRIGGER)
    schema_editor.execute(CREATE_UPDATE_TRIGGER)
    schema_editor.execute(DROP_DELETE_TRIGGER)
    schema_editor.execute(CREATE_DELETE_TRIGGER)


def drop_triggers(apps, schema_editor):
    _require_mysql(schema_editor, 'drop_triggers')
    schema_editor.execute(DROP_UPDATE_TRIGGER)
    schema_editor.execute(DROP_DELETE_TRIGGER)


class Migration(migrations.Migration):
    # MySQL cannot roll back DDL, so Django refuses to run raw DDL inside an
    # atomic migration. CREATE TRIGGER is DDL.
    atomic = False

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_triggers, drop_triggers),
    ]
