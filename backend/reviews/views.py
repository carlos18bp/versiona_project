"""Seal endpoints (D4) + seal plan (D5 coordinator) — docs/plan/03 §3."""

from django.http import Http404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.permissions import require_project_role
from documents.services.version_service import DomainError

from .models import Seal, SealValidityRecord
from .serializers import (
    SealCreateSerializer,
    SealPlanConfirmSerializer,
    SealSerializer,
    SealValidityRecordSerializer,
)
from .services import seal_service, signing


@api_view(['GET', 'POST'])
@require_project_role('viewer')
def version_seals(request, ver):
    """GET: seals + their validity records for this version. POST (reviewer+):
    place a seal over sections or the whole document."""
    version = request.resolved_object

    if request.method == 'GET':
        seals = (
            Seal.objects.filter(document_version=version)
            .select_related('reviewer')
            .prefetch_related('covered_sections__section')
        )
        incoming = (
            SealValidityRecord.objects.filter(to_document_version=version)
            .select_related('seal__reviewer', 'seal__document_version', 'decided_by')
            .prefetch_related('seal__covered_sections__section')
        )
        return Response({
            'seals': SealSerializer(seals, many=True).data,
            'validity_records': SealValidityRecordSerializer(incoming, many=True).data,
        })

    if request.effective_role not in ('reviewer', 'admin'):
        raise Http404  # I12: outsiders and viewers see no write surface

    serializer = SealCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        seal = seal_service.create_seal(
            version,
            request.user,
            covers_all=serializer.validated_data['covers_all'],
            section_keys=serializer.validated_data['section_keys'],
            request=request,
        )
    except DomainError as exc:
        return Response({'error': str(exc)}, status=exc.status_code)
    return Response(SealSerializer(seal).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@require_project_role('reviewer')
def seal_revoke(request, ver, seal_id):
    version = request.resolved_object
    seal = Seal.objects.filter(document_version=version, public_id=seal_id).first()
    if seal is None:
        raise Http404
    try:
        seal_service.revoke_seal(seal, request.user, request=request)
    except DomainError as exc:
        return Response({'error': str(exc)}, status=exc.status_code)
    return Response(SealSerializer(seal).data)


@api_view(['GET'])
@require_project_role('viewer')
def seal_verify(request, ver, seal_id):
    """Re-verifies the Ed25519 signature server-side and returns everything a
    third party needs to verify it OFFLINE (payload, signature, public key)."""
    version = request.resolved_object
    seal = Seal.objects.filter(document_version=version, public_id=seal_id).first()
    if seal is None:
        raise Http404
    valid = signing.verify(seal.signed_payload, seal.signature)
    return Response({
        'signature_valid': valid,
        'binds_version_sha256': seal.signed_payload.get('version_sha256') == version.sha256,
        'payload': seal.signed_payload,
        'signature': seal.signature,
        'key_id': seal.key_id,
        'public_key': signing.public_key_b64(),
        'algorithm': 'Ed25519',
    })


@api_view(['GET', 'POST'])
@require_project_role('viewer')
def version_seal_plan(request, ver):
    """D5 coordinator mode: GET lists pending records; POST (admin — the
    `can_confirm_seal_plan` capability, DP-07) confirms the plan."""
    version = request.resolved_object
    if request.method == 'GET':
        pending = (
            SealValidityRecord.objects.filter(
                to_document_version=version,
                decision=SealValidityRecord.Decision.PENDING,
            )
            .select_related('seal__reviewer', 'seal__document_version')
            .prefetch_related('seal__covered_sections__section')
        )
        return Response(
            {'pending': SealValidityRecordSerializer(pending, many=True).data}
        )

    if request.effective_role != 'admin':
        raise Http404
    serializer = SealPlanConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        resolved = seal_service.confirm_seal_plan(
            version, request.user, serializer.validated_data['decisions'], request=request
        )
    except DomainError as exc:
        return Response({'error': str(exc)}, status=exc.status_code)
    return Response(
        {'resolved': SealValidityRecordSerializer(resolved, many=True).data}
    )


@api_view(['GET'])
def seal_public_key(request, key_id):
    """Public key material for offline verification (E4 groundwork)."""
    if key_id != signing.key_id():
        raise Http404
    return Response({
        'key_id': key_id,
        'algorithm': 'Ed25519',
        'public_key': signing.public_key_b64(),
    })
