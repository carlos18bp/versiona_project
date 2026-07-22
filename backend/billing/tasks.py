"""Daily trial maintenance (F1): expiry bookkeeping + owner notices.

Correctness never depends on this task: `effective_plan` evaluates
`trial_ends_at` lazily at read time. This task only materializes the status
flip and sends each notice exactly once (the `*_notified_at` stamps are the
idempotency guards).
"""

from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .models import Subscription


def _notify_owners(org, event_key: str, context: dict) -> None:
    from notifications.services import notify
    from orgs.models import OrganizationMembership

    owners = OrganizationMembership.objects.filter(
        organization=org,
        role=OrganizationMembership.Role.OWNER,
        is_active=True,
    ).select_related('user')
    for membership in owners:
        notify(
            user=membership.user,
            event_key=event_key,
            org=org,
            context=context,
            link='/org/usage',
        )


@shared_task(name='billing.tasks.expire_trials_and_notify')
def expire_trials_and_notify() -> dict:
    now = timezone.now()
    ending_notices = 0
    expired = 0

    ending = Subscription.objects.filter(
        status=Subscription.Status.TRIALING,
        trial_ending_notified_at__isnull=True,
        trial_ends_at__gt=now,
        trial_ends_at__lte=now + timedelta(days=3),
        organization__plan='free',  # a console-upgraded org keeps its plan
    ).select_related('organization')
    for subscription in ending:
        with transaction.atomic():
            org = subscription.organization
            days = (subscription.trial_ends_at.date() - now.date()).days
            _notify_owners(org, 'billing.trial_ending', {
                'org': org.name,
                'days': days,
                'date': subscription.trial_ends_at.date().isoformat(),
            })
            subscription.trial_ending_notified_at = now
            subscription.save(update_fields=['trial_ending_notified_at'])
            ending_notices += 1

    over = Subscription.objects.filter(
        status=Subscription.Status.TRIALING,
        trial_ends_at__lte=now,
    ).select_related('organization')
    for subscription in over:
        with transaction.atomic():
            org = subscription.organization
            subscription.status = Subscription.Status.EXPIRED
            update_fields = ['status']
            if org.plan == 'free' and subscription.trial_expired_notified_at is None:
                _notify_owners(org, 'billing.trial_ended', {'org': org.name})
                subscription.trial_expired_notified_at = now
                update_fields.append('trial_expired_notified_at')
            subscription.save(update_fields=update_fields)
            expired += 1

    return {'expired': expired, 'ending_notices': ending_notices}
