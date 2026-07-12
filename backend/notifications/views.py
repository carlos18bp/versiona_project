"""In-app notification center endpoints (kit 5)."""

from django.http import Http404
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import serializers

from .models import NOTIFICATION_CATALOG, Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            'public_id', 'event_key', 'title', 'body', 'link', 'payload',
            'read_at', 'created_at',
        )


@api_view(['GET'])
def my_notifications(request):
    queryset = Notification.objects.filter(user=request.user)
    unread = queryset.filter(read_at__isnull=True).count()
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(queryset, request)
    response = paginator.get_paginated_response(NotificationSerializer(page, many=True).data)
    response.data['unread'] = unread
    return response


@api_view(['POST'])
def notification_read(request, notif):
    notification = Notification.objects.filter(
        user=request.user, public_id=notif
    ).first()
    if notification is None:
        raise Http404
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=['read_at', 'updated_at'])
    return Response(NotificationSerializer(notification).data)


@api_view(['POST'])
def notifications_read_all(request):
    updated = Notification.objects.filter(
        user=request.user, read_at__isnull=True
    ).update(read_at=timezone.now())
    return Response({'marked': updated})


@api_view(['GET', 'PATCH'])
def my_notification_preferences(request):
    """GET: catalog merged with the user's overrides. PATCH: upsert overrides
    {event_key: {in_app: bool, email: bool}} — mandatory events stay on."""
    if request.method == 'PATCH':
        payload = request.data or {}
        for event_key, channels in payload.items():
            if event_key not in NOTIFICATION_CATALOG:
                return Response({'error': f'Evento desconocido: {event_key}'}, status=400)
            for channel, enabled in (channels or {}).items():
                if channel not in ('in_app', 'email'):
                    return Response({'error': f'Canal desconocido: {channel}'}, status=400)
                if (
                    channel == 'in_app'
                    and NOTIFICATION_CATALOG[event_key].get('mandatory_in_app')
                    and not enabled
                ):
                    return Response(
                        {'error': f'"{event_key}" no puede silenciarse: es trabajo asignado.'},
                        status=400,
                    )
                NotificationPreference.objects.update_or_create(
                    user=request.user, event_key=event_key, channel=channel,
                    defaults={'enabled': bool(enabled)},
                )

    overrides = {
        (pref.event_key, pref.channel): pref.enabled
        for pref in NotificationPreference.objects.filter(user=request.user)
    }
    result = []
    for event_key, meta in NOTIFICATION_CATALOG.items():
        result.append({
            'event_key': event_key,
            'label_es': meta['label_es'],
            'label_en': meta['label_en'],
            'mandatory_in_app': meta['mandatory_in_app'],
            'in_app': overrides.get((event_key, 'in_app'), meta['default_in_app']),
            'email': overrides.get((event_key, 'email'), meta['default_email']),
        })
    return Response({'preferences': result})
