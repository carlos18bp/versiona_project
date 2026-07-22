"""Checklist templates (org, kit 2) + per-version check results (E3)."""

from django.http import Http404
from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.permissions import require_org_role, require_project_role
from documents.services.version_service import DomainError
from projects.services.config_service import validate_checklist

from .models import ChecklistTemplate, CheckRun
from .services import summary_for


class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistTemplate
        fields = ('public_id', 'name', 'items', 'created_at')


@api_view(['GET', 'POST'])
@require_org_role('member')
def org_checklist_templates(request, org):
    if request.method == 'GET':
        templates = ChecklistTemplate.objects.filter(organization=request.org)
        return Response({'results': TemplateSerializer(templates, many=True).data})

    if request.org_role not in ('owner', 'admin'):
        raise Http404
    payload = request.data or {}
    name = (payload.get('name') or '').strip()
    if not name:
        return Response({'error': 'La plantilla necesita un nombre.'}, status=400)
    try:
        items = validate_checklist(payload.get('items') or [])
    except DomainError as exc:
        return Response({'error': str(exc)}, status=exc.status_code)
    if ChecklistTemplate.objects.filter(organization=request.org, name=name).exists():
        return Response({'error': f'Ya existe una plantilla "{name}".'}, status=409)
    template = ChecklistTemplate.objects.create(
        organization=request.org, name=name, items=items, created_by=request.user
    )
    return Response(TemplateSerializer(template).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@require_project_role('viewer')
def version_checks(request, ver):
    """Latest check run with evidence (E3) + the traffic-light summary."""
    version = request.resolved_object
    run = (
        CheckRun.objects.filter(document_version=version, status=CheckRun.Status.DONE)
        .order_by('-created_at')
        .prefetch_related('results')
        .first()
    )
    if run is None:
        return Response({'summary': None, 'results': [],
                         'config_version': version.config_version.number})
    return Response({
        'summary': summary_for(version),
        'config_version': run.config_version.number,
        'results': [
            {
                'key': result.key,
                'label': result.label,
                'outcome': result.outcome,
                'evidence': result.evidence,
                'message': result.message,
            }
            for result in run.results.all()
        ],
    })
