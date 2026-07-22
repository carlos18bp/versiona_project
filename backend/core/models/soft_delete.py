"""
Soft-delete (trash) support — docs/plan/02 deltas, kit 3 (docs/audit/02 G07/G11).

Semantics:
- `Model.objects` excludes trashed rows; `Model.all_objects` sees everything.
- `instance.soft_delete(user)` sends to trash; `restore()` brings it back.
- Physical deletion happens ONLY through the purge path (beat task / owner
  endpoint) after the grace window — a PostgreSQL trigger on guarded tables
  additionally rejects DELETE while `deleted_at IS NULL` (I2/T2).
- The grace window lives in settings.TRASH_RETENTION_DAYS (env, default 30):
  nothing hardcoded (kit 7).
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def trashed(self):
        return self.filter(deleted_at__isnull=False)

    def purgeable(self, now=None):
        now = now or timezone.now()
        cutoff = now - timezone.timedelta(days=trash_retention_days())
        return self.trashed().filter(deleted_at__lt=cutoff)


class AliveManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class AllObjectsManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    pass


def trash_retention_days() -> int:
    return int(getattr(settings, 'TRASH_RETENTION_DAYS', 30))


class SoftDeletableModel(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    objects = AliveManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    @property
    def is_trashed(self) -> bool:
        return self.deleted_at is not None

    @property
    def purge_after(self):
        """Derived deadline shown in the trash UI (docs/audit/03 §9)."""
        if self.deleted_at is None:
            return None
        return self.deleted_at + timezone.timedelta(days=trash_retention_days())

    def soft_delete(self, user=None):
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=['deleted_at', 'deleted_by', 'updated_at'])

    def restore(self):
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['deleted_at', 'deleted_by', 'updated_at'])
