"""
Historically this enabled the PostgreSQL extensions the domain was expected to
rely on: `vector` (pgvector, reserved for a dormant SectionVersion.embedding,
DP-05) and `pg_trgm` (trigram similarity for section matching, docs/plan/05 §4).

Neither was ever used — no VectorField was declared and section matching went
with exact hashes plus difflib — and the project moved to MySQL 8, which has no
equivalent of either. The migration stays as an empty step because
core/0002_initial depends on it and its number is baked into the graph.
"""

from django.db import migrations


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = []
