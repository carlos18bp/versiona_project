"""Object-storage service for domain files (docs/plan/02 §6, 08 §5).

Key layout (never overwritten — one key per version):
    {env}/orgs/{org}/projects/{proj}/docs/{doc}/v{n}/original.pdf
    {env}/orgs/{org}/projects/{proj}/docs/{doc}/v{n}/artifacts/thumb-p1.png
Uploads land on a staging key first (uploads/{org}/{upload_id}) and are
copied to their final immutable key at `complete/` (DP-06).

Access is exclusively through short-TTL signed URLs; objects are never publicly
addressable. All configuration comes from settings/env (kit 7).

This module is the stable import path for the whole domain. It owns the key
layout — which is backend-agnostic — and forwards every object operation to the
active backend (`storage/s3.py` or `storage/filesystem.py`, chosen by whether a
bucket is configured). Keep new call sites on `storage_service.X`; do not import
the backends directly.
"""

import hashlib
import uuid

from django.conf import settings

from .storage import get_backend
from .storage.base import StorageUnavailable

__all__ = [
    'StorageUnavailable',
    'staging_key',
    'version_key',
    'thumb_key',
    'new_upload_id',
    'sha256_of',
    'presign_upload',
    'presign_download',
    'presign_view',
    'head',
    'get_bytes',
    'put_bytes',
    'put_stream',
    'copy',
    'delete',
]


# ---------------------------------------------------------------------------
# Key layout — identical on every backend
# ---------------------------------------------------------------------------
def _env_prefix() -> str:
    return getattr(settings, 'DJANGO_ENV', 'development')


def staging_key(org, upload_id: str) -> str:
    return f'{_env_prefix()}/uploads/{org.public_id}/{upload_id}'


def version_key(document, number: int, filename: str = 'original.pdf') -> str:
    project = document.project
    return (
        f'{_env_prefix()}/orgs/{project.organization.public_id}'
        f'/projects/{project.public_id}/docs/{document.public_id}/v{number}/{filename}'
    )


def thumb_key(document, number: int) -> str:
    return version_key(document, number, 'artifacts/thumb-p1.png')


def new_upload_id() -> str:
    return uuid.uuid4().hex


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Object operations — delegated to the active backend
# ---------------------------------------------------------------------------
def presign_upload(key: str, ttl: int | None = None) -> str:
    return get_backend().presign_upload(key, ttl)


def presign_download(key: str, filename: str, ttl: int | None = None) -> str:
    return get_backend().presign_download(key, filename, ttl)


def presign_view(key: str, content_type: str, ttl: int | None = None) -> str:
    return get_backend().presign_view(key, content_type, ttl)


def head(key: str) -> dict | None:
    """Object metadata, or None when the key does not exist.

    Both backends return a dict carrying at least 'ContentLength' — the only
    field the domain reads (version_service.complete_upload).
    """
    return get_backend().head(key)


def get_bytes(key: str) -> bytes:
    return get_backend().get_bytes(key)


def put_bytes(key: str, data: bytes, content_type: str) -> None:
    get_backend().put_bytes(key, data, content_type)


def put_stream(key: str, chunks, max_bytes: int | None = None) -> int:
    """Write an object from an iterable of chunks; returns the byte count.

    Used by the signed-URL upload view, which must never materialise a 25 MB
    body in memory (and must never touch request.body — see views_objects.py).
    """
    return get_backend().put_stream(key, chunks, max_bytes)


def copy(source_key: str, dest_key: str) -> None:
    get_backend().copy(source_key, dest_key)


def delete(key: str) -> None:
    get_backend().delete(key)
