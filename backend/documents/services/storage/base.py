"""Shared pieces for the object-storage backends.

Kept in its own module so both backends can import these without importing each
other (or the package __init__, which imports them).
"""


class StorageUnavailable(Exception):
    """Object storage is unusable for this request.

    Means "no backend is configured" or "the backend cannot be reached/written".
    NOT used for malformed keys — those raise SuspiciousFileOperation, because
    documents/serializers.py swallows StorageUnavailable to degrade a thumbnail
    and must never swallow a traversal attempt.
    """


class ObjectTooLarge(Exception):
    """The incoming object exceeded the byte ceiling while streaming."""
