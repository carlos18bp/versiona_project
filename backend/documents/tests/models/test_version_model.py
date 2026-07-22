"""DocumentVersion invariants at the model/database layer (I1, I2a, trash)."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction

from documents.models import Document, DocumentVersion
from orgs.models import Organization
from projects.models import Project, ProjectConfigVersion


@pytest.fixture
def document(db):
    org = Organization.objects.create(name='Acme', slug='acme')
    project = Project.objects.create(organization=org, name='Torre', slug='torre')
    return Document.objects.create(project=project, title='Contrato', slug='contrato')


def make_version(document, number=1, status=DocumentVersion.AnalysisStatus.READY, **extra):
    config = ProjectConfigVersion.current_for(document.project)
    return DocumentVersion.objects.create(
        document=document,
        number=number,
        sha256=f'{number:064d}',
        file_key=f'test/doc/{document.pk}/v{number}/original.pdf',
        analysis_status=status,
        config_version=config,
        **extra,
    )


@pytest.mark.django_db
def test_version_number_is_unique_per_document(document):
    """I1: the linear history admits no duplicated numbers."""
    make_version(document, number=1)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            make_version(document, number=1)


@pytest.mark.django_db
@pytest.mark.escenario('C2-E02')
def test_frozen_columns_reject_change_after_ready(document):
    """I2a: identity/content columns freeze once the version is analyzed."""
    version = make_version(document, number=1)

    version.sha256 = 'f' * 64

    with pytest.raises(ValidationError, match='I2a'):
        version.save()


@pytest.mark.django_db
def test_message_stays_editable_after_ready(document):
    """I2b: message is NOT part of the frozen set while the version is draft."""
    version = make_version(document, number=1)

    version.message = 'corrige observaciones del revisor 2'
    version.save()

    version.refresh_from_db()
    assert version.message == 'corrige observaciones del revisor 2'


@pytest.mark.django_db
def test_database_trigger_blocks_raw_frozen_update(document):
    """Defense in depth: the PG trigger stops raw SQL, not just the ORM."""
    version = make_version(document, number=1)

    with pytest.raises(Exception, match='I2a'):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    'UPDATE documents_documentversion SET sha256 = %s WHERE id = %s',
                    ['e' * 64, version.pk],
                )


@pytest.mark.django_db
@pytest.mark.escenario('C4-F01')
def test_physical_delete_requires_trash_first(document):
    """I2/T2: DELETE is rejected while the row is alive; allowed after trash."""
    version = make_version(document, number=1)

    with pytest.raises(Exception, match='trash'):
        with transaction.atomic():
            version.delete()

    version.soft_delete()
    version.delete()

    assert DocumentVersion.all_objects.filter(pk=version.pk).count() == 0


@pytest.mark.django_db
def test_is_draft_false_once_approved(document):
    version = make_version(document, number=1, is_approved=True)

    assert version.is_draft is False


@pytest.mark.django_db
def test_trashed_version_keeps_its_number_reserved(document):
    """I1 tombstones: a trashed version still occupies its number."""
    version = make_version(document, number=1)
    version.soft_delete()

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            make_version(document, number=1)
