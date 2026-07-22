"""EngineJob task edges: idempotent short-circuits (I15), permanent parse
failures (C1-E04) and the infrastructure retry ladder (docs/plan/05 §7)."""

from pathlib import Path
from unittest.mock import patch

import pytest

from documents.models import DocumentVersion
from engine.models import EngineJob
from engine.tasks import enqueue_analysis, run_analysis

TESTDATA = Path(__file__).resolve().parents[3] / 'testdata' / 'pdfs'


def load(name: str) -> bytes:
    return (TESTDATA / name).read_bytes()


@pytest.fixture
def version(document_with_versions):
    _document, versions = document_with_versions(n_versions=1)
    return versions[0]


@pytest.fixture
def make_job(version):
    def _make(**overrides):
        fields = {
            'job_type': EngineJob.Type.ANALYSIS,
            'document_version': version,
            'payload': {'version_id': version.pk, 'file_key': version.file_key},
            'idempotency_key': f'analysis:v{version.pk}',
            'status': EngineJob.Status.PENDING,
        }
        fields.update(overrides)
        return EngineJob.objects.create(**fields)

    return _make


@pytest.mark.django_db
@pytest.mark.escenario('C1-A04')
def test_enqueue_analysis_returns_the_done_job_without_redispatch(version, make_job):
    job = make_job(status=EngineJob.Status.DONE, result={'sections': {'total': 1}})

    returned = enqueue_analysis(version)

    assert returned.pk == job.pk
    assert returned.celery_task_id == ''
    assert EngineJob.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.escenario('C1-A05')
def test_run_analysis_returns_the_stored_result_for_a_done_job(make_job):
    job = make_job(status=EngineJob.Status.DONE, result={'cached': True})

    result = run_analysis(job.pk)

    assert result == {'cached': True}
    job.refresh_from_db()
    assert job.attempts == 0


@pytest.mark.django_db
@pytest.mark.escenario('C1-E02')
def test_run_analysis_marks_a_corrupt_pdf_as_permanent_failure(version, make_job):
    job = make_job()

    with patch('engine.tasks.storage_service.get_bytes', return_value=load('corrupto.pdf')):
        result = run_analysis(job.pk)

    assert result is None
    job.refresh_from_db()
    assert job.status == EngineJob.Status.FAILED
    assert job.error_detail.startswith('Documento inválido:')
    version.refresh_from_db()
    assert version.analysis_status == DocumentVersion.AnalysisStatus.FAILED


@pytest.mark.django_db
@pytest.mark.escenario('C1-E01')
def test_run_analysis_marks_an_encrypted_pdf_as_permanent_failure(version, make_job):
    job = make_job()

    with patch('engine.tasks.storage_service.get_bytes', return_value=load('protegido.pdf')):
        result = run_analysis(job.pk)

    assert result is None
    job.refresh_from_db()
    assert job.status == EngineJob.Status.FAILED
    assert job.error_detail.startswith('Documento inválido:')


@pytest.mark.django_db
@pytest.mark.escenario('C1-E05')
def test_run_analysis_requests_a_retry_on_infrastructure_error(version, make_job):
    job = make_job()

    with patch('engine.tasks.storage_service.get_bytes', side_effect=RuntimeError('minio caído')):
        with pytest.raises(RuntimeError):
            run_analysis(job.pk)

    job.refresh_from_db()
    assert job.status == EngineJob.Status.RUNNING
    assert job.attempts == 1


@pytest.mark.django_db
@pytest.mark.escenario('C1-E05')
def test_run_analysis_fails_permanently_after_exhausting_retries(version, make_job):
    job = make_job()

    with patch('engine.tasks.storage_service.get_bytes', side_effect=RuntimeError('minio caído')):
        outcome = run_analysis.apply(args=[job.pk], retries=3)

    assert outcome.result is None
    job.refresh_from_db()
    assert job.status == EngineJob.Status.FAILED
    assert job.error_detail.startswith('Error de análisis tras reintentos')
    version.refresh_from_db()
    assert version.analysis_status == DocumentVersion.AnalysisStatus.FAILED
