"""Async processing + TTL cleanup for anonymous public comparisons."""

from celery import shared_task
from django.utils import timezone

from documents.services import storage_service
from engine.services.analysis import OcrRequiredError

from .models import PublicComparison


@shared_task(name='public_tools.tasks.run_public_comparison', soft_time_limit=120)
def run_public_comparison(comparison_pk: int) -> None:
    from .services.public_comparison_service import build_result, delete_stored_files
    from .services.public_comparison_service import storage_key_for

    try:
        comparison = PublicComparison.objects.get(pk=comparison_pk)
    except PublicComparison.DoesNotExist:
        return
    if comparison.status == PublicComparison.Status.DONE:
        return

    comparison.status = PublicComparison.Status.PROCESSING
    comparison.save(update_fields=['status'])
    try:
        bytes_a = storage_service.get_bytes(storage_key_for(comparison.public_id, 'a'))
        bytes_b = storage_service.get_bytes(storage_key_for(comparison.public_id, 'b'))
        comparison.result = build_result(bytes_a, bytes_b)
        comparison.status = PublicComparison.Status.DONE
        comparison.save(update_fields=['result', 'status'])
    except OcrRequiredError:
        comparison.status = PublicComparison.Status.FAILED
        comparison.error_code = 'ocr_required'
        comparison.save(update_fields=['status', 'error_code'])
    except Exception:
        comparison.status = PublicComparison.Status.FAILED
        comparison.error_code = 'processing_failed'
        comparison.save(update_fields=['status', 'error_code'])
    finally:
        delete_stored_files(comparison)


@shared_task(name='public_tools.tasks.purge_expired_public_comparisons')
def purge_expired_public_comparisons() -> int:
    from .services.public_comparison_service import delete_stored_files

    expired = PublicComparison.objects.filter(expires_at__lt=timezone.now())
    purged = 0
    for comparison in expired:
        delete_stored_files(comparison)  # covers rows whose worker died mid-job
        comparison.delete()
        purged += 1
    return purged
