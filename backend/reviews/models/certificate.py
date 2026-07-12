"""Certificate — the exportable proof (docs/plan/02 §3.4 — flow E4, T6).

Append-only: one serial per org, a JSONB snapshot with EVERYTHING a third
party needs to verify offline (payloads, signatures, public key, validity
chain) and an S3 key that is never overwritten."""

from django.conf import settings
from django.db import models

from core.models import PublicIdModel, TimestampedModel
from documents.models import DocumentVersion


class Certificate(PublicIdModel, TimestampedModel):
    organization = models.ForeignKey(
        'orgs.Organization', on_delete=models.CASCADE, related_name='certificates'
    )
    document_version = models.ForeignKey(
        DocumentVersion, on_delete=models.PROTECT, related_name='certificates'
    )
    serial = models.CharField(max_length=40)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+'
    )
    # Everything needed for offline verification (T6): version sha256, seals
    # with canonical payloads + signatures, public key, validity decisions.
    snapshot = models.JSONField()
    pdf_key = models.CharField(max_length=500)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['organization', 'serial'], name='uniq_serial_per_org'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.serial} · v{self.document_version.number}'
