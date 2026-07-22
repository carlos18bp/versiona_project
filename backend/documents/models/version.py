"""
DocumentVersion — the immutable commit (docs/plan/02 §3.3, invariants I1/I2).

I2a: once `analysis_status` reaches READY the identity/content columns in
FROZEN_VERSION_COLUMNS never change (save() guard + PostgreSQL trigger).
Operational/derived columns (`analysis_status`, `thumb_*`, `deleted_*`,
`is_approved/approved_at`, `error_detail`) are explicitly outside the frozen
set (T8).

I2b: `message` is editable ONLY while the version is a draft (no seal, not
approved, no open review request — Seal/ReviewRequest checks join in It3/It4);
enforced in the version service with an AuditEvent (before/after).

Soft delete (C4): only the latest draft version is trash-eligible; the row
keeps its number while trashed and, after purge, the number is never reused
(I1 tombstones — `latest_number` on Document never decreases).
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from core.models import PublicIdModel, SoftDeletableModel, TimestampedModel

from .document import Document

FROZEN_VERSION_COLUMNS = (
    'document_id',
    'number',
    'sha256',
    'file_key',
    'size_bytes',
    'page_count',
    'author_id',
    'config_version_id',
    'source_scenario',
)


class DocumentVersion(PublicIdModel, TimestampedModel, SoftDeletableModel):
    class Scenario(models.TextChoices):
        TEXT_NATIVE = 'text_native', 'Native text'
        SCANNED_OCR = 'scanned_ocr', 'Scanned (OCR)'
        MIXED = 'mixed', 'Mixed'

    class AnalysisStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        READY = 'ready', 'Ready'
        FAILED = 'failed', 'Failed'

    class ThumbStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        READY = 'ready', 'Ready'
        FAILED = 'failed', 'Failed'

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    number = models.PositiveIntegerField()
    message = models.TextField(blank=True, default='')
    sha256 = models.CharField(max_length=64)
    file_key = models.CharField(max_length=500)
    size_bytes = models.BigIntegerField(default=0)
    page_count = models.PositiveIntegerField(default=0)
    source_scenario = models.CharField(
        max_length=12, choices=Scenario.choices, default=Scenario.TEXT_NATIVE
    )
    ocr_confidence = models.FloatField(null=True, blank=True)
    analysis_status = models.CharField(
        max_length=10, choices=AnalysisStatus.choices, default=AnalysisStatus.PENDING
    )
    error_detail = models.TextField(blank=True, default='')
    is_approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='+'
    )
    config_version = models.ForeignKey(
        'projects.ProjectConfigVersion', on_delete=models.PROTECT, related_name='+'
    )
    thumb_key = models.CharField(max_length=500, blank=True, default='')
    thumb_status = models.CharField(
        max_length=10, choices=ThumbStatus.choices, default=ThumbStatus.PENDING
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['document', 'number'], name='uniq_version_number'),
        ]
        indexes = [models.Index(fields=['document', 'sha256'])]
        ordering = ['-number']

    def __str__(self):
        return f'{self.document} v{self.number}'

    @property
    def is_draft(self) -> bool:
        """I2b draft frontier. Seal / open ReviewRequest checks extend this in
        It3/It4 (docs/audit/03 C2-A01/C2-E02)."""
        if self.is_approved:
            return False
        seals = getattr(self, 'seals', None)
        if seals is not None and seals.exists():
            return False
        requests = getattr(self, 'review_requests', None)
        if requests is not None and requests.filter(status='open').exists():
            return False
        return True

    def save(self, *args, **kwargs):
        if self.pk:
            update_fields = kwargs.get('update_fields')
            columns = FROZEN_VERSION_COLUMNS
            if update_fields is not None:
                # A partial save only freezes what it actually writes: a stale
                # in-memory copy of untouched columns must not false-positive.
                written = set(update_fields)
                columns = tuple(
                    column for column in FROZEN_VERSION_COLUMNS
                    if column in written or column.removesuffix('_id') in written
                )
            if columns:
                original = (
                    DocumentVersion.all_objects.filter(pk=self.pk)
                    .values(*columns, 'analysis_status')
                    .first()
                )
                if original and original['analysis_status'] == self.AnalysisStatus.READY:
                    changed = [
                        column for column in columns
                        if getattr(self, column) != original[column]
                    ]
                    if changed:
                        raise ValidationError(
                            f'I2a: frozen columns of an analyzed version cannot change: {changed}'
                        )
        super().save(*args, **kwargs)
