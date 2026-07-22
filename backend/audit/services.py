"""`audit.services.record` — called by every domain service (docs/plan/08 §4)."""

from .models import AuditEvent


def record(*, org, event_type, actor=None, project=None, obj=None, payload=None, request=None):
    ip = None
    request_id = ''
    if request is not None:
        ip = request.META.get('REMOTE_ADDR')
        request_id = request.META.get('HTTP_X_REQUEST_ID', '')[:64]

    return AuditEvent.objects.create(
        org_id_ref=org.pk,
        project_id_ref=project.pk if project is not None else None,
        actor=actor if getattr(actor, 'is_authenticated', False) else None,
        event_type=event_type,
        object_type=type(obj).__name__ if obj is not None else '',
        object_id_ref=str(getattr(obj, 'public_id', getattr(obj, 'pk', ''))) if obj is not None else '',
        payload=payload or {},
        ip=ip,
        request_id=request_id,
    )
