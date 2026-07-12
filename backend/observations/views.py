"""Observation endpoints (D3)."""

from django.http import Http404
from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.permissions import require_project_role, resolve_effective_role
from documents.models import DocumentVersion
from documents.services.version_service import DomainError

from .models import Observation, ObservationAnchor, ObservationReply
from . import services


class ReplySerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source='author.email', read_only=True)

    class Meta:
        model = ObservationReply
        fields = ('public_id', 'author_email', 'body', 'status_change', 'created_at')


class AnchorSerializer(serializers.ModelSerializer):
    version_number = serializers.IntegerField(source='document_version.number', read_only=True)

    class Meta:
        model = ObservationAnchor
        fields = ('version_number', 'page', 'quads', 'text_snippet', 'method')


class ObservationSerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source='author.email', read_only=True)
    section_key = serializers.CharField(source='section.stable_key', read_only=True, default=None)
    section_heading = serializers.CharField(
        source='section.title_current', read_only=True, default=None
    )
    created_on = serializers.IntegerField(source='created_on_version.number', read_only=True)
    resolved_in = serializers.IntegerField(
        source='resolved_in_version.number', read_only=True, default=None
    )
    replies = ReplySerializer(many=True, read_only=True)
    anchors = AnchorSerializer(many=True, read_only=True)

    class Meta:
        model = Observation
        fields = (
            'public_id', 'body', 'status', 'author_email', 'section_key',
            'section_heading', 'created_on', 'resolved_in', 'replies', 'anchors',
            'created_at',
        )


class ObservationCreateSerializer(serializers.Serializer):
    body = serializers.CharField()
    section_key = serializers.CharField(required=False, allow_blank=True, default='')
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    quads = serializers.ListField(child=serializers.DictField(), required=False, default=list)
    snippet = serializers.CharField(required=False, allow_blank=True, default='')


@api_view(['GET', 'POST'])
@require_project_role('viewer')
def version_observations(request, ver):
    """GET: the document's threads with their anchor for THIS version.
    POST (reviewer+): open a thread anchored to a section/region of it."""
    version: DocumentVersion = request.resolved_object

    if request.method == 'GET':
        status_filter = request.query_params.get('status')
        queryset = (
            Observation.objects.filter(document=version.document)
            .select_related('author', 'section', 'created_on_version', 'resolved_in_version')
            .prefetch_related('replies__author', 'anchors__document_version')
        )
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return Response({'results': ObservationSerializer(queryset, many=True).data})

    if request.effective_role not in ('reviewer', 'admin'):
        raise Http404
    serializer = ObservationCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        observation = services.create_observation(
            version, request.user,
            body=serializer.validated_data['body'],
            section_key=serializer.validated_data['section_key'],
            page=serializer.validated_data['page'],
            quads=serializer.validated_data['quads'],
            snippet=serializer.validated_data['snippet'],
            request=request,
        )
    except DomainError as exc:
        return Response({'error': str(exc)}, status=exc.status_code)
    return Response(ObservationSerializer(observation).data, status=status.HTTP_201_CREATED)


def _load_observation(request, obs):
    observation = (
        Observation.objects.filter(public_id=obs)
        .select_related('document__project__organization', 'author', 'section')
        .first()
    )
    if observation is None:
        raise Http404
    role = resolve_effective_role(request.user, observation.document.project)
    if role is None:
        raise Http404
    request.effective_role = role
    return observation


@api_view(['POST'])
def observation_reply(request, obs):
    observation = _load_observation(request, obs)
    if request.effective_role == 'viewer':
        raise Http404  # read-only role
    body = (request.data or {}).get('body', '')
    try:
        services.reply_to_observation(observation, request.user, body, request=request)
    except DomainError as exc:
        return Response({'error': str(exc)}, status=exc.status_code)
    observation.refresh_from_db()
    return Response(ObservationSerializer(observation).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def observation_status(request, obs):
    observation = _load_observation(request, obs)
    if request.effective_role == 'viewer':
        raise Http404
    new_status = (request.data or {}).get('status', '')
    try:
        services.set_observation_status(observation, request.user, new_status, request=request)
    except DomainError as exc:
        return Response({'error': str(exc)}, status=exc.status_code)
    return Response(ObservationSerializer(observation).data)
