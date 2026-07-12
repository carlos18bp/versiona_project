"""In-app notifications + the event catalog (kit 5 — docs/plan/03 §6)."""

from django.conf import settings
from django.db import models

from core.models import PublicIdModel, TimestampedModel

# event_key → defaults. `seal.preserved` is OFF on both channels by design:
# the promise (S6) is that a reviewer whose seal survived hears NOTHING.
NOTIFICATION_CATALOG = {
    'seal.invalidated': {
        'label_es': 'Tu sello requiere re-revisión',
        'label_en': 'Your seal requires re-review',
        'default_email': True,
        'default_in_app': True,
        'mandatory_in_app': True,  # never silenceable: it is assigned work
    },
    'seal.preserved': {
        'label_es': 'Tu sello se conservó',
        'label_en': 'Your seal was preserved',
        'default_email': False,
        'default_in_app': False,
        'mandatory_in_app': False,
    },
    'seal.placed': {
        'label_es': 'Se puso un sello en tu documento',
        'label_en': 'A seal was placed on your document',
        'default_email': True,
        'default_in_app': True,
        'mandatory_in_app': False,
    },
    'version.approved': {
        'label_es': 'La versión quedó aprobada',
        'label_en': 'The version was approved',
        'default_email': True,
        'default_in_app': True,
        'mandatory_in_app': False,
    },
    'seal_plan.pending': {
        'label_es': 'Hay un plan de invalidación por confirmar',
        'label_en': 'An invalidation plan awaits confirmation',
        'default_email': True,
        'default_in_app': True,
        'mandatory_in_app': True,
    },
}


class Notification(PublicIdModel, TimestampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications'
    )
    org_id_ref = models.BigIntegerField(db_index=True)
    project_id_ref = models.BigIntegerField(null=True, blank=True, db_index=True)
    event_key = models.CharField(max_length=40)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True, default='')
    link = models.CharField(max_length=500, blank=True, default='')
    payload = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    email_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['user', 'read_at'])]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.event_key} → {self.user}'


class NotificationPreference(TimestampedModel):
    """Absence of a row means "use the catalog default" (no rows are seeded)."""

    class Channel(models.TextChoices):
        IN_APP = 'in_app', 'In app'
        EMAIL = 'email', 'Email'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_prefs'
    )
    event_key = models.CharField(max_length=40)
    channel = models.CharField(max_length=8, choices=Channel.choices)
    enabled = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'event_key', 'channel'], name='uniq_notification_pref'
            ),
        ]

    def __str__(self):
        return f'{self.user}:{self.event_key}:{self.channel}={self.enabled}'
