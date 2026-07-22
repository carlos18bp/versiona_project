"""Anonymous public tools — the ONLY AllowAny surface beyond auth.

`PublicComparison` stores just the ephemeral RESULT of comparing two PDFs.
The uploaded files live under a short-TTL storage prefix and are deleted the
moment processing ends; no tenancy row (Organization/Project/Document/
DocumentVersion) is ever created from here.
"""

from django.db import models

from core.models import PublicIdModel, TimestampedModel


class PublicComparison(PublicIdModel, TimestampedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        DONE = 'done', 'Done'
        FAILED = 'failed', 'Failed'

    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    result = models.JSONField(null=True, blank=True)
    error_code = models.CharField(max_length=32, blank=True, default='')
    file_a_name = models.CharField(max_length=255, default='')
    file_b_name = models.CharField(max_length=255, default='')
    expires_at = models.DateTimeField(db_index=True)
    # sha256(ip + SECRET_KEY): abuse forensics without storing PII.
    ip_hash = models.CharField(max_length=64, blank=True, default='')

    class Meta:
        indexes = [models.Index(fields=['status', 'expires_at'])]

    def __str__(self):
        return f'{self.public_id} ({self.status})'
