"""
Anchored observations (docs/plan/02 §3.5 — flow D3, invariant I14).

The thread anchors to the SECTION IDENTITY (the same one D5 trusts), not to a
version: every new version gets exactly ONE anchor row, produced by the
re-anchor pass — `exact` when the section is intact, `reanchored_section` when
its content moved/changed, `orphaned` when it disappeared. Threads are never
deleted (I14)."""

from django.conf import settings
from django.db import models

from core.models import PublicIdModel, TimestampedModel
from documents.models import Document, DocumentVersion, Section


class Observation(PublicIdModel, TimestampedModel):
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        ANSWERED = 'answered', 'Answered'
        RESOLVED = 'resolved', 'Resolved'

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='observations')
    section = models.ForeignKey(
        Section, null=True, blank=True, on_delete=models.SET_NULL, related_name='observations'
    )
    created_on_version = models.ForeignKey(
        DocumentVersion, on_delete=models.CASCADE, related_name='observations_created'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='observations'
    )
    body = models.TextField()
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.OPEN)
    resolved_in_version = models.ForeignKey(
        DocumentVersion, null=True, blank=True, on_delete=models.SET_NULL, related_name='+'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'obs {self.pk} [{self.status}] @ {self.document}'


class ObservationAnchor(TimestampedModel):
    class Method(models.TextChoices):
        EXACT = 'exact', 'Exact (section intact)'
        REANCHORED = 'reanchored_section', 'Re-anchored to the section'
        ORPHANED = 'orphaned', 'Orphaned (section gone)'

    observation = models.ForeignKey(
        Observation, on_delete=models.CASCADE, related_name='anchors'
    )
    document_version = models.ForeignKey(
        DocumentVersion, on_delete=models.CASCADE, related_name='observation_anchors'
    )
    page = models.PositiveIntegerField(default=1)
    # Normalized quads [{page,x0,y0,x1,y1}] — same contract as diff bboxes.
    quads = models.JSONField(default=list, blank=True)
    text_snippet = models.CharField(max_length=300, blank=True, default='')
    method = models.CharField(max_length=20, choices=Method.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['observation', 'document_version'], name='uniq_anchor_per_version'
            ),
        ]

    def __str__(self):
        return f'anchor obs={self.observation_id} v={self.document_version_id} [{self.method}]'


class ObservationReply(PublicIdModel, TimestampedModel):
    observation = models.ForeignKey(
        Observation, on_delete=models.CASCADE, related_name='replies'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+'
    )
    body = models.TextField()
    # Recorded when this reply carried a state transition (I14 audit trail).
    status_change = models.CharField(max_length=20, blank=True, default='')

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'reply {self.pk} @ obs {self.observation_id}'
