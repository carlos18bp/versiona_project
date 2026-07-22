"""
AuditEvent — append-only audit trail (docs/plan/02 §3.7, 08 §4; base for F3).

Denormalized ids, no cascades: the trail survives any deletion. Written in
the same transaction as the mutation via `audit.services.record`. The project
activity feed (kit 6, It4) reads a whitelisted, ip-free projection of this
table; the raw log is org-admin only (T12).
"""

from django.conf import settings
from django.db import models

from core.models import TimestampedModel


class AuditEvent(TimestampedModel):
    org_id_ref = models.BigIntegerField(db_index=True)
    project_id_ref = models.BigIntegerField(null=True, blank=True, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    event_type = models.CharField(max_length=60, db_index=True)
    object_type = models.CharField(max_length=40, blank=True, default='')
    object_id_ref = models.CharField(max_length=64, blank=True, default='')
    payload = models.JSONField(default=dict, blank=True)
    request_id = models.CharField(max_length=64, blank=True, default='')
    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['project_id_ref', 'created_at']),
            models.Index(fields=['org_id_ref', 'event_type', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.event_type} ({self.created_at:%Y-%m-%d %H:%M})'
