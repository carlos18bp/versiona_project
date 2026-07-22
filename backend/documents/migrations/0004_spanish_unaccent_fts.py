"""B2 content search: accent-insensitive Spanish FTS.

Users type "interventoría"; PDFs may carry "interventoria" (and vice versa).
`unaccent` is a trusted extension since PG13, so the app role can create it.
The custom config chains unaccent → spanish_stem on both indexing and query
sides. Existing rows are backfilled.
"""

from django.db import migrations


def forwards(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute('CREATE EXTENSION IF NOT EXISTS unaccent;')
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_ts_config WHERE cfgname = 'spanish_unaccent'
                ) THEN
                    CREATE TEXT SEARCH CONFIGURATION spanish_unaccent (COPY = spanish);
                    ALTER TEXT SEARCH CONFIGURATION spanish_unaccent
                        ALTER MAPPING FOR hword, hword_part, word
                        WITH unaccent, spanish_stem;
                END IF;
            END
            $$;
        """)
        cursor.execute("""
            UPDATE documents_sectionversion
            SET search_vector = to_tsvector('spanish_unaccent', normalized_text);
        """)


class Migration(migrations.Migration):
    dependencies = [
        ('documents', '0003_sectionversion_search_vector_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
