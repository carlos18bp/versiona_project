"""
Document (docs/plan/02 §3.3 — flows C1/C3). Soft-deletable (kit 3, T14):
trash allowed only while NO version is sealed or approved (enforced in the
trash service); the (project, slug) uniqueness is partial for trash reuse.
"""

from django.db import models

from core.models import PublicIdModel, SoftDeletableModel, TimestampedModel
from projects.models import Project


class Document(PublicIdModel, TimestampedModel, SoftDeletableModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220)
    approved_version = models.ForeignKey(
        'documents.DocumentVersion',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    latest_number = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'slug'],
                condition=models.Q(deleted_at__isnull=True),
                name='uniq_document_slug_alive',
            ),
        ]

    def __str__(self):
        return self.title
