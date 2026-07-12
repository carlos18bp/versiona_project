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
