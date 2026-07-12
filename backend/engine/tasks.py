"""
Engine Celery tasks (docs/plan/05 §7 — AnalysisJob slice, It1).

Contract: the domain enqueues an EngineJob and consumes its `result`.
Idempotency by natural key (I15): a `done` job re-dispatched returns its
stored result without side effects. Parse errors are PERMANENT (no retry,
C1-E04); infrastructure errors retry with backoff (3 attempts).
"""

import logging

from celery import shared_task
from django.db import transaction

from documents.models import DocumentVersion
from documents.services import storage_service
from engine.models import EngineJob
from engine.services.analysis import EncryptedPdfError, InvalidPdfError, analyze_bytes
from engine.services.persistence import persist_analysis

logger = logging.getLogger(__name__)


def enqueue_analysis(version: DocumentVersion) -> EngineJob:
    """Create (or reuse) the analysis job for a version and dispatch it."""
    job, created = EngineJob.objects.get_or_create(
        idempotency_key=f'analysis:v{version.pk}',
        defaults={
            'job_type': EngineJob.Type.ANALYSIS,
            'document_version': version,
            'payload': {'version_id': version.pk, 'file_key': version.file_key},
        },
    )
    if job.status == EngineJob.Status.DONE:
        return job
    async_result = run_analysis.apply_async(args=[job.pk], queue='engine_heavy')
    EngineJob.objects.filter(pk=job.pk).update(celery_task_id=async_result.id or '')
    job.refresh_from_db()
    return job


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def run_analysis(self, job_id: int):
    job = EngineJob.objects.select_related('document_version__document').get(pk=job_id)
    if job.status == EngineJob.Status.DONE:
        return job.result
    version = job.document_version

    EngineJob.objects.filter(pk=job.pk).update(
        status=EngineJob.Status.RUNNING, attempts=job.attempts + 1
    )
    DocumentVersion.all_objects.filter(pk=version.pk).update(
        analysis_status=DocumentVersion.AnalysisStatus.PROCESSING
    )
    version.refresh_from_db()

    try:
        data = storage_service.get_bytes(version.file_key)
        analysis = analyze_bytes(data)
        with transaction.atomic():
            result = persist_analysis(version, analysis)
        EngineJob.objects.filter(pk=job.pk).update(
            status=EngineJob.Status.DONE, result=result, error_detail=''
        )
        return result
    except (EncryptedPdfError, InvalidPdfError) as exc:
        _fail(job, version, f'Documento inválido: {exc}')
        return None
    except Exception as exc:  # infrastructure: retry with backoff
        logger.exception('Analysis job %s failed (attempt %s)', job.pk, job.attempts + 1)
        if self.request.retries >= self.max_retries:
            _fail(job, version, f'Error de análisis tras reintentos: {exc}')
            return None
        raise self.retry(exc=exc)


def _fail(job: EngineJob, version: DocumentVersion, detail: str):
    EngineJob.objects.filter(pk=job.pk).update(
        status=EngineJob.Status.FAILED, error_detail=detail[:1000]
    )
    DocumentVersion.all_objects.filter(pk=version.pk).update(
        analysis_status=DocumentVersion.AnalysisStatus.FAILED, error_detail=detail[:1000]
    )
