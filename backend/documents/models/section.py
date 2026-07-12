"""
Section — stable identity across versions (docs/plan/02 §3.3; the ground D5
stands on). Identity does NOT depend on position (survives reordering) nor on
the exact heading (renames re-assign the SAME row via content matching,
docs/plan/05 §4). SectionVersion snapshots the content per version;
SectionLineage is the append-only probatory evidence of every matching
decision.

Bounding boxes travel normalized 0–1, top-left origin: [{page, x0, y0, x1, y1}].
"""

from django.db import models

from core.models import TimestampedModel

from .document import Document
from .version import DocumentVersion


class Section(TimestampedModel):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='sections')
    stable_key = models.CharField(max_length=250)
    title_current = models.CharField(max_length=300)
    level = models.PositiveSmallIntegerField(default=1)
    created_in_version = models.ForeignKey(
        DocumentVersion, on_delete=models.CASCADE, related_name='sections_created'
    )
    retired_in_version = models.ForeignKey(
        DocumentVersion,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='sections_retired',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['document', 'stable_key'], name='uniq_section_key'),
        ]

    def __str__(self):
        return f'{self.stable_key} ({self.document})'


class SectionVersion(TimestampedModel):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='snapshots')
    document_version = models.ForeignKey(
        DocumentVersion, on_delete=models.CASCADE, related_name='section_versions'
    )
    heading_text = models.CharField(max_length=300)
    heading_hash = models.CharField(max_length=64)
    body_hash = models.CharField(max_length=64)
    normalized_text = models.TextField()
    page_start = models.PositiveIntegerField()
    page_end = models.PositiveIntegerField()
    bboxes = models.JSONField(default=list)
    order_index = models.PositiveIntegerField()
    ocr_confidence = models.FloatField(null=True, blank=True)
    char_count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['section', 'document_version'], name='uniq_section_snapshot'
            ),
            models.UniqueConstraint(
                fields=['document_version', 'order_index'], name='uniq_snapshot_order'
            ),
        ]
        ordering = ['order_index']

    def __str__(self):
        return f'{self.section.stable_key} @ v{self.document_version.number}'


class SectionLineage(TimestampedModel):
    class Relation(models.TextChoices):
        SAME = 'same', 'Same'
        RENAMED = 'renamed', 'Renamed'
        SPLIT_FROM = 'split_from', 'Split from'
        MERGED_INTO = 'merged_into', 'Merged into'
        ADDED = 'added', 'Added'
        REMOVED = 'removed', 'Removed'

    document_version = models.ForeignKey(
        DocumentVersion, on_delete=models.CASCADE, related_name='lineage'
    )
    from_section = models.ForeignKey(
        Section, null=True, blank=True, on_delete=models.CASCADE, related_name='+'
    )
    to_section = models.ForeignKey(
        Section, null=True, blank=True, on_delete=models.CASCADE, related_name='+'
    )
    relation = models.CharField(max_length=12, choices=Relation.choices)
    similarity = models.FloatField(null=True, blank=True)
    decided_mode = models.CharField(max_length=12, default='auto')

    def __str__(self):
        return f'{self.relation} @ v{self.document_version.number}'
