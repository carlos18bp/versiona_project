"""
Configurable checks (docs/plan/02 §3.6 — flow E3) + org checklist templates
(kit 2, copy-on-apply: applying a template COPIES its items into a new config
version — no live link, so I8 stays structural).
"""

from django.conf import settings
from django.db import models

from core.models import PublicIdModel, TimestampedModel
from documents.models import DocumentVersion
from orgs.models import Organization
from projects.models import ProjectConfigVersion


class ChecklistTemplate(PublicIdModel, TimestampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='checklist_templates'
    )
    name = models.CharField(max_length=120)
    # Same shape as ProjectConfigVersion.checklist items.
    items = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='+'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['organization', 'name'], name='uniq_template_name'),
        ]
        ordering = ['name']

    def __str__(self):
        return f'{self.organization} · {self.name}'


class CheckRun(TimestampedModel):
    class Status(models.TextChoices):
        DONE = 'done', 'Done'
        FAILED = 'failed', 'Failed'

    document_version = models.ForeignKey(
        DocumentVersion, on_delete=models.CASCADE, related_name='check_runs'
    )
    config_version = models.ForeignKey(
        ProjectConfigVersion, on_delete=models.PROTECT, related_name='+'
    )
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.DONE)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'checks v{self.document_version.number} [{self.status}]'


class CheckResult(TimestampedModel):
    class Outcome(models.TextChoices):
        PASS = 'pass', 'Pass'
        WARN = 'warn', 'Warn'
        FAIL = 'fail', 'Fail'

    check_run = models.ForeignKey(CheckRun, on_delete=models.CASCADE, related_name='results')
    key = models.CharField(max_length=80)
    label = models.CharField(max_length=200)
    outcome = models.CharField(max_length=4, choices=Outcome.choices)
    # {section, page, snippet, reason} — enough to jump to the spot (E3).
    evidence = models.JSONField(default=dict, blank=True)
    message = models.CharField(max_length=300, blank=True, default='')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['check_run', 'key'], name='uniq_result_per_check'),
        ]

    def __str__(self):
        return f'{self.key}: {self.outcome}'
