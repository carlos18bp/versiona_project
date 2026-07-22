"""Ephemeral guarantees: files deleted after processing, rows purged on TTL."""

from datetime import timedelta
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from documents.services import storage_service
from public_tools.models import PublicComparison
from public_tools.services.public_comparison_service import (
    create_public_comparison,
    storage_key_for,
)
from public_tools.tasks import purge_expired_public_comparisons

TESTDATA = Path(__file__).resolve().parents[3] / 'testdata' / 'pdfs'


def upload(name: str) -> SimpleUploadedFile:
    return SimpleUploadedFile(
        name, (TESTDATA / name).read_bytes(), content_type='application/pdf'
    )


@pytest.mark.django_db
@pytest.mark.escenario('PC-P01')
def test_task_deletes_storage_objects_after_success():
    comparison = create_public_comparison(
        upload('contrato_v1.pdf'), upload('contrato_v2.pdf'), ip='203.0.113.9'
    )

    assert comparison.status == PublicComparison.Status.DONE
    assert storage_service.head(storage_key_for(comparison.public_id, 'a')) is None
    assert storage_service.head(storage_key_for(comparison.public_id, 'b')) is None


@pytest.mark.django_db
@pytest.mark.escenario('PC-P02')
def test_task_failure_marks_failed_and_cleans_storage(monkeypatch):
    def explode(*args, **kwargs):
        raise RuntimeError('boom')

    monkeypatch.setattr(
        'public_tools.services.public_comparison_service.build_result', explode
    )

    comparison = create_public_comparison(
        upload('contrato_v1.pdf'), upload('contrato_v2.pdf'), ip='203.0.113.9'
    )

    assert comparison.status == PublicComparison.Status.FAILED
    assert comparison.error_code == 'processing_failed'
    assert storage_service.head(storage_key_for(comparison.public_id, 'a')) is None


@pytest.mark.django_db
@pytest.mark.escenario('PC-P03')
def test_purge_deletes_expired_rows():
    comparison = PublicComparison.objects.create(
        status=PublicComparison.Status.DONE,
        result={'counts': {}},
        expires_at=timezone.now() - timedelta(hours=2),
    )

    purged = purge_expired_public_comparisons()

    assert purged == 1
    assert not PublicComparison.objects.filter(pk=comparison.pk).exists()
