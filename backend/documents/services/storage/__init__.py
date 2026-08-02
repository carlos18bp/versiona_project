"""Object-storage backend.

``filesystem`` — local files served through short-TTL signed URLs.

This used to be a two-backend switch: a configured bucket selected an S3/MinIO
implementation, no bucket selected the filesystem one. The S3 backend was
removed on 2026-08-02 — no environment ran it (staging, production and CI all
have no bucket) and nothing tested it, so it was a second contract to keep
correct with no way to notice when it drifted.

Callers never import this module directly; they go through
``documents.services.storage_service``, which owns the backend-agnostic key
layout. The ``get_backend`` seam is kept so a second backend can return without
touching those 28 call sites.
"""

from .base import ObjectTooLarge, StorageUnavailable

__all__ = ['StorageUnavailable', 'ObjectTooLarge', 'get_backend']


def get_backend():
    """Return the active backend module."""
    from . import filesystem
    return filesystem
