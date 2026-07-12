"""
EngineJob — the async unit of engine work (docs/plan/02 §3.7, docs/plan/05 §7).

The domain only enqueues jobs and consumes their `result`; idempotency by
natural key (I15): a `done` job re-enqueued returns its stored result.
"""

from django.db import models

from core.models import PublicIdModel, TimestampedModel


class EngineJob(PublicIdModel, TimestampedModel):
    class Type(models.TextChoices):
        ANALYSIS = 'analysis', 'Analysis'
        COMPARISON = 'comparison', 'Comparison'
        SEAL_REVIEW = 'seal_review', 'Seal review (D5)'
        REANCHOR = 'reanchor', 'Re-anchor observations'
        CHECK_RUN = 'check_run', 'Check run'
        SAMPLE_PROJECT = 'sample_project', 'Sample project seed (A1)'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        RUNNING = 'running', 'Running'
        DONE = 'done', 'Done'
        FAILED = 'failed', 'Failed'

    job_type = models.CharField(max_length=16, choices=Type.choices)
    payload = models.JSONField(default=dict)
    result = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    attempts = models.PositiveSmallIntegerField(default=0)
    idempotency_key = models.CharField(max_length=200, unique=True)
    celery_task_id = models.CharField(max_length=100, blank=True, default='')
    error_detail = models.TextField(blank=True, default='')
    document_version = models.ForeignKey(
        'documents.DocumentVersion',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='engine_jobs',
    )

    class Meta:
        indexes = [models.Index(fields=['job_type', 'status'])]

    def __str__(self):
        return f'{self.job_type}:{self.idempotency_key} [{self.status}]'
