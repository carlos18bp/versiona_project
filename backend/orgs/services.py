"""Organization services (flows A1/A2)."""

from django.db import transaction

from .models import Organization, OrganizationMembership


@transaction.atomic
def ensure_personal_org(user) -> Organization:
    """Every user owns a personal organization from sign-up on (A1).

    Idempotent: returns the first org the user OWNS, creating the personal one
    only when none exists (safe for google_login get_or_create re-logins).
    """
    membership = (
        OrganizationMembership.objects.filter(
            user=user, role=OrganizationMembership.Role.OWNER, is_active=True
        )
        .select_related('organization')
        .first()
    )
    if membership:
        return membership.organization

    display = (user.first_name or user.email.split('@')[0]).strip() or 'personal'
    org = Organization.objects.create(
        name=f'{display} (personal)',
        slug=Organization.build_unique_slug(f'{display}-personal'),
        kind=Organization.Kind.PERSONAL,
    )
    OrganizationMembership.objects.create(
        organization=org, user=user, role=OrganizationMembership.Role.OWNER
    )
    from billing.services import start_trial  # local import, as in invitations

    start_trial(org)
    return org
