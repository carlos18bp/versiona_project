"""
Plans and limits (docs/plan/02 §3.7 — flow F1, invariant I13, DP-04).

MVP: a static plan catalog + `Organization.plan`. Wompi checkout is DEFERRED
until the operator provides sandbox keys (docs/audit/02 §4) — the upgrade CTA
is informative. DP-04: hitting a limit NEVER deletes anything; old history is
LOCKED, not purged.
"""

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


def plan_limits(plan_key: str) -> dict:
    return PLANS.get(plan_key, PLANS['free'])
