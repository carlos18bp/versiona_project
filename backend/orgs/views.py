"""Org endpoints (It1 slice: my orgs + unified trash — docs/plan/03 §3)."""

from itertools import chain

from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.permissions import require_org_role

from .models import OrganizationMembership


@api_view(['GET'])
def my_orgs(request):
    memberships = (
        OrganizationMembership.objects.filter(user=request.user, is_active=True)
        .select_related('organization')
        .order_by('organization__name')
    )
    return Response({
        'results': [
            {
                'public_id': str(m.organization.public_id),
                'name': m.organization.name,
                'slug': m.organization.slug,
                'kind': m.organization.kind,
                'role': m.role,
            }
            for m in memberships
        ]
    })


@api_view(['GET'])
@require_org_role('admin')
def org_trash(request, org):
    """Unified trash list (kit 3 — B4/C4): projects, documents, draft versions."""
    from documents.models import Document, DocumentVersion
    from projects.models import Project
    from projects.serializers import TrashItemSerializer

    projects = Project.all_objects.trashed().filter(organization=request.org)
    documents = Document.all_objects.trashed().filter(
        project__organization=request.org, project__deleted_at__isnull=True
    ).select_related('project')
    versions = DocumentVersion.all_objects.trashed().filter(
        document__project__organization=request.org,
        document__deleted_at__isnull=True,
        document__project__deleted_at__isnull=True,
    ).select_related('document__project')

    def item(obj, type_name, name, context):
        return {
            'type': type_name,
            'public_id': obj.public_id,
            'name': name,
            'context': context,
            'deleted_at': obj.deleted_at,
            'deleted_by': obj.deleted_by.email if obj.deleted_by else None,
            'purge_after': obj.purge_after,
        }

    items = list(chain(
        (item(p, 'project', p.name, p.organization.name) for p in projects),
        (item(d, 'document', d.title, d.project.name) for d in documents),
        (item(v, 'version', f'{v.document.title} · v{v.number}', v.document.project.name)
         for v in versions),
    ))
    items.sort(key=lambda entry: entry['deleted_at'], reverse=True)
    return Response({'results': TrashItemSerializer(items, many=True).data})
