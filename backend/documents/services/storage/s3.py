"""S3/MinIO object storage.

The original implementation, moved here unchanged so it can sit beside the
filesystem backend. Access is exclusively through short-TTL presigned URLs; the
bucket stays private.
"""

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from django.conf import settings

from .base import ObjectTooLarge, StorageUnavailable


def _client():
    if not settings.AWS_STORAGE_BUCKET_NAME:
        raise StorageUnavailable('Object storage is not configured (AWS_STORAGE_BUCKET_NAME).')
    return boto3.client(
        's3',
        endpoint_url=settings.AWS_S3_ENDPOINT_URL or None,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        config=Config(signature_version='s3v4'),
    )


def _bucket() -> str:
    return settings.AWS_STORAGE_BUCKET_NAME


def presign_upload(key: str, ttl: int | None = None) -> str:
    """Presigned PUT (content pinned to application/pdf; size re-verified at
    complete/ — docs/plan/08 §5)."""
    return _client().generate_presigned_url(
        'put_object',
        Params={'Bucket': _bucket(), 'Key': key, 'ContentType': 'application/pdf'},
        ExpiresIn=ttl or int(getattr(settings, 'UPLOAD_SIGNED_URL_TTL_SECONDS', 900)),
    )


def presign_download(key: str, filename: str, ttl: int | None = None) -> str:
    return _client().generate_presigned_url(
        'get_object',
        Params={
            'Bucket': _bucket(),
            'Key': key,
            'ResponseContentDisposition': f'attachment; filename="{filename}"',
            'ResponseContentType': 'application/pdf',
        },
        ExpiresIn=ttl or int(getattr(settings, 'MEDIA_SIGNED_URL_TTL_SECONDS', 300)),
    )


def presign_view(key: str, content_type: str, ttl: int | None = None) -> str:
    """Inline variant for the in-app viewer/thumbnails (react-pdf needs GET)."""
    return _client().generate_presigned_url(
        'get_object',
        Params={'Bucket': _bucket(), 'Key': key, 'ResponseContentType': content_type},
        ExpiresIn=ttl or int(getattr(settings, 'MEDIA_SIGNED_URL_TTL_SECONDS', 300)),
    )


def head(key: str) -> dict | None:
    """Object metadata, or None when absent.

    Projected down to the four fields in the backend contract so no call site
    can quietly start depending on an S3-only field (VersionId,
    ServerSideEncryption, …) and break the filesystem path.
    """
    try:
        raw = _client().head_object(Bucket=_bucket(), Key=key)
    except ClientError:
        return None
    return {k: raw[k] for k in _HEAD_FIELDS if k in raw}


_HEAD_FIELDS = ('ContentLength', 'ContentType', 'LastModified', 'ETag')


def get_bytes(key: str) -> bytes:
    body = _client().get_object(Bucket=_bucket(), Key=key)['Body']
    return body.read()


def put_bytes(key: str, data: bytes, content_type: str) -> None:
    _client().put_object(Bucket=_bucket(), Key=key, Body=data, ContentType=content_type)


def put_stream(key: str, chunks, max_bytes: int | None = None) -> int:
    """Buffer-and-put. Only the filesystem backend ever serves an inbound PUT
    (S3 takes the browser's bytes directly), so this exists for contract parity
    and for the MinIO→filesystem migration command."""
    data = b''.join(chunks)
    if max_bytes is not None and len(data) > max_bytes:
        raise ObjectTooLarge(f'Object exceeds {max_bytes} bytes')
    put_bytes(key, data, 'application/pdf')
    return len(data)


def copy(source_key: str, dest_key: str) -> None:
    _client().copy_object(
        Bucket=_bucket(),
        Key=dest_key,
        CopySource={'Bucket': _bucket(), 'Key': source_key},
        MetadataDirective='REPLACE',
        ContentType='application/pdf',
    )


def delete(key: str) -> None:
    _client().delete_object(Bucket=_bucket(), Key=key)
