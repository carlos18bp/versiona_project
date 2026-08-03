"""B2 content search — the searchable projection of a section body.

Originally a PostgreSQL `SearchVectorField` plus a GIN index. On MySQL the
column is plain text holding accent-folded, Spanish-stemmed tokens (built by
documents.search.build_search_text), and the index is FULLTEXT, created in 0004
because Django has no index class that can declare it.

The file keeps its original name: documents/0004 and reviews/0003_certificate
depend on this label.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0002_version_guard_trigger'),
    ]

    operations = [
        migrations.AddField(
            model_name='sectionversion',
            name='search_text',
            field=models.TextField(blank=True, default='', editable=False),
        ),
    ]
