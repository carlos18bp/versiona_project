"""F1 trial: signup grant, lazy effective plan and console-override precedence."""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from unittest.mock import patch

from billing.models import Subscription
from billing.services import (
    check_history_access,
    check_project_limit,
    effective_plan,
    start_trial,
    usage_report,
)
from documents.services.version_service import DomainError
from orgs.services import ensure_personal_org


@pytest.fixture
def free_org(versiona_context):
    org = versiona_context.org
    org.plan = 'free'
    org.save(update_fields=['plan'])
    return org


@pytest.mark.django_db
@pytest.mark.escenario('F1-T01')
@patch('accounts.views.auth.verify_recaptcha', return_value=True)
def test_signup_starts_a_pro_trial_on_the_new_personal_org(mock_captcha, api_client):
    api_client.post(
        reverse('sign_up'),
        {'email': 'nueva@versiona.test', 'password': 'pass1234'},
        format='json',
    )

    subscription = Subscription.objects.get(
        organization__memberships__user__email='nueva@versiona.test'
    )
    assert subscription.status == Subscription.Status.TRIALING
    assert subscription.plan_key == 'pro'
    assert subscription.trial_ends_at > timezone.now() + timedelta(days=13)


@pytest.mark.django_db
@pytest.mark.escenario('F1-T01')
def test_ensure_personal_org_keeps_a_single_trial_on_relogin(django_user_model):
    user = django_user_model.objects.create_user(
        email='relogin@versiona.test', password='secreta123'
    )

    first = ensure_personal_org(user)
    second = ensure_personal_org(user)

    assert first == second
    assert Subscription.objects.filter(organization=first).count() == 1


@pytest.mark.django_db
@pytest.mark.escenario('F1-T02')
def test_org_without_subscription_stays_on_its_stored_plan(free_org):
    assert effective_plan(free_org) == 'free'


@pytest.mark.django_db
@pytest.mark.escenario('F1-T02')
def test_effective_plan_is_pro_while_the_trial_runs(free_org):
    start_trial(free_org)

    assert effective_plan(free_org) == 'pro'


@pytest.mark.django_db
@pytest.mark.escenario('F1-T02')
def test_effective_plan_falls_back_to_free_after_expiry_without_beat(free_org):
    start_trial(free_org)

    with freeze_time(timezone.now() + timedelta(days=15)):
        assert effective_plan(free_org) == 'free'


@pytest.mark.django_db
@pytest.mark.escenario('F1-T03')
def test_console_override_pro_wins_over_an_expired_trial(free_org):
    subscription = start_trial(free_org)
    subscription.trial_ends_at = timezone.now() - timedelta(days=1)
    subscription.save(update_fields=['trial_ends_at'])
    free_org.plan = 'pro'
    free_org.save(update_fields=['plan'])

    assert effective_plan(free_org) == 'pro'


@pytest.mark.django_db
@pytest.mark.escenario('F1-T03')
def test_console_override_enterprise_wins_over_an_active_trial(free_org):
    start_trial(free_org)
    free_org.plan = 'enterprise'
    free_org.save(update_fields=['plan'])

    assert effective_plan(free_org) == 'enterprise'


@pytest.mark.django_db
@pytest.mark.escenario('F1-T04')
def test_trial_lifts_the_free_project_limit(free_org):
    start_trial(free_org)

    check_project_limit(free_org)  # 1 active project < pro's 20 — no exception


@pytest.mark.django_db
@pytest.mark.escenario('F1-T04')
def test_expired_trial_restores_the_free_project_limit(free_org):
    start_trial(free_org)

    with freeze_time(timezone.now() + timedelta(days=15)):
        with pytest.raises(DomainError) as exc:
            check_project_limit(free_org)

    assert exc.value.status_code == 402


@pytest.mark.django_db
@pytest.mark.escenario('F1-T04')
def test_trial_lifts_the_member_limit_for_invitations(free_org, versiona_context):
    from orgs.invitations import create_invitation

    start_trial(free_org)

    create_invitation(
        versiona_context.project, versiona_context.users['admin'],
        email='octava@externa.co', role='viewer',
    )  # 7 members < pro's 25 — no exception


@pytest.mark.django_db
@pytest.mark.escenario('F1-T04')
def test_trial_unlocks_history_older_than_thirty_days(free_org, document_with_versions):
    from documents.models import DocumentVersion

    document, versions = document_with_versions(n_versions=2)
    DocumentVersion.all_objects.filter(pk=versions[0].pk).update(
        created_at=timezone.now() - timedelta(days=45)
    )
    start_trial(free_org)

    check_history_access(DocumentVersion.objects.get(pk=versions[0].pk))


@pytest.mark.django_db
@pytest.mark.escenario('F2-T01')
def test_usage_report_carries_the_trial_block(free_org):
    start_trial(free_org)

    report = usage_report(free_org)

    assert report['plan'] == 'pro'
    assert report['effective_plan'] == 'pro'
    assert report['trial']['on_trial'] is True
    assert report['trial']['days_left'] == 14
    assert report['upgrade_available'] is True


@pytest.mark.django_db
@pytest.mark.escenario('F2-T01')
def test_usage_report_after_expiry_offers_the_upgrade(free_org):
    start_trial(free_org)

    with freeze_time(timezone.now() + timedelta(days=15)):
        report = usage_report(free_org)

    assert report['plan'] == 'free'
    assert report['trial']['on_trial'] is False
    assert report['upgrade_available'] is True
