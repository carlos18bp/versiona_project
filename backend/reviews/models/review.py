"""ReviewRequest + ReviewAssignment (docs/plan/02 §3.4 — flow D1).

Opening a request freezes the version's commit message (I2b: `is_draft`
consults the open requests) and puts the work in each reviewer's inbox. An
assignment completes when its reviewer SEALS the version — the seal is the
act of review (D4)."""

from django.conf import settings
from django.db import models

from core.models import PublicIdModel, TimestampedModel
from documents.models import DocumentVersion


class ReviewRequest(PublicIdModel, TimestampedModel):
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        SUPERSEDED = 'superseded', 'Superseded by a newer version'

    document_version = models.ForeignKey(
        DocumentVersion, on_delete=models.CASCADE, related_name='review_requests'
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='review_requests_made'
    )
    message = models.TextField(blank=True, default='')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    due_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['document_version'],
                condition=models.Q(status='open'),
                name='uniq_open_request_per_version',
            ),
        ]

    def __str__(self):
        return f'review v{self.document_version.number} [{self.status}]'


class ReviewAssignment(TimestampedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        DONE = 'done', 'Done'

    review_request = models.ForeignKey(
        ReviewRequest, on_delete=models.CASCADE, related_name='assignments'
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='review_assignments'
    )
    # "all" or a list of stable_keys the author asks this reviewer to focus on.
    scope = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['review_request', 'reviewer'], name='uniq_assignment_per_reviewer'
            ),
        ]

    def __str__(self):
        return f'{self.reviewer} ← {self.review_request} [{self.status}]'
