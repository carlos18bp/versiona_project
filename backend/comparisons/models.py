"""
Comparison + SectionDiff (docs/plan/02 §3.6 — flow E1, the star screen).

A comparison is idempotent per (from_version, to_version): the unique pair IS
the cache (I15). SectionDiff carries the per-section classification plus the
word-level diff consumed by the side-by-side highlights.
"""

from django.conf import settings
from django.db import models

from core.models import PublicIdModel, TimestampedModel
from documents.models import Document, DocumentVersion, Section


class Comparison(PublicIdModel, TimestampedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        RUNNING = 'running', 'Running'
        DONE = 'done', 'Done'
        FAILED = 'failed', 'Failed'

    class Trigger(models.TextChoices):
        AUTO = 'auto', 'Automatic (post-upload)'
        MANUAL = 'manual', 'Manual (E1)'

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='comparisons')
    from_version = models.ForeignKey(
        DocumentVersion, on_delete=models.CASCADE, related_name='comparisons_from'
    )
    to_version = models.ForeignKey(
        DocumentVersion, on_delete=models.CASCADE, related_name='comparisons_to'
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    trigger = models.CharField(max_length=8, choices=Trigger.choices, default=Trigger.MANUAL)
    summary = models.JSONField(default=dict, blank=True)
    error_detail = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='+'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['from_version', 'to_version'], name='uniq_comparison_pair'
            ),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.document} v{self.from_version.number}→v{self.to_version.number}'

    @property
    def has_changes(self) -> bool:
        counts = self.summary.get('counts', {})
        return any(
            counts.get(key, 0) for key in ('modified', 'added', 'removed', 'renamed_only')
        )


class SectionDiff(TimestampedModel):
    class ChangeType(models.TextChoices):
        UNCHANGED = 'unchanged', 'Unchanged'
        MODIFIED = 'modified', 'Modified'
        ADDED = 'added', 'Added'
        REMOVED = 'removed', 'Removed'
        RENAMED_ONLY = 'renamed_only', 'Renamed only'

    comparison = models.ForeignKey(Comparison, on_delete=models.CASCADE, related_name='diffs')
    section = models.ForeignKey(
        Section, null=True, blank=True, on_delete=models.CASCADE, related_name='+'
    )
    stable_key = models.CharField(max_length=250)
    heading_from = models.CharField(max_length=300, blank=True, default='')
    heading_to = models.CharField(max_length=300, blank=True, default='')
    change_type = models.CharField(max_length=13, choices=ChangeType.choices)
    similarity = models.FloatField(null=True, blank=True)
    order_index = models.PositiveIntegerField(default=0)
    # Word-level ops [{op: equal|insert|delete, text}] + the bboxes to highlight
    # on each side (normalized 0-1, top-left origin).
    word_diff = models.JSONField(default=list, blank=True)
    bboxes_from = models.JSONField(default=list, blank=True)
    bboxes_to = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['order_index']

    def __str__(self):
        return f'{self.stable_key}: {self.change_type}'
