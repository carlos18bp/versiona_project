"""F1 limit enforcement + F2 usage (I13, DP-04: lock, never delete)."""

from django.utils import timezone

from documents.services.version_service import DomainError

from .models import WARNING_THRESHOLD, plan_limits

UPGRADE_CTA = (
    'Tu plan {label} llegó a su límite de {what}. Mejora tu plan para seguir '
    'creciendo — el pago en línea llega pronto; escríbenos mientras tanto.'
)


def _usage(org) -> dict:
    from orgs.models import OrganizationMembership

    limits = plan_limits(org.plan)
    active_projects = org.projects.filter(status='active').count()
    members = OrganizationMembership.objects.filter(organization=org).count()
    return {
        'plan': org.plan,
        'plan_label': limits['label'],
        'limits': {
            'max_active_projects': limits['max_active_projects'],
            'max_members': limits['max_members'],
            'history_days': limits['history_days'],
        },
        'usage': {'active_projects': active_projects, 'members': members},
    }


def usage_report(org) -> dict:
    """F2: usage vs limits with preventive warnings at 80%."""
    report = _usage(org)
    warnings = []
    for key, used in (
        ('max_active_projects', report['usage']['active_projects']),
        ('max_members', report['usage']['members']),
    ):
        limit = report['limits'][key]
        if limit and used / limit >= WARNING_THRESHOLD:
            warnings.append({
                'limit': key,
                'used': used,
                'max': limit,
                'at_capacity': used >= limit,
            })
    report['warnings'] = warnings
    report['upgrade_available'] = org.plan == 'free'
    return report


def check_project_limit(org):
    """Raised BEFORE creating a project (F1-L01)."""
    report = _usage(org)
    limit = report['limits']['max_active_projects']
    if limit and report['usage']['active_projects'] >= limit:
        raise DomainError(
            UPGRADE_CTA.format(label=report['plan_label'],
                               what=f'{limit} proyecto(s) activo(s)'),
            402,
        )


def check_member_limit(org):
    """Raised BEFORE inviting / accepting a NEW member (F1-L02)."""
    report = _usage(org)
    limit = report['limits']['max_members']
    if limit and report['usage']['members'] >= limit:
        raise DomainError(
            UPGRADE_CTA.format(label=report['plan_label'],
                               what=f'{limit} miembro(s)'),
            402,
        )


def check_history_access(version):
    """DP-04 / C3-L02: on the free plan, versions older than the window are
    LOCKED (never deleted) — except each document's latest version."""
    org = version.document.project.organization
    limits = plan_limits(org.plan)
    window = limits['history_days']
    if window is None:
        return
    if version.number == version.document.latest_number:
        return
    age = timezone.now() - version.created_at
    if age.days >= window:
        raise DomainError(
            f'El historial de más de {window} días está bloqueado en el plan '
            f'{limits["label"]} (la versión sigue guardada, nada se borra). '
            'Mejora tu plan para acceder.',
            402,
        )
