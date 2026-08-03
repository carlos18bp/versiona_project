"""
Project (docs/plan/02 §3.2 — flows B1/B2/B4).

Soft-deletable (trash, kit 3): the (org, slug) uniqueness is partial so a new
project can reuse the slug of a trashed one; restore validates collisions
(T13). `status` gains `archived` (B4): reversible, read-only, always allowed.
"""

from django.db import models

from core.models import PublicIdModel, SoftDeletableModel, TimestampedModel
from orgs.models import Organization


class Project(PublicIdModel, TimestampedModel, SoftDeletableModel):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        ARCHIVED = 'archived', 'Archived'

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='projects'
    )
    name = models.CharField(max_length=140)
    slug = models.SlugField(max_length=160)
    description = models.TextField(blank=True, default='')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    is_sample = models.BooleanField(default=False)

    # Stand-in for the partial unique index. MySQL 8 has none
    # (mysql.features.supports_partial_indexes = False) and Django SKIPS a
    # conditional UniqueConstraint there without failing, so the condition moves
    # into the column instead: a trashed row carries NULL and a UNIQUE key
    # ignores NULLs. STORED because PostgreSQL 16 has no VIRTUAL columns.
    slug_alive = models.GeneratedField(
        expression=models.Case(
            models.When(deleted_at__isnull=True, then=models.F('slug')),
            default=models.Value(None),
            output_field=models.SlugField(max_length=160),
        ),
        output_field=models.SlugField(max_length=160),
        db_persist=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'slug_alive'],
                name='uniq_project_slug_alive',
            ),
        ]
        indexes = [models.Index(fields=['organization', 'status'])]

    def __str__(self):
        return self.name

    @property
    def is_archived(self) -> bool:
        return self.status == self.Status.ARCHIVED

    @property
    def is_read_only(self) -> bool:
        """Archived or trashed projects reject every mutation (B4-L01)."""
        return self.is_archived or self.is_trashed
