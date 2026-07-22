"""Anonymous public comparator endpoints (AllowAny + strict per-IP throttles).

Note the throttle classes subclass SimpleRateThrottle directly: DRF's
ScopedRateThrottle reads `view.throttle_scope`, an attribute @api_view FBVs
never carry, which silently disables it.
"""

from django.utils import timezone
from rest_framework.decorators import (
    api_view,
    parser_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle

from .models import PublicComparison
from .services.public_comparison_service import (
    PublicCompareError,
    create_public_comparison,
)


class _IpRateThrottle(SimpleRateThrottle):
    def get_cache_key(self, request, view):
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request),
        }


class PublicCompareThrottle(_IpRateThrottle):
    scope = 'public_compare'


class PublicCompareDailyThrottle(_IpRateThrottle):
    scope = 'public_compare_daily'


class PublicCompareStatusThrottle(_IpRateThrottle):
    scope = 'public_compare_status'


def _payload(comparison: PublicComparison) -> dict:
    return {
        'public_id': str(comparison.public_id),
        'status': comparison.status,
        'error_code': comparison.error_code,
        'file_a_name': comparison.file_a_name,
        'file_b_name': comparison.file_b_name,
        'created_at': comparison.created_at,
        'expires_at': comparison.expires_at,
        'result': comparison.result,
    }


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PublicCompareThrottle, PublicCompareDailyThrottle])
@parser_classes([MultiPartParser])
def create_comparison(request):
    try:
        comparison = create_public_comparison(
            request.FILES.get('file_a'),
            request.FILES.get('file_b'),
            request.META.get('REMOTE_ADDR', ''),
        )
    except PublicCompareError as exc:
        return Response(
            {'error': str(exc), 'error_code': exc.error_code},
            status=exc.status_code,
        )
    return Response(
        {
            'public_id': str(comparison.public_id),
            'status': comparison.status,
            'status_url': f'/api/public/comparisons/{comparison.public_id}/',
        },
        status=202,
    )


@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([PublicCompareStatusThrottle])
def comparison_detail(request, pub):
    try:
        comparison = PublicComparison.objects.get(public_id=pub)
    except PublicComparison.DoesNotExist:
        return Response({'error_code': 'not_found'}, status=404)
    if comparison.expires_at < timezone.now():
        return Response({'error_code': 'expired'}, status=410)
    return Response(_payload(comparison))
