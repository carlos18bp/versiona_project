"""
Persistence of an analysis result: Section identity matching (steps 1–2 of
docs/plan/05 §4), SectionVersion snapshots, lineage evidence, thumbnail and
version fields. Runs inside one transaction; deterministic upserts (I15).
"""

from django.contrib.postgres.search import SearchVector
from django.db import transaction

from documents.models import Document, DocumentVersion, Section, SectionLineage, SectionVersion
from documents.services import storage_service


@transaction.atomic
def persist_analysis(version: DocumentVersion, analysis: dict) -> dict:
    document: Document = version.document
    alive_sections = {
        section.stable_key: section
        for section in document.sections.filter(retired_in_version__isnull=True)
    }
    by_body_hash: dict[str, Section] = {}
    if alive_sections:
        previous = (
            SectionVersion.objects.filter(
                section__in=alive_sections.values(),
                document_version__number__lt=version.number,
            )
            .order_by('section_id', '-document_version__number')
            .select_related('section')
        )
        seen = set()
        for snapshot in previous:
            if snapshot.section_id in seen:
                continue
            seen.add(snapshot.section_id)
            by_body_hash.setdefault(snapshot.body_hash, snapshot.section)

    matched_ids = set()
    counters = {'same': 0, 'renamed': 0, 'added': 0, 'removed': 0}

    for payload in analysis['sections']:
        section = alive_sections.get(payload['stable_key'])
        relation = SectionLineage.Relation.SAME
        if section is None:
            candidate = by_body_hash.get(payload['body_hash'])
            if candidate is not None and candidate.pk not in matched_ids:
                # Step 2: exact-content match ⇒ rename re-assigns the SAME row
                section = candidate
                section.stable_key = payload['stable_key']
                section.title_current = payload['heading']
                section.save(update_fields=['stable_key', 'title_current', 'updated_at'])
                relation = SectionLineage.Relation.RENAMED
            else:
                section = Section.objects.create(
                    document=document,
                    stable_key=payload['stable_key'],
                    title_current=payload['heading'],
                    level=payload['level'],
                    created_in_version=version,
                )
                relation = SectionLineage.Relation.ADDED
        else:
            if section.title_current != payload['heading']:
                section.title_current = payload['heading']
                section.save(update_fields=['title_current', 'updated_at'])

        matched_ids.add(section.pk)
        counters['same' if relation == SectionLineage.Relation.SAME else
                 'renamed' if relation == SectionLineage.Relation.RENAMED else 'added'] += 1

        SectionVersion.objects.create(
            section=section,
            document_version=version,
            heading_text=payload['heading'],
            heading_hash=payload['heading_hash'],
            body_hash=payload['body_hash'],
            normalized_text=payload['normalized_text'],
            page_start=payload['page_start'],
            page_end=payload['page_end'],
            bboxes=payload['bboxes'],
            order_index=payload['order_index'],
            ocr_confidence=payload.get('ocr_confidence'),
            char_count=payload['char_count'],
        )
        if relation != SectionLineage.Relation.SAME:
            SectionLineage.objects.create(
                document_version=version,
                from_section=section if relation == SectionLineage.Relation.RENAMED else None,
                to_section=section,
                relation=relation,
            )

    for stale in alive_sections.values():
        if stale.pk not in matched_ids:
            stale.retired_in_version = version
            stale.save(update_fields=['retired_in_version', 'updated_at'])
            SectionLineage.objects.create(
                document_version=version,
                from_section=stale,
                relation=SectionLineage.Relation.REMOVED,
            )
            counters['removed'] += 1

    thumb = storage_service.thumb_key(document, version.number)
    try:
        storage_service.put_bytes(thumb, analysis['thumbnail_png'], 'image/png')
        version.thumb_key = thumb
        version.thumb_status = DocumentVersion.ThumbStatus.READY
    except Exception:
        version.thumb_status = DocumentVersion.ThumbStatus.FAILED

    SectionVersion.objects.filter(document_version=version).update(
        search_vector=SearchVector('normalized_text', config='spanish_unaccent')
    )
    version.page_count = analysis['page_count']
    version.source_scenario = analysis['scenario']
    version.analysis_status = DocumentVersion.AnalysisStatus.READY
    version.error_detail = ''
    version.save()

    return {
        'scenario': analysis['scenario'],
        'degraded': analysis['degraded'],
        'page_count': analysis['page_count'],
        'sections': counters | {'total': len(analysis['sections'])},
    }
