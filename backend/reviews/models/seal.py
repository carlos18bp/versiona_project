"""
Seal — the approval act (docs/plan/02 §3.4 — flow D4, invariants I4/I6).

Append-only: a Seal row is NEVER updated or deleted. Withdrawing a seal
pre-approval (DP-08) is an append event (`revoked_at`, an explicit column the
signature does not cover, plus an AuditEvent), never a delete.

The signature binds the act to the exact binary: the canonical payload carries
the version sha256 + the covered sections with their body hashes, so a third
party can verify it offline with the public key (E4 groundwork).
"""

from django.conf import settings
from django.db import models

from core.models import PublicIdModel, TimestampedModel
from documents.models import DocumentVersion, Section


class Seal(PublicIdModel, TimestampedModel):
    document_version = models.ForeignKey(
        DocumentVersion, on_delete=models.CASCADE, related_name='seals'
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='seals'
    )
    covers_all = models.BooleanField(default=False)
    signed_payload = models.JSONField()
    signature = models.TextField()
    key_id = models.CharField(max_length=40)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['document_version', 'reviewer'],
                condition=models.Q(revoked_at__isnull=True),
                name='uniq_active_seal_per_reviewer',
            ),
        ]
        ordering = ['created_at']

    def __str__(self):
        return f'seal {self.reviewer} @ v{self.document_version.number}'

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None

    @property
    def covered_keys(self) -> list[str]:
        if self.covers_all:
            return ['*']
        return sorted(
            self.covered_sections.values_list('section__stable_key', flat=True)
        )


class SealSection(TimestampedModel):
    """Explicit M2M: which sections the seal covers (docs/plan/02 §3.4)."""

    seal = models.ForeignKey(Seal, on_delete=models.CASCADE, related_name='covered_sections')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='+')
    body_hash = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['seal', 'section'], name='uniq_seal_section'),
        ]

    def __str__(self):
        return f'{self.seal_id}:{self.section.stable_key}'
