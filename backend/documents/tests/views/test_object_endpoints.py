"""Signed-URL object endpoint — the local replacement for S3 presigned URLs.

These are the first tests in the suite that exercise the real HTTP upload leg.
Until now every test short-circuited it by calling storage_service.put_bytes()
directly, so a broken PUT path would have shipped green.
"""

from pathlib import Path

import pytest
from django.core import signing
from freezegun import freeze_time

from documents.models import DocumentVersion
from documents.services import storage_service, version_service
from documents.services.storage import filesystem as fs

TESTDATA = Path(__file__).resolve().parents[4] / 'testdata' / 'pdfs'
KEY = 'test/orgs/abc/docs/def/v1/original.pdf'
PAYLOAD = b'%PDF-1.7 pretend this is a contract'


@pytest.fixture(autouse=True)
def _test_storage_prefix(settings):
    settings.DJANGO_ENV = 'test'


@pytest.fixture
def stored():
    storage_service.put_bytes(KEY, PAYLOAD, 'application/pdf')
    return KEY


# ---------------------------------------------------------------------------
# GET
# ---------------------------------------------------------------------------
def test_inline_token_serves_the_bytes_with_the_signed_content_type(client, stored):
    """Catches: serving the wrong content type, which breaks the pdf.js viewer."""
    url = storage_service.presign_view(stored, 'application/pdf')

    response = client.get(url)

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert response['Content-Disposition'].startswith('inline')
    assert b''.join(response.streaming_content) == PAYLOAD


def test_attachment_token_sets_the_download_filename(client, stored):
    """Catches: a download that saves as the opaque storage key instead of the
    document's name."""
    url = storage_service.presign_download(stored, 'contrato-v1.pdf')

    response = client.get(url)

    assert response.status_code == 200
    assert 'attachment' in response['Content-Disposition']
    assert 'contrato-v1.pdf' in response['Content-Disposition']


def test_get_works_anonymously(client, stored):
    """Catches: adding an auth requirement. pdf.js's worker, <img src> and
    window.open() cannot attach the JWT — the signature is the only credential."""
    response = client.get(storage_service.presign_view(stored, 'application/pdf'))

    assert response.status_code == 200


def test_expired_token_is_refused(client, stored):
    """Catches: a TTL that is decorative. A signed URL that never dies is a
    permanent public link to a private document."""
    with freeze_time('2026-01-01 12:00:00'):
        url = storage_service.presign_view(stored, 'application/pdf')

    with freeze_time('2026-01-01 12:30:00'):
        response = client.get(url)

    assert response.status_code == 403
    assert response.json()['code'] == 'signature_expired'


def test_tampered_token_is_refused(client, stored):
    """Catches: a token whose payload can be edited to name another key."""
    url = storage_service.presign_view(stored, 'application/pdf')
    tampered = url[:-6] + ('x' if url[-6] != 'x' else 'y') + url[-5:]

    response = client.get(tampered)

    assert response.status_code == 403
    assert response.json()['code'] == 'signature_invalid'


def test_token_minted_under_another_secret_key_is_refused(client, stored, settings):
    """Catches: signatures not actually bound to this deployment's SECRET_KEY."""
    settings.SECRET_KEY = 'a-different-secret'
    url = storage_service.presign_view(stored, 'application/pdf')
    settings.SECRET_KEY = 'the-real-secret'

    response = client.get(url)

    assert response.status_code == 403


def test_valid_token_for_a_missing_object_is_404_not_500(client):
    """Catches: an unhandled FileNotFoundError leaking a traceback."""
    response = client.get(storage_service.presign_view('test/gone/v1/original.pdf', 'application/pdf'))

    assert response.status_code == 404


def test_traversal_key_inside_a_valid_signature_is_refused(client):
    """Catches: trusting the key because the signature checked out. Defense in
    depth if a caller-controlled key ever reaches the signer."""
    token = signing.dumps(
        {'v': 1, 'k': '../../../etc/passwd', 'm': 'GET', 'ct': 'text/plain',
         'd': 'inline', 'exp': 4102444800},
        salt=fs.SIGNING_SALT, compress=True,
    )

    response = client.get(f'/api/objects/{token}/')

    assert response.status_code == 400
    assert response.json()['code'] == 'bad_key'


def test_get_token_cannot_be_replayed_as_a_put(client, stored):
    """Catches: a read link that also grants write."""
    response = client.put(
        storage_service.presign_view(stored, 'application/pdf'),
        data=b'%PDF-1.7 overwritten',
        content_type='application/pdf',
    )

    assert response.status_code == 403
    assert storage_service.get_bytes(stored) == PAYLOAD


def test_sendfile_mode_delegates_to_nginx(client, stored, settings):
    """Catches: shipping the X-Accel path without the header, which serves an
    empty body; and shipping it with a body, which doubles the transfer."""
    settings.OBJECT_STORAGE_SENDFILE_ROOT = '/__objects_internal'

    response = client.get(storage_service.presign_view(stored, 'application/pdf'))

    assert response.status_code == 200
    assert response['X-Accel-Redirect'] == f'/__objects_internal/{stored}'
    assert response.content == b''


# ---------------------------------------------------------------------------
# PUT
# ---------------------------------------------------------------------------
def test_put_stores_the_body(client):
    """Catches: the upload leg silently discarding bytes."""
    url = storage_service.presign_upload(KEY)

    response = client.put(url, data=PAYLOAD, content_type='application/pdf')

    assert response.status_code == 200
    assert storage_service.get_bytes(KEY) == PAYLOAD


def test_put_is_csrf_exempt():
    """Catches: removing @csrf_exempt. The browser PUTs with a bare axios call
    that sends no cookie and no CSRF token, so every upload would 403."""
    from django.test import Client

    csrf_client = Client(enforce_csrf_checks=True)
    url = storage_service.presign_upload(KEY)

    response = csrf_client.put(url, data=PAYLOAD, content_type='application/pdf')

    assert response.status_code == 200


def test_put_rejects_a_non_pdf_content_type(client):
    """Catches: accepting arbitrary binaries into the document store."""
    url = storage_service.presign_upload(KEY)

    response = client.put(url, data=b'not a pdf', content_type='text/plain')

    assert response.status_code == 415
    assert storage_service.head(KEY) is None


def test_put_rejects_an_honestly_declared_oversize_body(client, settings):
    """Catches: no size ceiling — rejected before a byte is read."""
    settings.MAX_PDF_SIZE_MB = 1
    url = storage_service.presign_upload(KEY)

    response = client.put(url, data=b'a' * (2 * 1024 * 1024), content_type='application/pdf')

    assert response.status_code == 413
    assert storage_service.head(KEY) is None


# The other half of the size defence — the running byte counter, which covers a
# request that arrives chunked with no Content-Length at all — is exercised at
# the backend level in test_storage_filesystem.py::test_put_stream_enforces_the
# _byte_ceiling. It cannot be provoked through the WSGI test client: Django wraps
# wsgi.input in a LimitedStream bounded by CONTENT_LENGTH, so an understated
# length truncates the read rather than overflowing it.


def test_put_is_idempotent_so_a_retry_is_safe(client):
    """Catches: a second PUT (network retry) failing or duplicating the object."""
    url = storage_service.presign_upload(KEY)

    assert client.put(url, data=PAYLOAD, content_type='application/pdf').status_code == 200
    assert client.put(url, data=PAYLOAD, content_type='application/pdf').status_code == 200
    assert storage_service.get_bytes(KEY) == PAYLOAD


# ---------------------------------------------------------------------------
# The whole flow
# ---------------------------------------------------------------------------
@pytest.mark.django_db
@pytest.mark.escenario('C1-F01')
def test_upload_intent_then_put_then_complete_creates_the_version(versiona_context, client_as):
    """The headline test: the real three-legged upload the browser performs.

    Catches: any break between minting the URL, PUTting to it and completing —
    the leg that every other test in this suite skips by writing to storage
    directly.
    """
    editor = versiona_context.users['editor']
    document = version_service.create_document(versiona_context.project, 'Contrato', editor)
    pdf = (TESTDATA / 'contrato_v1.pdf').read_bytes()
    api = client_as('editor')

    intent = api.post(f'/api/documents/{document.public_id}/versions/upload_intent/').json()
    put = api.put(intent['url'], data=pdf, content_type='application/pdf')
    complete = api.post(
        f'/api/documents/{document.public_id}/versions/complete/',
        {'upload_id': intent['upload_id'], 'message': 'primera entrega'},
        format='json',
    )

    assert put.status_code == 200
    assert complete.status_code == 202  # accepted: analysis is enqueued
    version = DocumentVersion.objects.get(document=document, number=1)
    assert version.size_bytes == len(pdf)
    assert version.sha256 == storage_service.sha256_of(pdf)
