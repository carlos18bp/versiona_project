"""Fake data follows Versiona business rules (It9 checklist): every fake user
gets a personal org + trial via the real signup path, and delete cleans the
domain without touching superusers."""

from datetime import timedelta
from io import StringIO

import pytest
from billing.models import Subscription
from django.core.management import CommandError, call_command
from django.utils import timezone
from freezegun import freeze_time
from orgs.models import Invitation, Organization, OrganizationMembership

from accounts.models import User


def run(command, *args, **options):
    out = StringIO()
    call_command(command, *args, stdout=out, **options)
    return out.getvalue()


@pytest.mark.django_db
@pytest.mark.escenario('FD-01')
def test_create_users_provisions_a_personal_org_with_trial():
    run('create_users', 2)

    users = User.objects.filter(is_superuser=False)
    assert users.count() == 2
    for user in users:
        membership = OrganizationMembership.objects.get(user=user)
        assert membership.role == OrganizationMembership.Role.OWNER
        subscription = Subscription.objects.get(organization=membership.organization)
        assert subscription.status == Subscription.Status.TRIALING


@pytest.mark.django_db
@pytest.mark.escenario('FD-02')
def test_create_users_never_creates_staff_accounts():
    run('create_users', 3)

    assert User.objects.filter(is_staff=True).count() == 0
    assert User.objects.filter(is_superuser=True).count() == 0


@pytest.mark.django_db
@pytest.mark.escenario('FD-03')
def test_delete_fake_data_requires_confirmation():
    with pytest.raises(CommandError):
        call_command('delete_fake_data')


@pytest.mark.django_db
@pytest.mark.escenario('FD-04')
def test_delete_fake_data_protects_superusers(django_user_model):
    django_user_model.objects.create_superuser(
        email='root@versiona.test', password='secreta123'
    )
    run('create_users', 2)

    run('delete_fake_data', confirm=True)

    assert User.objects.filter(is_superuser=True).count() == 1
    assert User.objects.filter(is_superuser=False).count() == 0


@pytest.mark.django_db
@pytest.mark.escenario('FD-05')
def test_delete_fake_data_removes_orphaned_orgs():
    run('create_users', 2)
    assert Organization.objects.count() == 2

    run('delete_fake_data', confirm=True)

    assert Organization.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.escenario('FD-06')
def test_delete_fake_data_keeps_orgs_with_remaining_members(django_user_model):
    root = django_user_model.objects.create_superuser(
        email='root@versiona.test', password='secreta123'
    )
    shared = Organization.objects.create(
        name='Compartida', slug='compartida', kind=Organization.Kind.TEAM
    )
    OrganizationMembership.objects.create(
        organization=shared, user=root, role=OrganizationMembership.Role.OWNER
    )
    run('create_users', 1)
    fake_user = User.objects.get(is_superuser=False)
    OrganizationMembership.objects.create(
        organization=shared, user=fake_user, role=OrganizationMembership.Role.MEMBER
    )

    run('delete_fake_data', confirm=True)

    assert Organization.objects.filter(slug='compartida').exists()


@pytest.mark.django_db
@pytest.mark.escenario('FD-08')
@freeze_time('2026-07-22 12:00:00')
def test_delete_fake_data_preserves_users_woven_into_protected_evidence():
    run('create_users', 2)
    inviter, other = User.objects.filter(is_superuser=False).order_by('pk')
    org = OrganizationMembership.objects.get(user=inviter).organization
    Invitation.objects.create(
        organization=org, email='externa@ejemplo.co', role='viewer',
        token='fd08-token', invited_by=inviter,
        expires_at=timezone.now() + timedelta(days=7),
    )

    run('delete_fake_data', confirm=True)

    assert User.objects.filter(pk=inviter.pk).exists()  # protected evidence
    assert not User.objects.filter(pk=other.pk).exists()


@pytest.mark.django_db
@pytest.mark.escenario('FD-07')
def test_e2e_scenario_reseed_is_idempotent():
    run('create_fake_data', scenario='e2e')
    first_users = User.objects.count()
    first_orgs = Organization.objects.count()

    run('create_fake_data', scenario='e2e')

    assert User.objects.count() == first_users
    assert Organization.objects.count() == first_orgs
    assert Organization.objects.filter(slug='acme-e2e', plan='enterprise').count() == 1
