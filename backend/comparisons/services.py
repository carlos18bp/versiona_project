"""Comparison domain services (flow E1)."""

from django.db import transaction

from audit import services as audit
from documents.models import DocumentVersion, SectionVersion
from documents.services.version_service import DomainError
from engine.services.comparison import compare_snapshots

from .models import Comparison, SectionDiff


def _snapshots(version: DocumentVersion) -> list[dict]:
    return [
        {
            'stable_key': snap.section.stable_key,
            'heading': snap.heading_text,
            'body_hash': snap.body_hash,
            'normalized_text': snap.normalized_text,
            'bboxes': snap.bboxes,
            'order_index': snap.order_index,
            'section_id': snap.section_id,
        }
        for snap in SectionVersion.objects.filter(document_version=version)
        .select_related('section')
        .order_by('order_index')
    ]


def ensure_comparable(version: DocumentVersion):
    if version.analysis_status != DocumentVersion.AnalysisStatus.READY:
        raise DomainError(
            f'La versión v{version.number} aún no está analizada o falló: no se puede comparar.',
            409,
        )
    if version.is_trashed:
        raise DomainError(f'La versión v{version.number} está en la papelera.', 409)


def validate_pair(document, from_version: DocumentVersion, to_version: DocumentVersion):
    """Guards run BEFORE any cache lookup: a comparison is never served for a
    pair that is not comparable today (E1-E01)."""
    if from_version.document_id != document.pk or to_version.document_id != document.pk:
        raise DomainError('Las versiones no pertenecen a este documento.', 400)
    if from_version.pk == to_version.pk:
        raise DomainError('Elige dos versiones distintas para comparar.', 400)
    ensure_comparable(from_version)
    ensure_comparable(to_version)


@transaction.atomic
def build_comparison(
    document, from_version: DocumentVersion, to_version: DocumentVersion, user=None,
    trigger: str = Comparison.Trigger.MANUAL, request=None,
) -> Comparison:
    """Idempotent per pair (I15): an existing done comparison is returned as-is."""
    validate_pair(document, from_version, to_version)

    existing = Comparison.objects.filter(
        from_version=from_version, to_version=to_version
    ).first()
    if existing and existing.status == Comparison.Status.DONE:
        return existing

    comparison = existing or Comparison.objects.create(
        document=document,
        from_version=from_version,
        to_version=to_version,
        trigger=trigger,
        created_by=user,
    )

    result = compare_snapshots(_snapshots(from_version), _snapshots(to_version))
    sections_by_key = {
        snap['stable_key']: snap['section_id']
        for snap in _snapshots(to_version) + _snapshots(from_version)
    }

    SectionDiff.objects.filter(comparison=comparison).delete()
    SectionDiff.objects.bulk_create([
        SectionDiff(
            comparison=comparison,
            section_id=sections_by_key.get(diff['stable_key']),
            **{k: v for k, v in diff.items() if k != 'stable_key'},
            stable_key=diff['stable_key'],
        )
        for diff in result['diffs']
    ])

    comparison.summary = {
        'counts': result['counts'],
        'text': result['summary_text'],
        'from': from_version.number,
        'to': to_version.number,
    }
    comparison.status = Comparison.Status.DONE
    comparison.save(update_fields=['summary', 'status', 'updated_at'])

    audit.record(
        org=document.project.organization, project=document.project, actor=user,
        event_type='comparison.created', obj=comparison,
        payload={'from': from_version.number, 'to': to_version.number,
                 'counts': result['counts'], 'trigger': trigger},
        request=request,
    )
    return comparison
