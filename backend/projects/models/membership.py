"""Per-project membership and role (docs/plan/02 §3.2 — flow A2, matrix 03 §5)."""

from django.conf import settings
from django.db import models

from core.models import TimestampedModel

from .project import Project


class ProjectMembership(TimestampedModel):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        EDITOR = 'editor', 'Editor'
        REVIEWER = 'reviewer', 'Reviewer'
        VIEWER = 'viewer', 'Viewer'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='project_memberships'
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.VIEWER)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['project', 'user'], name='uniq_project_membership'),
        ]

    def __str__(self):
        return f'{self.user} @ {self.project} ({self.role})'
