"""POST/GET /api/public/comparisons/ — AllowAny, validated, throttled."""

from datetime import timedelta
from pathlib import Path

import pytest
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from public_tools.models import PublicComparison
from public_tools.views import PublicCompareThrottle

TESTDATA = Path(__file__).resolve().parents[3] / 'testdata' / 'pdfs'
URL = '/api/public/comparisons/'


@pytest.fixture(autouse=True)
def _clean_throttle_cache():
    cache.clear()
    yield
    cache.clear()


def upload(name: str, content: bytes | None = None) -> SimpleUploadedFile:
    data = content if content is not None else (TESTDATA / name).read_bytes()
    return SimpleUploadedFile(name, data, content_type='application/pdf')


def post_pair(api_client, file_a, file_b):
    return api_client.post(URL, {'file_a': file_a, 'file_b': file_b},
                           format='multipart')


@pytest.mark.django_db
@pytest.mark.escenario('PC-F01')
def test_post_happy_path_returns_done_result_in_eager_mode(api_client):
    response = post_pair(
        api_client, upload('contrato_v1.pdf'), upload('contrato_v2.pdf')
    )

    assert response.status_code == 202
    detail = api_client.get(response.data['status_url'])
    assert detail.data['status'] == 'done'
    assert detail.data['result']['summary_text'] == (
        '2 modificadas, 1 eliminada, 1 agregada'
    )


@pytest.mark.django_db
@pytest.mark.escenario('PC-F02')
def test_post_creates_no_org_project_document_rows(api_client):
    from documents.models import Document, DocumentVersion
    from orgs.models import Organization
    from projects.models import Project

    post_pair(api_client, upload('contrato_v1.pdf'), upload('contrato_v2.pdf'))

    assert Organization.objects.count() == 0
    assert Project.objects.count() == 0
    assert Document.all_objects.count() == 0
    assert DocumentVersion.all_objects.count() == 0


@pytest.mark.django_db
@pytest.mark.escenario('PC-E01')
def test_post_rejects_oversize_file_with_413(api_client):
    heavy = upload('pesado.pdf', b'%PDF-' + b'0' * (11 * 1024 * 1024))

    response = post_pair(api_client, heavy, upload('contrato_v2.pdf'))

    assert response.status_code == 413
    assert response.data['error_code'] == 'too_big'


@pytest.mark.django_db
@pytest.mark.escenario('PC-E02')
def test_post_rejects_non_pdf_with_415(api_client):
    fake = upload('archivo.pdf', b'GIF89a not a pdf at all')

    response = post_pair(api_client, fake, upload('contrato_v2.pdf'))

    assert response.status_code == 415
    assert response.data['error_code'] == 'not_pdf'


@pytest.mark.django_db
@pytest.mark.escenario('PC-E03')
def test_post_rejects_encrypted_pdf_with_400(api_client):
    response = post_pair(
        api_client, upload('protegido.pdf'), upload('contrato_v2.pdf')
    )

    assert response.status_code == 400
    assert response.data['error_code'] == 'encrypted_pdf'


@pytest.mark.django_db
@pytest.mark.escenario('PC-E04')
def test_post_rejects_scanned_pdf_with_422_ocr_required(api_client):
    response = post_pair(
        api_client, upload('escaneado_v1.pdf'), upload('contrato_v2.pdf')
    )

    assert response.status_code == 422
    assert response.data['error_code'] == 'ocr_required'


@pytest.mark.django_db
@pytest.mark.escenario('PC-E05')
def test_post_rejects_page_count_over_cap_with_422(api_client, settings):
    settings.PUBLIC_COMPARE_MAX_PAGES = 1

    response = post_pair(
        api_client, upload('contrato_v1.pdf'), upload('contrato_v2.pdf')
    )

    assert response.status_code == 422
    assert response.data['error_code'] == 'too_many_pages'


@pytest.mark.django_db
@pytest.mark.escenario('PC-E06')
def test_post_throttled_returns_429(api_client, monkeypatch):
    monkeypatch.setattr(PublicCompareThrottle, 'rate', '1/hour', raising=False)

    post_pair(api_client, upload('contrato_v1.pdf'), upload('contrato_v2.pdf'))
    second = post_pair(
        api_client, upload('contrato_v1.pdf'), upload('contrato_v2.pdf')
    )

    assert second.status_code == 429


@pytest.mark.django_db
@pytest.mark.escenario('PC-E07')
def test_get_unknown_id_returns_404(api_client):
    response = api_client.get(
        f'{URL}0198c9a0-0000-7000-8000-000000000000/'
    )

    assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.escenario('PC-E08')
def test_get_expired_row_returns_410_with_expired_code(api_client):
    comparison = PublicComparison.objects.create(
        status=PublicComparison.Status.DONE,
        result={'counts': {}},
        expires_at=timezone.now() - timedelta(hours=1),
    )

    response = api_client.get(f'{URL}{comparison.public_id}/')

    assert response.status_code == 410
    assert response.data['error_code'] == 'expired'
