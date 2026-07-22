"""
Object-storage service for domain files (docs/plan/02 §6, 08 §5).

Key layout (never overwritten — one key per version):
    {env}/orgs/{org}/projects/{proj}/docs/{doc}/v{n}/original.pdf
    {env}/orgs/{org}/projects/{proj}/docs/{doc}/v{n}/artifacts/thumb-p1.png
Uploads land on a staging key first (uploads/{org}/{upload_id}) and are
copied to their final immutable key at `complete/` (DP-06).

Access is exclusively through short-TTL presigned URLs; the bucket stays
private. All configuration comes from settings/env (kit 7).
"""

import hashlib
import uuid

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from django.conf import settings


class StorageUnavailable(Exception):
    pass


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
    try:
        return _client().head_object(Bucket=_bucket(), Key=key)
    except ClientError:
        return None


def get_bytes(key: str) -> bytes:
    body = _client().get_object(Bucket=_bucket(), Key=key)['Body']
    return body.read()


def put_bytes(key: str, data: bytes, content_type: str) -> None:
    _client().put_object(Bucket=_bucket(), Key=key, Body=data, ContentType=content_type)


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


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
