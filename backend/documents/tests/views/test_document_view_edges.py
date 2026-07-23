"""Edge matrix for document/version endpoints (C1/C3/C4 guards, B4 read-only
locks and the C3-L02 plan lock) over engine-independent fixtures."""

from unittest.mock import patch

import pytest
from freezegun import freeze_time

from documents.models import Document, DocumentVersion
from documents.services import trash_service
from projects.models import Project


@pytest.fixture
def doc_with_version(document_with_versions):
    document, versions = document_with_versions(n_versions=1)
    return document, versions[0]


@pytest.mark.django_db
@pytest.mark.escenario('C1-F01')
def test_documents_list_returns_paginated_documents(client_as, versiona_context, doc_with_version):
    document, _ = doc_with_version

    response = client_as('viewer').get(
        f'/api/projects/{versiona_context.project.public_id}/documents/'
    )

    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['public_id'] == str(document.public_id)


@pytest.mark.django_db
@pytest.mark.escenario('C1-F01')
def test_documents_list_filters_by_title_search(client_as, versiona_context, document_with_versions):
    document_with_versions(n_versions=1, document_slug='contrato')
    document_with_versions(n_versions=1, document_slug='acta')

    response = client_as('viewer').get(
        f'/api/projects/{versiona_context.project.public_id}/documents/', {'q': 'acta'}
    )

    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['title'] == 'Acta'


@pytest.mark.django_db
@pytest.mark.escenario('B4-L01')
def test_create_document_in_archived_project_is_rejected(client_as, versiona_context):
    project = versiona_context.project
    project.status = Project.Status.ARCHIVED
    project.save(update_fields=['status'])

    response = client_as('editor').post(
        f'/api/projects/{project.public_id}/documents/', {'title': 'Nuevo'}
    )

    assert response.status_code == 409
    assert response.data['error'] == (
        'El proyecto está archivado o en la papelera: es de solo lectura.'
    )


@pytest.mark.django_db
@pytest.mark.escenario('C3-F01')
def test_document_detail_returns_document_payload(client_as, doc_with_version):
    document, _ = doc_with_version

    response = client_as('viewer').get(f'/api/documents/{document.public_id}/')

    assert response.status_code == 200
    assert response.data['title'] == 'Contrato'
    assert response.data['latest_number'] == 1


@pytest.mark.django_db
@pytest.mark.escenario('C4-P02')
def test_document_delete_requires_admin_role(client_as, doc_with_version):
    document, _ = doc_with_version

    response = client_as('editor').delete(f'/api/documents/{document.public_id}/')

    assert response.status_code == 403
    assert response.data['error'] == 'Se requiere rol admin.'


@pytest.mark.django_db
@pytest.mark.escenario('C4-F01')
def test_admin_deletes_document_into_trash(client_as, doc_with_version):
    document, _ = doc_with_version

    response = client_as('admin').delete(f'/api/documents/{document.public_id}/')

    assert response.status_code == 204
    assert Document.objects.filter(pk=document.pk).count() == 0
    assert Document.all_objects.get(pk=document.pk).is_trashed


@pytest.mark.django_db
@pytest.mark.escenario('C4-E01')
def test_delete_document_with_approved_version_is_rejected(client_as, doc_with_version):
    document, version = doc_with_version
    DocumentVersion.all_objects.filter(pk=version.pk).update(is_approved=True)

    response = client_as('admin').delete(f'/api/documents/{document.public_id}/')

    assert response.status_code == 409
    assert 'archiva el proyecto' in response.data['error']


@pytest.mark.django_db
@pytest.mark.escenario('C4-F02')
def test_admin_restores_trashed_document_via_api(client_as, versiona_context, doc_with_version):
    document, _ = doc_with_version
    trash_service.trash_document(document, versiona_context.users['admin'])

    response = client_as('admin').post(f'/api/documents/{document.public_id}/restore/')

    assert response.status_code == 200
    assert Document.objects.filter(pk=document.pk).count() == 1


@pytest.mark.django_db
@pytest.mark.escenario('C4-F02')
def test_restore_document_not_in_trash_returns_400(client_as, doc_with_version):
    document, _ = doc_with_version

    response = client_as('admin').post(f'/api/documents/{document.public_id}/restore/')

    assert response.status_code == 400
    assert response.data['error'] == 'El documento no está en la papelera.'


@pytest.mark.django_db
@pytest.mark.escenario('B4-L01')
def test_upload_intent_on_archived_project_is_rejected(client_as, versiona_context, doc_with_version):
    document, _ = doc_with_version
    project = versiona_context.project
    project.status = Project.Status.ARCHIVED
    project.save(update_fields=['status'])

    response = client_as('editor').post(
        f'/api/documents/{document.public_id}/versions/upload_intent/'
    )

    assert response.status_code == 409
    assert 'solo lectura' in response.data['error']


@pytest.mark.django_db
@pytest.mark.escenario('C2-E02')
def test_edit_message_on_approved_version_is_rejected(client_as, doc_with_version):
    document, version = doc_with_version
    DocumentVersion.all_objects.filter(pk=version.pk).update(is_approved=True)

    response = client_as('editor').patch(
        f'/api/versions/{version.public_id}/', {'message': 'tarde'}, format='json'
    )

    assert response.status_code == 409
    assert 'congelado' in response.data['error']


@pytest.mark.django_db
@pytest.mark.escenario('C4-P02')
def test_viewer_cannot_delete_a_version(client_as, doc_with_version):
    _, version = doc_with_version

    response = client_as('viewer').delete(f'/api/versions/{version.public_id}/')

    assert response.status_code == 403
    assert response.data['error'] == 'Solo el autor o un admin eliminan un borrador.'


@pytest.mark.django_db
@pytest.mark.escenario('C4-E02')
def test_delete_non_latest_version_returns_conflict(client_as, document_with_versions):
    document, versions = document_with_versions(n_versions=2)

    response = client_as('editor').delete(f'/api/versions/{versions[0].public_id}/')

    assert response.status_code == 409
    assert response.data['error'] == 'Solo la última versión del documento puede eliminarse.'


@pytest.mark.django_db
@pytest.mark.escenario('C4-P02')
def test_restore_version_by_non_author_editor_is_rejected(
    api_client, versiona_context, doc_with_version, django_user_model
):
    from orgs.models import OrganizationMembership
    from projects.models import ProjectMembership

    document, version = doc_with_version
    trash_service.trash_version(version, versiona_context.users['editor'])
    otro = django_user_model.objects.create_user(
        email='otro-editor@versiona.test', password='secreta123', first_name='Otro'
    )
    OrganizationMembership.objects.create(
        organization=versiona_context.org, user=otro,
        role=OrganizationMembership.Role.MEMBER,
    )
    ProjectMembership.objects.create(
        project=versiona_context.project, user=otro, role=ProjectMembership.Role.EDITOR
    )
    api_client.force_authenticate(user=otro)

    response = api_client.post(f'/api/versions/{version.public_id}/restore/')

    assert response.status_code == 403
    assert response.data['error'] == 'Solo el autor o un admin restauran.'


@pytest.mark.django_db
@pytest.mark.escenario('C4-F02')
def test_restore_version_not_in_trash_returns_400(client_as, doc_with_version):
    _, version = doc_with_version

    response = client_as('editor').post(f'/api/versions/{version.public_id}/restore/')

    assert response.status_code == 400
    assert response.data['error'] == 'La versión no está en la papelera.'


@pytest.mark.django_db
@pytest.mark.escenario('C3-L02')
def test_download_of_locked_history_version_returns_402_with_upgrade(
    client_as, versiona_context, document_with_versions
):
    versiona_context.org.plan = 'free'
    versiona_context.org.save(update_fields=['plan'])
    with freeze_time('2026-01-01'):
        document, versions = document_with_versions(n_versions=2)

    with freeze_time('2026-03-01'):
        response = client_as('viewer').get(f'/api/versions/{versions[0].public_id}/download/')

    assert response.status_code == 402
    assert response.data['upgrade'] is True
    assert 'bloqueado' in response.data['error']


@pytest.mark.django_db
@pytest.mark.escenario('C3-F02')
def test_version_file_returns_inline_presigned_url(client_as, doc_with_version):
    _, version = doc_with_version

    with patch(
        'documents.services.storage_service.presign_view',
        return_value='https://minio.test/inline.pdf',
    ) as presign:
        response = client_as('viewer').get(f'/api/versions/{version.public_id}/file/')

    assert response.status_code == 200
    assert response.data['url'] == 'https://minio.test/inline.pdf'
    presign.assert_called_once_with(version.file_key, 'application/pdf')
