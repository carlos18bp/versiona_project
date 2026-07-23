"""C3-A02 negative verification: there is no per-section history ("blame")
endpoint. `versions/{ver}/sections/` lists one version's snapshots only, and
no route serves "in which version did this section change". The underlying
snapshots already carry the evidence a future endpoint would need."""

import uuid
from pathlib import Path

import pytest
from django.urls import Resolver404, resolve

from documents.models import SectionVersion
from documents.services import storage_service, version_service

TESTDATA = Path(__file__).resolve().parents[4] / 'testdata' / 'pdfs'


@pytest.fixture(autouse=True)
def _test_env(settings):
    settings.DJANGO_ENV = 'test'


def upload(document, fixture, message, author):
    intent = version_service.create_upload_intent(document, author)
    storage_service.put_bytes(intent.key, (TESTDATA / fixture).read_bytes(), 'application/pdf')
    version, _ = version_service.complete_upload(document, intent.upload_id, message, author)
    return version


@pytest.fixture
def document_with_two_versions(versiona_context):
    editor = versiona_context.users['editor']
    document = version_service.create_document(versiona_context.project, 'Historial', editor)
    v1 = upload(document, 'contrato_v1.pdf', 'v1', editor)
    v2 = upload(document, 'contrato_v2.pdf', 'v2', editor)
    return versiona_context, document, v1, v2


@pytest.mark.django_db
@pytest.mark.escenario('C3-A02')
def test_document_section_history_route_is_not_registered():
    with pytest.raises(Resolver404):
        resolve(f'/api/documents/{uuid.uuid4()}/sections/objeto-del-contrato/history/')


@pytest.mark.django_db
@pytest.mark.escenario('C3-A02')
def test_section_blame_request_returns_not_found(client_as, document_with_two_versions):
    _, document, _, _ = document_with_two_versions

    response = client_as('viewer').get(
        f'/api/documents/{document.public_id}/sections/objeto-del-contrato/history/'
    )

    assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.escenario('C3-A02')
def test_version_sections_payload_carries_no_blame_field(client_as, document_with_two_versions):
    _, _, _, v2 = document_with_two_versions

    response = client_as('viewer').get(f'/api/versions/{v2.public_id}/sections/')

    assert set(response.data['results'][0]) == {
        'stable_key', 'heading_text', 'level', 'order_index',
        'page_start', 'page_end', 'bboxes', 'body_hash', 'char_count',
    }


@pytest.mark.django_db
@pytest.mark.escenario('C3-A02')
def test_snapshots_hold_the_evidence_a_blame_endpoint_would_need(document_with_two_versions):
    _, document, v1, v2 = document_with_two_versions

    hashes = list(
        SectionVersion.objects.filter(
            section__document=document,
            section__stable_key='obligaciones-del-contratista',
            document_version__in=[v1, v2],
        ).order_by('document_version__number').values_list('body_hash', flat=True)
    )

    assert hashes[0] != hashes[1]
