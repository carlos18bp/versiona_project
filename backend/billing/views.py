"""Public plan catalog (F1) — feeds the /precios marketing page."""

from django.conf import settings
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .models import PLANS


class PublicPlansThrottle(AnonRateThrottle):
    # AnonRateThrottle resolves its rate from the class-level scope, which
    # works on FBVs (ScopedRateThrottle does NOT — it reads a view attribute
    # @api_view never sets).
    scope = 'public'


@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([PublicPlansThrottle])
def public_plans(request):
    """Stable, additive-only contract. Order fixed: free → pro → enterprise.
    `null` limit = unlimited; `null` price = contract pricing."""
    plans = [
        {
            'key': key,
            'label': plan['label'],
            'price_cop': plan['price_cop'],
            'limits': {
                'max_active_projects': plan['max_active_projects'],
                'max_members': plan['max_members'],
                'history_days': plan['history_days'],
            },
        }
        for key, plan in PLANS.items()
    ]
    return Response({'trial_days': settings.BILLING_TRIAL_DAYS, 'plans': plans})
