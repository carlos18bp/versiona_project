"""
Enable the PostgreSQL extensions the domain relies on (docs/plan/02 §6):
- vector (pgvector): SectionVersion.embedding, dormant until V2 (DP-05).
- pg_trgm: trigram similarity for section matching (docs/plan/05 §4).

Both are trusted extensions, so the database owner can create them (works on
CI service containers and on pytest-created test databases). No-op on
non-PostgreSQL backends.
"""

from django.db import migrations


def create_extensions(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    schema_editor.execute('CREATE EXTENSION IF NOT EXISTS vector')
    schema_editor.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.RunPython(create_extensions, migrations.RunPython.noop),
    ]
