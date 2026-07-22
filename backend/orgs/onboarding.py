"""
A1 — the wow moment (docs/plan/01 A1, success metric S1: value in <5 min).

The wizard renames the personal org and seeds a SAMPLE project with the two
contract fixtures, so the very first thing a new user sees is a working
comparison — without uploading anything. The seed is idempotent per org.
"""

from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.utils.text import slugify

from audit import services as audit
from orgs.models import Organization

SAMPLE_SLUG = 'proyecto-de-ejemplo'
FIXTURES = Path(settings.BASE_DIR).parent / 'testdata' / 'pdfs'


def onboarding_state(user) -> dict:
    """Where the wizard stands for this user's personal org."""
    org = (
        Organization.objects.filter(
            memberships__user=user, kind=Organization.Kind.PERSONAL
        ).first()
        or Organization.objects.filter(memberships__user=user).first()
    )
    if org is None:
        return {'status': 'no_org'}
    sample = org.projects.filter(slug=SAMPLE_SLUG).first()
    if sample is None:
        return {'status': 'pending', 'org': str(org.public_id), 'org_name': org.name}
    wow = _wow_link(sample)
    return {
        'status': 'done',
        'org': str(org.public_id),
        'org_name': org.name,
        'project': str(sample.public_id),
        'wow_link': wow,
    }


def _wow_link(project) -> str | None:
    document = project.documents.order_by('created_at').first()
    if document is None:
        return None
    versions = {v.number: v for v in document.versions.all()}
    if 1 in versions and 2 in versions:
        return (f'/projects/{project.public_id}/documents/{document.public_id}'
                f'/compare/{versions[1].public_id}/{versions[2].public_id}')
    return f'/projects/{project.public_id}/documents/{document.public_id}'


@transaction.atomic
def complete_onboarding(user, org_name: str, request=None) -> dict:
    """Rename the personal org and seed the sample project (idempotent)."""
    from documents.services import storage_service, version_service
    from documents.services.version_service import DomainError
    from projects.models import Project, ProjectMembership

    org = Organization.objects.filter(
        memberships__user=user, kind=Organization.Kind.PERSONAL
    ).first()
    if org is None:
        raise DomainError('No tienes una organización personal.', 409)

    org_name = (org_name or '').strip()
    if org_name and org.name != org_name:
        org.name = org_name
        base = slugify(org_name)[:140] or org.slug
        slug = base
        suffix = 1
        while Organization.objects.exclude(pk=org.pk).filter(slug=slug).exists():
            suffix += 1
            slug = f'{base}-{suffix}'
        org.slug = slug
        org.save(update_fields=['name', 'slug', 'updated_at'])

    sample = org.projects.filter(slug=SAMPLE_SLUG).first()
    if sample is None:
        sample = Project.objects.create(
            organization=org,
            name='Proyecto de ejemplo',
            slug=SAMPLE_SLUG,
            description='Un contrato con dos versiones para que veas la comparación '
                        'y los sellos en acción. Puedes borrarlo cuando quieras.',
            is_sample=True,
        )
        ProjectMembership.objects.get_or_create(
            project=sample, user=user,
            defaults={'role': ProjectMembership.Role.ADMIN},
        )
        document = version_service.create_document(sample, 'Contrato de obra (ejemplo)', user)
        for fixture, message in (
            ('contrato_v1.pdf', 'Primera entrega del contratista'),
            ('contrato_v2.pdf', 'Atiende observaciones: sube la multa al 5%'),
        ):
            intent = version_service.create_upload_intent(document, user)
            storage_service.put_bytes(
                intent.key, (FIXTURES / fixture).read_bytes(), 'application/pdf'
            )
            version_service.complete_upload(document, intent.upload_id, message, user)

        audit.record(
            org=org, project=sample, actor=user,
            event_type='onboarding.sample_seeded', obj=sample,
            payload={'org_name': org.name}, request=request,
        )

    return onboarding_state(user)
