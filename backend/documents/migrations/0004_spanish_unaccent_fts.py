"""B2 content search: the FULLTEXT index, plus a backfill of existing rows.

Users type "interventoría"; PDFs may carry "interventoria" (and vice versa),
and "obligación" has to find "obligaciones". PostgreSQL solved both halves in
the database with a `spanish_unaccent` TEXT SEARCH CONFIGURATION chaining
`unaccent` into `spanish_stem`. MySQL 8 has neither, so folding and stemming
happen in Python (documents.search) and the database keeps only the inverted
index.

Django cannot declare a FULLTEXT index, hence raw DDL. The backfill has to run
row by row for the same reason the column exists: build_search_text is Python
and cannot be expressed in SQL.
"""

from django.db import migrations

CREATE_FULLTEXT = (
    'CREATE FULLTEXT INDEX sectionversion_fts ON documents_sectionversion (search_text)'
)
DROP_FULLTEXT = 'DROP INDEX sectionversion_fts ON documents_sectionversion'


def _require_mysql(schema_editor, action):
    vendor = schema_editor.connection.vendor
    if vendor != 'mysql':
        raise NotImplementedError(
            f'{action}: the B2 search index is written for MySQL FULLTEXT; '
            f'{vendor} would migrate cleanly with content search unindexed.'
        )


def forwards(apps, schema_editor):
    _require_mysql(schema_editor, 'create_fulltext_index')
    schema_editor.execute(CREATE_FULLTEXT)

    from documents.search import build_search_text

    SectionVersion = apps.get_model('documents', 'SectionVersion')
    pending = []
    for snapshot in SectionVersion.objects.exclude(normalized_text='').iterator():
        snapshot.search_text = build_search_text(snapshot.normalized_text)
        pending.append(snapshot)
        if len(pending) >= 500:
            SectionVersion.objects.bulk_update(pending, ['search_text'])
            pending = []
    if pending:
        SectionVersion.objects.bulk_update(pending, ['search_text'])


def backwards(apps, schema_editor):
    _require_mysql(schema_editor, 'drop_fulltext_index')
    schema_editor.execute(DROP_FULLTEXT)


class Migration(migrations.Migration):
    # CREATE FULLTEXT INDEX is DDL and MySQL cannot roll it back.
    atomic = False

    dependencies = [
        ('documents', '0003_sectionversion_search_vector_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
