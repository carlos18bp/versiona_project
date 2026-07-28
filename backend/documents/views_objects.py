"""Signed-URL access to filesystem-backed objects.

These are the local stand-in for S3 presigned URLs (see
services/storage/filesystem.py). Deliberately plain Django views, not DRF:

- DRF's DEFAULT_PERMISSION_CLASSES is IsAuthenticated and would have to be
  overridden anyway;
- DRF runs content negotiation and parsers, and a raw application/pdf body
  would need a custom parser class;
- most importantly, anything that touches request.data / request.body trips
  DATA_UPLOAD_MAX_MEMORY_SIZE (2.5 MB by default) and 400s every real PDF.

**The signature IS the authorization.** Same semantics as the S3 presigned URL
it replaces: authorization is checked when the URL is minted — upload_intent is
behind @require_project_role('editor'), version_file and the review downloads
behind 'viewer' — and the token is then HMAC'd to one key, one method, one
content type, one disposition and one expiry. It cannot be widened, and it dies
in 300 s (view/download) or 900 s (upload). A leaked upload token can only write
one staging slot that nobody else can name, and complete_upload still re-verifies
size, %PDF- magic, a full parse and the sha256 server-side.

That is also why csrf_exempt is correct and not a weakening: CSRF defends against
*ambient* authority (cookies the browser attaches by itself). There is none here
— the browser PUTs with a bare axios call carrying no cookies and no
Authorization header, so the only credential is an unguessable bearer token that
an attacker's page cannot obtain.
"""

from urllib.parse import quote

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.http import FileResponse, HttpResponse, JsonResponse
from django.utils.http import content_disposition_header
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .services.storage import ObjectTooLarge
from .services.storage import filesystem as fs

_UPLOAD_CHUNK = 64 * 1024


class _StreamedFileResponse(FileResponse):
    # Django's default is 4096, i.e. ~6400 yields for a 25 MB PDF. block_size is
    # read during __init__, so it must be set on the class, not the instance.
    block_size = 512 * 1024


def _error(code: str, detail: str, status: int) -> JsonResponse:
    return JsonResponse({'detail': detail, 'code': code}, status=status)


_TOKEN_ERRORS = {
    'signature_invalid': ('Enlace inválido.', 403),
    'signature_expired': ('El enlace venció: recarga la página.', 403),
}


@csrf_exempt
@require_http_methods(['GET', 'HEAD', 'PUT'])
def object_access(request, token):
    """Serve or accept exactly ONE object, named by a signed short-TTL token."""
    method = 'PUT' if request.method == 'PUT' else 'GET'
    try:
        payload = fs.verify_token(token, method)
    except fs.InvalidObjectToken as exc:
        detail, status = _TOKEN_ERRORS.get(exc.code, _TOKEN_ERRORS['signature_invalid'])
        return _error(exc.code, detail, status)

    key = payload.get('k', '')
    try:
        # Defense in depth: the key is inside a valid signature, but validate it
        # anyway so a caller-controlled key could never become a traversal.
        path = fs.resolve_path(key)
    except SuspiciousFileOperation:
        return _error('bad_key', 'Clave inválida.', 400)

    if request.method == 'PUT':
        return _receive(request, key, payload)
    return _serve(path, key, payload)


def _receive(request, key, payload):
    expected = payload.get('ct', fs.UPLOAD_CONTENT_TYPE)
    got = (request.content_type or '').split(';')[0].strip()
    if got != expected:
        return _error('content_type_mismatch', 'Tipo de contenido no permitido.', 415)

    limit = int(getattr(settings, 'MAX_PDF_SIZE_MB', 25)) * 1024 * 1024

    # Enforced twice on purpose: the declared length rejects before a single
    # byte is read, the running counter defends against an absent, understated
    # or chunked Content-Length. complete_upload checks a third time, against
    # the plan's own limit.
    try:
        declared = int(request.META.get('CONTENT_LENGTH') or 0)
    except (TypeError, ValueError):
        declared = 0
    if declared > limit:
        return _error('too_large', 'El archivo supera el límite permitido.', 413)

    try:
        fs.put_stream(key, _chunks(request), max_bytes=limit)
    except ObjectTooLarge:
        return _error('too_large', 'El archivo supera el límite permitido.', 413)
    except SuspiciousFileOperation:
        return _error('bad_key', 'Clave inválida.', 400)
    return HttpResponse(status=200)  # S3's PUT Object also answers 200, empty body


def _chunks(request):
    """Read the body straight off the stream.

    request.read() bypasses the DATA_UPLOAD_MAX_MEMORY_SIZE guard that lives in
    the `body` property, and keeps peak RSS flat — which matters with 2 sync
    gunicorn workers on a RAM-constrained VPS.
    """
    while True:
        block = request.read(_UPLOAD_CHUNK)
        if not block:
            return
        yield block


def _serve(path, key, payload):
    if not path.is_file():
        return _error('not_found', 'No encontrado.', 404)

    content_type = payload.get('ct', 'application/octet-stream')
    as_attachment = payload.get('d') == 'attachment'
    filename = payload.get('fn') or path.name

    sendfile_root = (getattr(settings, 'OBJECT_STORAGE_SENDFILE_ROOT', '') or '').rstrip('/')
    if sendfile_root:
        # Hand off to nginx: the worker is released immediately, transfer uses
        # sendfile(2), and Range/206 works — which Django's FileResponse does
        # not support at all, so pdf.js would otherwise pull whole files.
        response = HttpResponse(status=200)
        response['X-Accel-Redirect'] = f'{sendfile_root}/{quote(key)}'
        response['Content-Type'] = content_type
        if as_attachment:
            response['Content-Disposition'] = content_disposition_header(True, filename)
    else:
        response = _StreamedFileResponse(
            path.open('rb'),
            content_type=content_type,
            as_attachment=as_attachment,
            filename=filename,
        )
    response['X-Content-Type-Options'] = 'nosniff'
    response['Cache-Control'] = 'private, no-store'
    return response
