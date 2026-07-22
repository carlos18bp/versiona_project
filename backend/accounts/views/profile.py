"""User profile & preferences (kit 2/7 — /settings screen, docs/audit/02 G28)."""

import zoneinfo

from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from accounts.models import User
from audit import services as audit
from orgs.services import ensure_personal_org


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone', 'language', 'timezone')
        read_only_fields = ('email',)

    def validate_timezone(self, value):
        try:
            zoneinfo.ZoneInfo(value)
        except (zoneinfo.ZoneInfoNotFoundError, ValueError):
            raise serializers.ValidationError('Zona horaria IANA inválida.')
        return value


@api_view(['GET', 'PATCH'])
def me_profile(request):
    if request.method == 'GET':
        return Response(ProfileSerializer(request.user).data)

    serializer = ProfileSerializer(request.user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    org = ensure_personal_org(request.user)
    audit.record(org=org, actor=request.user, event_type='profile.updated',
                 obj=request.user, payload={'fields': sorted(request.data.keys())},
                 request=request)
    return Response(ProfileSerializer(request.user).data, status=status.HTTP_200_OK)
