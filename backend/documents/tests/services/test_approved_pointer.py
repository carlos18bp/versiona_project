"""C2-L02: uploading over a document that already has an APPROVED version is
allowed, and the approved pointer never moves on its own (D5 governs approval;
I5 keeps at most one current approved version)."""

from pathlib import Path

import pytest

from documents.models import Document, DocumentVersion
from documents.services import storage_service, version_service
from reviews.services import seal_service

TESTDATA = Path(__file__).resolve().parents[4] / 'testdata' / 'pdfs'


@pytest.fixture(autouse=True)
def _test_env(settings, tmp_path):
    settings.DJANGO_ENV = 'test'
    settings.SEAL_SIGNING_KEY_PATH = str(tmp_path / 'seal_key.pem')


def upload(document, fixture, message, author):
    intent = version_service.create_upload_intent(document, author)
    storage_service.put_bytes(intent.key, (TESTDATA / fixture).read_bytes(), 'application/pdf')
    version, _ = version_service.complete_upload(document, intent.upload_id, message, author)
    return version


@pytest.fixture
def document_with_approved_v1(versiona_context):
    editor = versiona_context.users['editor']
    document = version_service.create_document(versiona_context.project, 'Aprobado', editor)
    v1 = upload(document, 'contrato_v1.pdf', 'v1', editor)
    seal_service.create_seal(v1, versiona_context.users['reviewer'], covers_all=True)
    v1.refresh_from_db()
    document.approved_version = v1
    document.save(update_fields=['approved_version'])
    return versiona_context, document, v1


@pytest.mark.django_db
@pytest.mark.escenario('C2-L02')
def test_upload_over_an_approved_version_is_accepted(document_with_approved_v1):
    context, document, _ = document_with_approved_v1

    v2 = upload(document, 'contrato_v2.pdf', 'v2', context.users['editor'])

    assert v2.number == 2


@pytest.mark.django_db
@pytest.mark.escenario('C2-L02')
def test_the_new_version_reaches_ready_over_an_approved_document(document_with_approved_v1):
    context, document, _ = document_with_approved_v1

    v2 = upload(document, 'contrato_v2.pdf', 'v2', context.users['editor'])

    v2.refresh_from_db()
    assert v2.analysis_status == DocumentVersion.AnalysisStatus.READY


@pytest.mark.django_db
@pytest.mark.escenario('C2-L02')
def test_the_approved_pointer_does_not_move_to_the_new_version(document_with_approved_v1):
    context, document, v1 = document_with_approved_v1

    upload(document, 'contrato_v2.pdf', 'v2', context.users['editor'])

    document.refresh_from_db()
    assert document.approved_version_id == v1.pk


@pytest.mark.django_db
@pytest.mark.escenario('C2-L02')
def test_the_new_version_is_not_approved_by_the_upload(document_with_approved_v1):
    context, document, _ = document_with_approved_v1

    v2 = upload(document, 'contrato_v2.pdf', 'v2', context.users['editor'])

    v2.refresh_from_db()
    assert v2.is_approved is False


@pytest.mark.django_db
@pytest.mark.escenario('C2-L02')
def test_i5_only_one_approved_version_remains_after_the_upload(document_with_approved_v1):
    context, document, _ = document_with_approved_v1

    upload(document, 'contrato_v2.pdf', 'v2', context.users['editor'])

    approved = DocumentVersion.objects.filter(document=document, is_approved=True)
    assert approved.count() == 1
