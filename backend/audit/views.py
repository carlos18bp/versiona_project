"""Project activity feed (kit 6 — reuses AuditEvent, docs/audit/02 G27).

Whitelisted event types only, serialized WITHOUT ip/request_id: the feed is
product surface, the full log is an org-admin tool (F3, It7)."""

from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination

from core.permissions import require_project_role

from .models import AuditEvent

ACTIVITY_WHITELIST = [
    'version.uploaded', 'version.approved', 'version.message_edited',
    'document.created', 'document.trashed', 'document.restored',
    'version.trashed', 'version.restored', 'version.downloaded',
    'comparison.created',
    'seal.created', 'seal.revoked', 'seal.preserved', 'seal.invalidated',
    'seal_plan.confirmed_preserved', 'seal_plan.confirmed_invalidated',
    'review.requested', 'review.cancelled',
    'observation.created', 'observation.answered', 'observation.resolved',
    'observation.open',
    'project.updated', 'project.archived', 'project.unarchived',
]


@api_view(['GET'])
@require_project_role('viewer')
def project_activity(request, proj):
    queryset = AuditEvent.objects.filter(
        project_id_ref=request.project.pk,
        event_type__in=ACTIVITY_WHITELIST,
    ).select_related('actor').order_by('-created_at')
    event_filter = request.query_params.get('type')
    if event_filter:
        queryset = queryset.filter(event_type=event_filter)
    # Kit 4: activity by date range
    date_from = request.query_params.get('from')
    date_to = request.query_params.get('to')
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)

    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(queryset, request)
    return paginator.get_paginated_response([
        {
            'event_type': event.event_type,
            'actor_email': event.actor.email if event.actor else None,
            'payload': event.payload,
            'created_at': event.created_at,
        }
        for event in page
    ])


@api_view(['GET'])
def org_audit(request, org):
    """F3 base: the FULL org audit log (org owner/admin only) with filters and
    CSV export — this one includes actor emails but still no raw IPs in CSV."""
    import csv

    from django.http import Http404, HttpResponse

    from core.permissions import resolve_org_role
    from orgs.models import Organization

    organization = Organization.objects.filter(public_id=org).first()
    if organization is None:
        raise Http404
    if resolve_org_role(request.user, organization) not in ('owner', 'admin'):
        raise Http404

    queryset = AuditEvent.objects.filter(org_id_ref=organization.pk).select_related(
        'actor'
    ).order_by('-created_at')
    event_filter = request.query_params.get('type')
    if event_filter:
        queryset = queryset.filter(event_type=event_filter)
    actor = request.query_params.get('actor')
    if actor:
        queryset = queryset.filter(actor__email__icontains=actor)
    date_from = request.query_params.get('from')
    date_to = request.query_params.get('to')
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)

    if request.query_params.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="audit.csv"'
        writer = csv.writer(response)
        writer.writerow(['fecha', 'evento', 'actor', 'payload'])
        for event in queryset[:5000]:
            writer.writerow([
                event.created_at.isoformat(),
                event.event_type,
                event.actor.email if event.actor else '',
                str(event.payload),
            ])
        return response

    from rest_framework.pagination import PageNumberPagination

    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(queryset, request)
    return paginator.get_paginated_response([
        {
            'event_type': event.event_type,
            'actor_email': event.actor.email if event.actor else None,
            'payload': event.payload,
            'created_at': event.created_at,
        }
        for event in page
    ])
