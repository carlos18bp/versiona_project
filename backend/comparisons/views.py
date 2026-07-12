"""Comparison endpoints (flow E1 — docs/plan/03 §3)."""

from django.http import Http404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.permissions import require_project_role, resolve_effective_role
from documents.models import Document, DocumentVersion
from documents.services.version_service import DomainError

from .models import Comparison
from .serializers import (
    ComparisonCreateSerializer,
    ComparisonDetailSerializer,
    SectionDiffDetailSerializer,
)
from .services import build_comparison, validate_pair


@api_view(['GET', 'POST'])
@require_project_role('viewer')
def document_comparisons(request, doc):
    document: Document = request.resolved_object

    if request.method == 'GET':
        queryset = Comparison.objects.filter(document=document).select_related(
            'from_version', 'to_version'
        )[:25]
        return Response(
            {'results': ComparisonDetailSerializer(queryset, many=True).data}
        )

    serializer = ComparisonCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    versions = {
        str(version.public_id): version
        for version in DocumentVersion.objects.filter(
            document=document,
            public_id__in=[
                serializer.validated_data['from_version'],
                serializer.validated_data['to_version'],
            ],
        )
    }
    from_version = versions.get(str(serializer.validated_data['from_version']))
    to_version = versions.get(str(serializer.validated_data['to_version']))
    if from_version is None or to_version is None:
        raise Http404

    try:
        # Guards first: a stale cache is never served for an uncomparable pair.
        validate_pair(document, from_version, to_version)
        existing = Comparison.objects.filter(
            from_version=from_version, to_version=to_version, status=Comparison.Status.DONE
        ).first()
        comparison = existing or build_comparison(
            document, from_version, to_version, request.user, request=request
        )
    except DomainError as exc:
        return Response({'error': str(exc)}, status=exc.status_code)

    return Response(
        ComparisonDetailSerializer(comparison).data,
        # 200 = served from cache; 201 = freshly computed (docs/plan/03 §3).
        status=status.HTTP_200_OK if existing else status.HTTP_201_CREATED,
    )


def _load_comparison(request, cmp_id):
    comparison = (
        Comparison.objects.filter(public_id=cmp_id)
        .select_related('document__project__organization', 'from_version', 'to_version')
        .first()
    )
    if comparison is None:
        raise Http404
    project = comparison.document.project
    role = resolve_effective_role(request.user, project)
    if role is None:
        raise Http404
    return comparison


@api_view(['GET'])
def comparison_detail(request, cmp):
    comparison = _load_comparison(request, cmp)
    return Response(ComparisonDetailSerializer(comparison).data)


@api_view(['GET'])
def comparison_section_diff(request, cmp, sec):
    comparison = _load_comparison(request, cmp)
    diff = comparison.diffs.filter(stable_key=sec).first()
    if diff is None:
        raise Http404
    return Response(SectionDiffDetailSerializer(diff).data)
