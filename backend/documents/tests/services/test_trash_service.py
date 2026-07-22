"""Trash rules (kit 3 — B4/C4, tensions T4/T5). Scenario ids per docs/audit/03."""

import pytest
from freezegun import freeze_time

from documents.models import DocumentVersion
from documents.services import trash_service
from documents.services.version_service import DomainError


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
