"""Object-storage backends.

Two interchangeable implementations of the same contract:

- ``s3``         — presigned URLs against S3/MinIO (the original implementation)
- ``filesystem`` — local files served through short-TTL signed URLs

The active one is chosen by configuration, mirroring the STORAGES['default']
switch in settings.py: a bucket means S3, no bucket means filesystem. Callers
never import these directly; they go through
``documents.services.storage_service``.
"""

from django.conf import settings

from .base import ObjectTooLarge, StorageUnavailable

__all__ = ['StorageUnavailable', 'ObjectTooLarge', 'get_backend']


def get_backend():
    """Return the active backend module.

    Resolved per call, not cached, so pytest-django's function-scoped `settings`
    fixture flips the backend without a module reload.
    """
    if getattr(settings, 'AWS_STORAGE_BUCKET_NAME', ''):
        from . import s3  # lazy: boto3 stays optional on hosts that never use it
        return s3
    from . import filesystem
    return filesystem
