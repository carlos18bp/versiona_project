"""Integration matrix for document/version endpoints (flows C1/C2/C3/C4 —
docs/audit/03 §3). Upload flows run against real MinIO + eager Celery."""

from pathlib import Path

import pytest

from documents.services import storage_service

TESTDATA = Path(__file__).resolve().parents[4] / 'testdata' / 'pdfs'


@pytest.fixture(autouse=True)
def _test_storage_prefix(settings):
    settings.DJANGO_ENV = 'test'


def documents_url(context):
    return f'/api/projects/{context.project.public_id}/documents/'


def upload_via_api(client, document_public_id, fixture='contrato_v1.pdf', message='entrega'):
    intent = client.post(f'/api/documents/{document_public_id}/versions/upload_intent/')
    assert intent.status_code == 200, intent.data
    key_suffix = intent.data['upload_id']
    from documents.models import Document
    document = Document.objects.get(public_id=document_public_id)
    staging = storage_service.staging_key(document.project.organization, key_suffix)
    storage_service.put_bytes(staging, (TESTDATA / fixture).read_bytes(), 'application/pdf')
    return client.post(
        f'/api/documents/{document_public_id}/versions/complete/',
        {'upload_id': key_suffix, 'message': message},
        format='json',
    )


@pytest.fixture
def api_document(client_as, versiona_context):
    response = client_as('editor').post(documents_url(versiona_context), {'title': 'Contrato'})
    assert response.status_code == 201
    return response.data['public_id']


# ---------------------------------------------------------------------------
# C1 — create document + upload
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.parametrize('actor, expected', [
    pytest.param('editor', 201, id='c1-p01-editor'),
    pytest.param('admin', 201, id='c1-p01-admin'),
    pytest.param('reviewer', 403, id='c1-p02-reviewer'),
    pytest.param('viewer', 403, id='c1-p02-viewer'),
    pytest.param('anonymous', 401, id='c1-p03-anonymous'),
    pytest.param('non_member', 404, id='c1-p04-non-member'),
])
def test_create_document_permission_matrix(client_as, versiona_context, actor, expected):
    response = client_as(actor).post(documents_url(versiona_context), {'title': 'Doc'})

    assert response.status_code == expected


@pytest.mark.django_db
@pytest.mark.escenario('C1-F01')
def test_upload_first_version_via_api_indexes_sections(client_as, versiona_context, api_document):
    response = upload_via_api(client_as('editor'), api_document)

    assert response.status_code == 202
    assert response.data['version']['number'] == 1
    job = client_as('viewer').get(f"/api/jobs/{response.data['job_id']}/")
    assert job.status_code == 200
    assert job.data['status'] == 'done'
    sections = client_as('viewer').get(
        f"/api/versions/{response.data['version']['public_id']}/sections/"
    )
    keys = [s['stable_key'] for s in sections.data['results']]
    assert 'objeto-del-contrato' in keys


@pytest.mark.django_db
@pytest.mark.parametrize('actor, expected', [
    pytest.param('editor', 200, id='c1-upload-p01-editor'),
    pytest.param('reviewer', 403, id='c1-upload-p02-reviewer'),
    pytest.param('anonymous', 401, id='c1-upload-p03-anonymous'),
    pytest.param('non_member', 404, id='c1-upload-p04-non-member'),
])
def test_upload_intent_permission_matrix(client_as, versiona_context, api_document, actor, expected):
    response = client_as(actor).post(f'/api/documents/{api_document}/versions/upload_intent/')

    assert response.status_code == expected


@pytest.mark.django_db
@pytest.mark.escenario('C2-E01')
def test_upload_identical_binary_returns_409(client_as, versiona_context, api_document):
    editor = client_as('editor')
    upload_via_api(editor, api_document)

    duplicate = upload_via_api(editor, api_document)

    assert duplicate.status_code == 409


# ---------------------------------------------------------------------------
# C3 — timeline, download, detail
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.escenario('C3-F01')
def test_timeline_shows_versions_with_thumbs_and_tombstones(client_as, versiona_context, api_document):
    editor = client_as('editor')
    first = upload_via_api(editor, api_document)
    upload_via_api(editor, api_document, 'contrato_v2.pdf', 'segunda')
    # trash v2 to verify the tombstone appears (C4-F01 timeline view)
    from documents.models import DocumentVersion
    v2 = DocumentVersion.objects.get(document__public_id=api_document, number=2)
    trash = editor.delete(f'/api/versions/{v2.public_id}/')
    assert trash.status_code == 204

    timeline = client_as('viewer').get(f'/api/documents/{api_document}/versions/')

    assert timeline.status_code == 200
    rows = timeline.data['results']
    assert [row['number'] for row in rows] == [2, 1]
    assert rows[0]['is_trashed'] is True
    assert rows[1]['is_trashed'] is False
    assert rows[1]['thumb_url']
    assert first.data['version']['number'] == 1


@pytest.mark.django_db
@pytest.mark.escenario('C3-F02')
def test_download_returns_signed_url_and_audits(client_as, versiona_context, api_document):
    editor = client_as('editor')
    uploaded = upload_via_api(editor, api_document)
    version_id = uploaded.data['version']['public_id']

    response = client_as('viewer').get(f'/api/versions/{version_id}/download/')

    assert response.status_code == 200
    assert 'X-Amz-Signature' in response.data['url']
    from audit.models import AuditEvent
    assert AuditEvent.objects.filter(event_type='version.downloaded').exists()


@pytest.mark.django_db
@pytest.mark.parametrize('actor, expected', [
    pytest.param('viewer', 200, id='c3-p01-viewer'),
    pytest.param('anonymous', 401, id='c3-p03-anonymous'),
    pytest.param('non_member', 404, id='c3-p04-non-member'),
])
def test_version_detail_permission_matrix(client_as, versiona_context, api_document, actor, expected):
    uploaded = upload_via_api(client_as('editor'), api_document)
    version_id = uploaded.data['version']['public_id']

    response = client_as(actor).get(f'/api/versions/{version_id}/')

    assert response.status_code == expected


# ---------------------------------------------------------------------------
# C2 — draft message editing (I2b)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.escenario('C2-A01')
def test_author_edits_draft_message(client_as, versiona_context, api_document):
    editor = client_as('editor')
    uploaded = upload_via_api(editor, api_document)
    version_id = uploaded.data['version']['public_id']

    response = editor.patch(
        f'/api/versions/{version_id}/', {'message': 'corregido'}, format='json'
    )

    assert response.status_code == 200
    assert response.data['message'] == 'corregido'


@pytest.mark.django_db
@pytest.mark.parametrize('actor, expected', [
    pytest.param('admin', 200, id='c2-edit-p01-admin'),
    pytest.param('reviewer', 403, id='c2-edit-p02-reviewer'),
    pytest.param('viewer', 403, id='c2-edit-p02-viewer'),
    pytest.param('anonymous', 401, id='c2-edit-p03-anonymous'),
    pytest.param('non_member', 404, id='c2-edit-p04-non-member'),
])
def test_edit_message_permission_matrix(client_as, versiona_context, api_document, actor, expected):
    uploaded = upload_via_api(client_as('editor'), api_document)
    version_id = uploaded.data['version']['public_id']

    response = client_as(actor).patch(
        f'/api/versions/{version_id}/', {'message': 'x'}, format='json'
    )

    assert response.status_code == expected


# ---------------------------------------------------------------------------
# C4 — trash a draft version via API
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.escenario('C4-F02')
def test_trash_and_restore_version_roundtrip(client_as, versiona_context, api_document):
    editor = client_as('editor')
    uploaded = upload_via_api(editor, api_document)
    version_id = uploaded.data['version']['public_id']

    assert editor.delete(f'/api/versions/{version_id}/').status_code == 204

    trash_list = client_as('owner').get(f'/api/orgs/{versiona_context.org.public_id}/trash/')
    assert any(item['type'] == 'version' for item in trash_list.data['results'])

    restored = editor.post(f'/api/versions/{version_id}/restore/')
    assert restored.status_code == 200
    assert restored.data['is_trashed'] is False
