"""Trash rules (kit 3 — B4/C4, tensions T4/T5). Scenario ids per docs/audit/03."""

import pytest
from freezegun import freeze_time

from documents.models import Document, DocumentVersion
from documents.services import trash_service
from documents.services.version_service import DomainError
from reviews.models import Seal


@pytest.fixture
def doc_and_version(document_with_versions):
    document, versions = document_with_versions(n_versions=1)
    return document, versions[0]


@pytest.mark.django_db
@pytest.mark.escenario('C4-F01')
def test_latest_draft_version_goes_to_trash(doc_and_version, versiona_context):
    document, version = doc_and_version

    trash_service.trash_version(version, versiona_context.users['editor'])

    assert DocumentVersion.objects.filter(pk=version.pk).count() == 0
    assert DocumentVersion.all_objects.get(pk=version.pk).is_trashed


@pytest.mark.django_db
@pytest.mark.escenario('C4-E01')
def test_approved_version_is_never_trash_eligible(doc_and_version, versiona_context):
    document, version = doc_and_version
    DocumentVersion.all_objects.filter(pk=version.pk).update(is_approved=True)
    version.refresh_from_db()

    with pytest.raises(DomainError) as excinfo:
        trash_service.trash_version(version, versiona_context.users['admin'])

    assert excinfo.value.status_code == 409


@pytest.mark.django_db
@pytest.mark.escenario('C4-E02')
def test_non_latest_version_cannot_be_trashed(document_with_versions, versiona_context):
    document, versions = document_with_versions(n_versions=2)

    with pytest.raises(DomainError) as excinfo:
        trash_service.trash_version(versions[0], versiona_context.users['editor'])

    assert excinfo.value.status_code == 409


@pytest.mark.django_db
@pytest.mark.escenario('C4-F02')
def test_restore_returns_version_to_timeline(doc_and_version, versiona_context):
    document, version = doc_and_version
    trash_service.trash_version(version, versiona_context.users['editor'])
    version.refresh_from_db()

    trash_service.restore_version(version, versiona_context.users['editor'])

    assert DocumentVersion.objects.filter(pk=version.pk).count() == 1


@pytest.mark.django_db
@pytest.mark.escenario('C4-E03')
def test_restore_blocked_when_newer_version_exists(document_with_versions, versiona_context):
    document, versions = document_with_versions(n_versions=1)
    trash_service.trash_version(versions[0], versiona_context.users['editor'])
    DocumentVersion.objects.create(
        document=document, number=2, sha256='b' * 64,
        file_key='test/x/v2/original.pdf',
        analysis_status=DocumentVersion.AnalysisStatus.READY,
        config_version=versiona_context.config,
    )
    document.latest_number = 2
    document.save(update_fields=['latest_number'])
    versions[0].refresh_from_db()

    with pytest.raises(DomainError) as excinfo:
        trash_service.restore_version(versions[0], versiona_context.users['editor'])

    assert excinfo.value.status_code == 409


@pytest.mark.django_db
@pytest.mark.escenario('C4-A01')
def test_purge_removes_expired_and_number_is_never_reused(doc_and_version, versiona_context, settings):
    settings.TRASH_RETENTION_DAYS = 30
    document, version = doc_and_version
    with freeze_time('2026-06-01'):
        trash_service.trash_version(version, versiona_context.users['editor'])

    with freeze_time('2026-07-05'):
        counts = trash_service.purge_expired()

    assert counts['versions'] == 1
    assert DocumentVersion.all_objects.filter(pk=version.pk).count() == 0
    # I1 tombstone: latest_number never decreases → next upload is v2
    document.refresh_from_db()
    assert document.latest_number == 1


@pytest.mark.django_db
@pytest.mark.escenario('B4-F02')
def test_trash_project_requires_exact_name_confirmation(versiona_context):
    with pytest.raises(DomainError, match='nombre exacto'):
        trash_service.trash_project(
            versiona_context.project, 'nombre-equivocado', versiona_context.users['admin']
        )


@pytest.mark.django_db
@pytest.mark.escenario('B4-E01')
def test_project_with_approved_version_only_archivable(document_with_versions, versiona_context):
    document, versions = document_with_versions(n_versions=1)
    DocumentVersion.all_objects.filter(pk=versions[0].pk).update(is_approved=True)

    with pytest.raises(DomainError) as excinfo:
        trash_service.trash_project(
            versiona_context.project, versiona_context.project.name,
            versiona_context.users['admin'],
        )

    assert excinfo.value.status_code == 409


@pytest.mark.django_db
@pytest.mark.escenario('B4-F01')
def test_archive_makes_project_read_only_and_reversible(versiona_context):
    admin = versiona_context.users['admin']

    trash_service.archive_project(versiona_context.project, admin)
    versiona_context.project.refresh_from_db()
    assert versiona_context.project.is_read_only is True

    trash_service.unarchive_project(versiona_context.project, admin)
    versiona_context.project.refresh_from_db()
    assert versiona_context.project.is_read_only is False


@pytest.mark.django_db
@pytest.mark.escenario('C4-F01')
def test_trash_document_without_sealed_versions_goes_to_trash(doc_and_version, versiona_context):
    document, version = doc_and_version

    trash_service.trash_document(document, versiona_context.users['admin'])

    assert Document.objects.filter(pk=document.pk).count() == 0
    assert Document.all_objects.get(pk=document.pk).is_trashed


@pytest.mark.django_db
@pytest.mark.escenario('C4-E01')
def test_document_with_sealed_version_cannot_be_trashed(doc_and_version, versiona_context):
    document, version = doc_and_version
    Seal.objects.create(
        document_version=version, reviewer=versiona_context.users['reviewer'],
        covers_all=True, signed_payload={}, signature='firma', key_id='k-test',
    )

    with pytest.raises(DomainError) as excinfo:
        trash_service.trash_document(document, versiona_context.users['admin'])

    assert excinfo.value.status_code == 409
    assert 'archiva el proyecto' in str(excinfo.value)


@pytest.mark.django_db
@pytest.mark.escenario('C4-F02')
def test_restore_version_not_in_trash_is_rejected(doc_and_version, versiona_context):
    document, version = doc_and_version

    with pytest.raises(DomainError) as excinfo:
        trash_service.restore_version(version, versiona_context.users['editor'])

    assert excinfo.value.status_code == 400
    assert str(excinfo.value) == 'La versión no está en la papelera.'


@pytest.mark.django_db
@pytest.mark.escenario('C4-E03')
def test_restore_version_requires_restoring_trashed_document_first(doc_and_version, versiona_context):
    document, version = doc_and_version
    editor = versiona_context.users['editor']
    trash_service.trash_version(version, editor)
    version.refresh_from_db()
    trash_service.trash_document(document, versiona_context.users['admin'])

    with pytest.raises(DomainError) as excinfo:
        trash_service.restore_version(version, editor)

    assert excinfo.value.status_code == 409
    assert str(excinfo.value) == 'Restaura primero el documento/proyecto contenedor.'


@pytest.mark.django_db
@pytest.mark.escenario('C4-F02')
def test_restore_document_not_in_trash_is_rejected(doc_and_version, versiona_context):
    document, _ = doc_and_version

    with pytest.raises(DomainError) as excinfo:
        trash_service.restore_document(document, versiona_context.users['admin'])

    assert excinfo.value.status_code == 400
    assert str(excinfo.value) == 'El documento no está en la papelera.'


@pytest.mark.django_db
@pytest.mark.escenario('B4-F03')
def test_restore_document_requires_restoring_project_first(doc_and_version, versiona_context):
    document, _ = doc_and_version
    admin = versiona_context.users['admin']
    trash_service.trash_document(document, admin)
    trash_service.trash_project(versiona_context.project, versiona_context.project.name, admin)

    with pytest.raises(DomainError) as excinfo:
        trash_service.restore_document(document, admin)

    assert excinfo.value.status_code == 409
    assert str(excinfo.value) == 'Restaura primero el proyecto.'


@pytest.mark.django_db
@pytest.mark.escenario('C4-F02')
def test_restore_document_returns_it_to_the_project(doc_and_version, versiona_context):
    document, _ = doc_and_version
    admin = versiona_context.users['admin']
    trash_service.trash_document(document, admin)

    trash_service.restore_document(document, admin)

    document.refresh_from_db()
    assert document.is_trashed is False
    assert Document.objects.filter(pk=document.pk).count() == 1


@pytest.mark.django_db
@pytest.mark.escenario('B4-F03')
def test_restore_project_not_in_trash_is_rejected(versiona_context):
    with pytest.raises(DomainError) as excinfo:
        trash_service.restore_project(versiona_context.project, versiona_context.users['admin'])

    assert excinfo.value.status_code == 400
    assert str(excinfo.value) == 'El proyecto no está en la papelera.'


@pytest.mark.django_db
@pytest.mark.escenario('B4-A02')
def test_purge_deletes_expired_document_with_its_versions(doc_and_version, versiona_context, settings):
    settings.TRASH_RETENTION_DAYS = 30
    document, version = doc_and_version
    with freeze_time('2026-06-01'):
        trash_service.trash_document(document, versiona_context.users['admin'])

    with freeze_time('2026-07-05'):
        counts = trash_service.purge_expired()

    assert counts == {'versions': 0, 'documents': 1, 'projects': 0}
    assert Document.all_objects.filter(pk=document.pk).count() == 0
    assert DocumentVersion.all_objects.filter(pk=version.pk).count() == 0


@pytest.mark.django_db
@pytest.mark.escenario('B4-A02')
def test_purge_deletes_expired_project_cascade(doc_and_version, versiona_context, settings):
    from projects.models import Project

    settings.TRASH_RETENTION_DAYS = 30
    document, version = doc_and_version
    with freeze_time('2026-06-01'):
        trash_service.trash_project(
            versiona_context.project, versiona_context.project.name,
            versiona_context.users['admin'],
        )

    with freeze_time('2026-07-05'):
        counts = trash_service.purge_expired()

    assert counts == {'versions': 0, 'documents': 0, 'projects': 1}
    assert Project.all_objects.filter(pk=versiona_context.project.pk).count() == 0
    assert Document.all_objects.filter(pk=document.pk).count() == 0
    assert DocumentVersion.all_objects.filter(pk=version.pk).count() == 0


@pytest.mark.django_db
@pytest.mark.escenario('B4-E02')
def test_project_restore_with_live_slug_collision_is_rejected(versiona_context):
    from projects.models import Project

    admin = versiona_context.users['admin']
    trash_service.trash_project(versiona_context.project, versiona_context.project.name, admin)
    versiona_context.project.refresh_from_db()
    Project.objects.create(
        organization=versiona_context.org, name='Torre Central', slug='torre-central'
    )

    with pytest.raises(DomainError) as excinfo:
        trash_service.restore_project(versiona_context.project, admin)

    assert excinfo.value.status_code == 409


@pytest.mark.django_db
@pytest.mark.escenario('B4-F03')
def test_restore_document_renames_slug_when_an_alive_document_took_it(
    doc_and_version, versiona_context
):
    document, _ = doc_and_version
    original_slug = document.slug
    trash_service.trash_document(document, versiona_context.users['editor'])
    Document.objects.create(
        project=document.project, title=document.title, slug=original_slug
    )

    trash_service.restore_document(
        Document.all_objects.get(pk=document.pk), versiona_context.users['editor']
    )

    restored = Document.objects.get(pk=document.pk)
    assert restored.slug == f'{original_slug}-restaurado'
    assert Document.objects.filter(slug=original_slug).count() == 1
