"""The daily trial beat task: idempotent expiry + owner notices."""

from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone

from billing.models import Subscription
from billing.services import start_trial
from billing.tasks import expire_trials_and_notify
from notifications.models import Notification


@pytest.fixture
def trial_org(versiona_context):
    org = versiona_context.org
    org.plan = 'free'
    org.save(update_fields=['plan'])
    start_trial(org)
    mail.outbox.clear()
    return org


def _set_trial_end(org, delta):
    Subscription.objects.filter(organization=org).update(
        trial_ends_at=timezone.now() + delta
    )


@pytest.mark.django_db
@pytest.mark.escenario('F1-T05')
def test_beat_flips_expired_trials_to_expired(trial_org):
    _set_trial_end(trial_org, timedelta(days=-1))

    result = expire_trials_and_notify()

    subscription = Subscription.objects.get(organization=trial_org)
    assert subscription.status == Subscription.Status.EXPIRED
    assert result['expired'] == 1


@pytest.mark.django_db
@pytest.mark.escenario('F1-T05')
def test_beat_sends_the_expiry_notice_once(trial_org):
    _set_trial_end(trial_org, timedelta(days=-1))

    expire_trials_and_notify()
    expire_trials_and_notify()

    notices = Notification.objects.filter(event_key='billing.trial_ended')
    assert notices.count() == 1
    assert len(mail.outbox) == 1


@pytest.mark.django_db
@pytest.mark.escenario('F1-T06')
def test_beat_sends_the_t3_notice_inside_the_window(trial_org):
    _set_trial_end(trial_org, timedelta(days=2))

    result = expire_trials_and_notify()

    assert result['ending_notices'] == 1
    assert Notification.objects.filter(event_key='billing.trial_ending').count() == 1


@pytest.mark.django_db
@pytest.mark.escenario('F1-T06')
def test_beat_never_repeats_the_t3_notice(trial_org):
    _set_trial_end(trial_org, timedelta(days=2))

    expire_trials_and_notify()
    expire_trials_and_notify()

    assert Notification.objects.filter(event_key='billing.trial_ending').count() == 1


@pytest.mark.django_db
@pytest.mark.escenario('F1-T06')
def test_beat_ignores_trials_outside_the_t3_window(trial_org):
    _set_trial_end(trial_org, timedelta(days=10))

    result = expire_trials_and_notify()

    assert result['ending_notices'] == 0
    assert Notification.objects.filter(event_key='billing.trial_ending').count() == 0


@pytest.mark.django_db
@pytest.mark.escenario('F1-T07')
def test_beat_skips_notices_for_console_upgraded_orgs(trial_org):
    trial_org.plan = 'pro'
    trial_org.save(update_fields=['plan'])
    _set_trial_end(trial_org, timedelta(days=-1))

    expire_trials_and_notify()

    subscription = Subscription.objects.get(organization=trial_org)
    assert subscription.status == Subscription.Status.EXPIRED
    assert Notification.objects.filter(event_key='billing.trial_ended').count() == 0
