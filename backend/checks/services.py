"""E3 check engine: evaluates the PINNED config's checklist (I8) against the
version's sections, with evidence pointing at the exact spot."""

import re

from django.db import transaction
from django.utils import timezone

from documents.models import DocumentVersion, SectionVersion

from .models import CheckResult, CheckRun


def _sections(version: DocumentVersion) -> list:
    return list(
        SectionVersion.objects.filter(document_version=version)
        .select_related('section')
        .order_by('order_index')
    )


def _evaluate(item: dict, sections: list) -> tuple[str, dict, str]:
    """(outcome, evidence, message) for one checklist item."""
    check_type = item['type']
    param = item['param']
    violation = 'warn' if item.get('severity', 'fail') == 'warn' else 'fail'

    if check_type == 'required_section':
        for snap in sections:
            if snap.section.stable_key == param:
                return ('pass',
                        {'section': param, 'page': snap.page_start},
                        f'La sección "{snap.heading_text}" está presente.')
        return (violation, {'reason': 'section_missing', 'expected': param},
                f'Falta la sección requerida "{param}".')

    try:
        pattern = re.compile(param, re.IGNORECASE)
    except re.error:
        return ('fail', {'reason': 'invalid_pattern', 'param': param},
                f'Patrón inválido: {param}')

    for snap in sections:
        match = pattern.search(snap.normalized_text)
        if match:
            start = max(0, match.start() - 40)
            snippet = snap.normalized_text[start:match.end() + 40].strip()
            evidence = {
                'section': snap.section.stable_key,
                'page': snap.page_start,
                'snippet': snippet,
            }
            if check_type == 'required_text':
                return ('pass', evidence, 'Texto requerido encontrado.')
            return (violation, evidence,
                    f'Texto prohibido encontrado en "{snap.heading_text}".')

    if check_type == 'required_text':
        return (violation, {'reason': 'text_missing', 'pattern': param},
                'El texto requerido no aparece en el documento.')
    return ('pass', {}, 'El texto prohibido no aparece.')


@transaction.atomic
def run_checks(version: DocumentVersion) -> CheckRun | None:
    """Idempotent per version+config (I15): a completed run is returned as-is."""
    config = version.config_version
    if not config.checklist:
        return None
    existing = CheckRun.objects.filter(
        document_version=version, config_version=config, status=CheckRun.Status.DONE
    ).first()
    if existing:
        return existing

    run = CheckRun.objects.create(document_version=version, config_version=config)
    sections = _sections(version)
    CheckResult.objects.bulk_create([
        CheckResult(
            check_run=run,
            key=item['key'],
            label=item['label'],
            outcome=outcome,
            evidence=evidence,
            message=message,
        )
        for item in config.checklist
        for outcome, evidence, message in [_evaluate(item, sections)]
    ])
    run.finished_at = timezone.now()
    run.save(update_fields=['finished_at', 'updated_at'])
    return run


def summary_for(version: DocumentVersion) -> dict | None:
    """{pass, warn, fail} of the latest run — the timeline traffic light."""
    run = (
        CheckRun.objects.filter(document_version=version, status=CheckRun.Status.DONE)
        .order_by('-created_at')
        .prefetch_related('results')
        .first()
    )
    if run is None:
        return None
    counters = {'pass': 0, 'warn': 0, 'fail': 0}
    for result in run.results.all():
        counters[result.outcome] += 1
    return counters
