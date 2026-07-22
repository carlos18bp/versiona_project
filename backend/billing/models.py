"""
Plans and limits (docs/plan/02 §3.7 — flow F1, invariant I13, DP-04).

Catalog stays static; plan STATE lives in two places with a fixed precedence
(billing.services.effective_plan): a non-free `Organization.plan` set by the
operator via console ALWAYS wins, then an active `Subscription` trial, then
free. Wompi checkout is DEFERRED until the operator provides keys
(docs/audit/02 §4). DP-04: hitting a limit NEVER deletes anything; old
history is LOCKED, not purged.
"""

from django.db import models

from core.models import PublicIdModel, TimestampedModel

PLANS = {
    'free': {
        'label': 'Gratis',
        'max_active_projects': 1,
        'max_members': 2,
        'history_days': 30,
        'price_cop': 0,
    },
    'pro': {
        'label': 'Pro',
        'max_active_projects': 20,
        'max_members': 25,
        'history_days': None,  # unlimited
        'price_cop': 149000,
    },
    'enterprise': {
        'label': 'Enterprise',
        'max_active_projects': None,  # unlimited
        'max_members': None,
        'history_days': None,
        'price_cop': None,  # contract pricing
    },
}

WARNING_THRESHOLD = 0.8  # F2: preventive warnings at 80%

TRIAL_PLAN_KEY = 'pro'


def plan_limits(plan_key: str) -> dict:
    return PLANS.get(plan_key, PLANS['free'])


class Subscription(PublicIdModel, TimestampedModel):
    """Time-boxed plan grant for one organization (today: the signup trial).

    A row here NEVER outranks a console override: `effective_plan` consults it
    only while `Organization.plan` is 'free'. To kill a running trial by hand:
    `subscription.status = 'expired'; subscription.save()`.
    """

    class Status(models.TextChoices):
        TRIALING = 'trialing', 'Trialing'
        EXPIRED = 'expired', 'Expired'

    organization = models.OneToOneField(
        'orgs.Organization', on_delete=models.CASCADE, related_name='subscription'
    )
    plan_key = models.CharField(max_length=20, default=TRIAL_PLAN_KEY)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.TRIALING
    )
    trial_ends_at = models.DateTimeField()
    trial_ending_notified_at = models.DateTimeField(null=True, blank=True)
    trial_expired_notified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.organization} · {self.plan_key} ({self.status})'
