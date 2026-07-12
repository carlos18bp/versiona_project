"""
Shared model mixins (docs/plan/02 §2).

Every Versiona domain model composes these:
- TimestampedModel: created_at / updated_at on all rows.
- PublicIdModel: a UUIDv7 `public_id` exposed in API routes instead of the
  integer PK (multi-tenant anti-enumeration, invariant I12). UUIDv7 is
  time-ordered, so the unique index stays insert-friendly.
"""

import os
import time
import uuid

from django.db import models


def uuid7() -> uuid.UUID:
    """UUIDv7 per RFC 9562: 48-bit unix-ms timestamp + random tail.

    Implemented locally because the stdlib gains uuid.uuid7 only in 3.14.
    """
    ts_ms = time.time_ns() // 1_000_000
    raw = bytearray(ts_ms.to_bytes(6, 'big') + os.urandom(10))
    raw[6] = (raw[6] & 0x0F) | 0x70  # version 7
    raw[8] = (raw[8] & 0x3F) | 0x80  # RFC variant
    return uuid.UUID(bytes=bytes(raw))


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PublicIdModel(models.Model):
    public_id = models.UUIDField(
        default=uuid7, unique=True, editable=False, db_index=True
    )

    class Meta:
        abstract = True
