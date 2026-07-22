"""
SealValidityRecord — THE piece of D5 (docs/plan/02 §3.4, invariants I4/I11).

Append-only. A seal is valid at version N (> the version it signed) **iff** an
unbroken chain of `preserved` records reaches N; one `invalidated` or
`superseded` link cuts the chain permanently. The Seal row itself is never
touched — the validity lives in this ledger, with the evidence of WHY.
"""

from django.conf import settings
from django.db import models

from core.models import TimestampedModel
from documents.models import DocumentVersion

from .seal import Seal


class SealValidityRecord(TimestampedModel):
    class Decision(models.TextChoices):
        PRESERVED = 'preserved', 'Preserved (with certificate)'
        INVALIDATED = 'invalidated', 'Invalidated (requires re-review)'
        PENDING = 'pending_confirmation', 'Pending coordinator confirmation'
        SUPERSEDED = 'superseded', 'Superseded by a newer version'

    class Mode(models.TextChoices):
        AUTO = 'auto', 'Automatic'
        COORDINATOR = 'coordinator', 'Coordinator'

    seal = models.ForeignKey(Seal, on_delete=models.CASCADE, related_name='validity_records')
    to_document_version = models.ForeignKey(
        DocumentVersion, on_delete=models.CASCADE, related_name='seal_validity_records'
    )
    comparison = models.ForeignKey(
        'comparisons.Comparison', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    decision = models.CharField(max_length=20, choices=Decision.choices)
    proposed_decision = models.CharField(
        max_length=20, choices=Decision.choices, blank=True, default=''
    )
    reason_code = models.CharField(max_length=40, blank=True, default='')
    evidence = models.JSONField(default=dict, blank=True)
    decided_mode = models.CharField(max_length=12, choices=Mode.choices, default=Mode.AUTO)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['seal', 'to_document_version'], name='uniq_validity_per_version'
            ),
        ]
        ordering = ['to_document_version__number']

    def __str__(self):
        return f'{self.seal_id} @ v{self.to_document_version.number}: {self.decision}'

    @property
    def is_final(self) -> bool:
        return self.decision != self.Decision.PENDING
