"""
Versioned, immutable project configuration (docs/plan/02 §3.2 — flow B3, I8).

Editing configuration (It5) always creates a NEW row; every DocumentVersion
pins the config row that was current at its creation, which makes B3
non-retroactivity structural. It1 only auto-creates version 1 with defaults.
"""

from django.conf import settings as django_settings
from django.db import models

from core.models import TimestampedModel

from .project import Project


def default_approval_policy() -> dict:
    """Every valid seal required comes from section owners; It1 default:
    any single reviewer seal approves (refined in It3/It5)."""
    return {'required': 'all_assigned'}


class ProjectConfigVersion(TimestampedModel):
    class D5Mode(models.TextChoices):
        AUTO = 'auto', 'Automatic'
        COORDINATOR = 'coordinator', 'Coordinator confirms'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='config_versions')
    number = models.PositiveIntegerField()
    approval_policy = models.JSONField(default=default_approval_policy)
    d5_mode = models.CharField(max_length=12, choices=D5Mode.choices, default=D5Mode.AUTO)
    coordinators = models.JSONField(default=list, blank=True)
    # E3: [{key, label, type: required_section|required_text|forbidden_text,
    #       param, severity: fail|warn}] — evaluated against the PINNED config
    #       of each version (I8), never retroactively.
    checklist = models.JSONField(default=list, blank=True)
    # B3: {stable_key: [user_id, ...]} — feeds the 'all_assigned' approval
    # policy and the reviewer suggestions (D1).
    section_owners = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        django_settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='+'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['project', 'number'], name='uniq_project_config_number'),
        ]
        ordering = ['-number']

    def __str__(self):
        return f'{self.project} config v{self.number}'

    @classmethod
    def current_for(cls, project: Project) -> 'ProjectConfigVersion':
        current = cls.objects.filter(project=project).order_by('-number').first()
        if current is None:
            current = cls.objects.create(project=project, number=1)
        return current
