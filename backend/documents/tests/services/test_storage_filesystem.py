"""Filesystem object storage backend — the contract the domain relies on.

Every test here names the bug it would catch, because these are the guarantees
that used to come from S3/MinIO for free and now come from our own code.
"""

import os
from pathlib import Path

import pytest
from django.core.exceptions import SuspiciousFileOperation

from documents.services import storage_service
from documents.services.storage import filesystem as fs
from documents.services.storage.base import ObjectTooLarge

KEY = 'test/orgs/abc/docs/def/v1/original.pdf'
PAYLOAD = b'%PDF-1.7 pretend this is a contract'


def test_put_then_head_and_get_round_trip():
    """Catches: a write that silently truncates or a read that returns stale bytes."""
    storage_service.put_bytes(KEY, PAYLOAD, 'application/pdf')

    meta = storage_service.head(KEY)
    assert meta['ContentLength'] == len(PAYLOAD)
    assert storage_service.get_bytes(KEY) == PAYLOAD


def test_head_returns_none_for_missing_key():
    """Catches: raising instead of the None sentinel — complete_upload branches on
    `meta is None` to tell the user to retry the upload."""
    assert storage_service.head('test/orgs/abc/docs/nope/v9/original.pdf') is None


def test_copy_then_delete_source_leaves_destination_readable():
    """Catches: a copy() that aliases instead of duplicating. complete_upload
    copies the staging key to the immutable version key and then deletes the
    staging key — if that lost the bytes, every upload would vanish."""
    dest = 'test/orgs/abc/docs/def/v2/original.pdf'
    storage_service.put_bytes(KEY, PAYLOAD, 'application/pdf')

    storage_service.copy(KEY, dest)
    storage_service.delete(KEY)

    assert storage_service.get_bytes(dest) == PAYLOAD
    assert storage_service.head(KEY) is None


def test_delete_of_missing_key_is_a_silent_no_op():
    """Catches: losing S3's idempotent delete. version_service and the public
    comparison purge both delete keys that may already be gone."""
    storage_service.delete('test/orgs/abc/docs/ghost/v1/original.pdf')  # must not raise


@pytest.mark.parametrize('bad_key', [
    '../../../etc/passwd',
    'a/../../b',
    '/etc/passwd',
    '..',
    'a\x00b',
    'a\\b',
    '',
])
def test_traversal_keys_are_refused(bad_key):
    """Catches: a crafted key escaping the object root to read or clobber an
    arbitrary file. SuspiciousFileOperation on purpose, not StorageUnavailable —
    serializers.py swallows the latter to degrade a thumbnail and must never
    swallow this."""
    with pytest.raises(SuspiciousFileOperation):
        storage_service.put_bytes(bad_key, b'x', 'application/pdf')
    with pytest.raises(SuspiciousFileOperation):
        storage_service.get_bytes(bad_key)
    with pytest.raises(SuspiciousFileOperation):
        storage_service.head(bad_key)
    with pytest.raises(SuspiciousFileOperation):
        storage_service.delete(bad_key)


def test_traversal_does_not_create_a_file_outside_the_root(settings, tmp_path):
    """Catches: the specific disaster — writing through the root into a sibling."""
    outside = tmp_path / 'outside.txt'
    depth = len(Path(settings.OBJECT_STORAGE_ROOT).resolve().parts)
    escape = '/'.join(['..'] * depth) + str(outside)

    with pytest.raises(SuspiciousFileOperation):
        storage_service.put_bytes(escape, b'pwned', 'application/pdf')

    assert not outside.exists()


def test_failed_write_leaves_no_partial_object_and_no_temp_file(settings):
    """Catches: a non-atomic write. A crash mid-upload must not leave a truncated
    PDF behind a key that head() will happily report as complete."""
    def exploding_chunks():
        yield b'%PDF-1.7 first half'
        raise RuntimeError('connection dropped')

    with pytest.raises(RuntimeError):
        fs.put_stream(KEY, exploding_chunks())

    assert storage_service.head(KEY) is None
    parent = fs.resolve_path(KEY).parent
    assert [p.name for p in parent.iterdir() if p.name.startswith('.tmp-')] == []


def test_put_stream_enforces_the_byte_ceiling(settings):
    """Catches: an unbounded upload filling the disk when Content-Length lies."""
    with pytest.raises(ObjectTooLarge):
        fs.put_stream(KEY, [b'a' * 100, b'b' * 100], max_bytes=150)

    assert storage_service.head(KEY) is None


def test_nested_key_creates_parents_with_restricted_modes(settings):
    """Catches: world-readable objects. nginx reads them as www-data via the
    group bit; nothing else on the box should be able to."""
    storage_service.put_bytes(KEY, PAYLOAD, 'application/pdf')
    path = fs.resolve_path(KEY)

    assert path.is_file()
    assert os.stat(path).st_mode & 0o777 == 0o640
    assert os.stat(path.parent).st_mode & 0o777 == 0o750

# test_backend_selection_follows_the_bucket_setting was removed with the S3
# backend on 2026-08-02. It asserted that a configured bucket selected S3 and an
# empty one selected the filesystem — a switch that no longer exists. Rewriting
# it as `assert get_backend() is fs` would assert that the only backend is the
# only backend, which is the tautological shape docs/TESTING_QUALITY_STANDARDS.md
# rules out.
