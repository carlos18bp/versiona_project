"""Seal + validity serializers (D4/D5)."""

from rest_framework import serializers

from .models import Seal, SealValidityRecord


class SealSerializer(serializers.ModelSerializer):
    reviewer_email = serializers.EmailField(source='reviewer.email', read_only=True)
    version_number = serializers.IntegerField(source='document_version.number', read_only=True)
    covered_keys = serializers.ListField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Seal
        fields = (
            'public_id', 'reviewer_email', 'version_number', 'covers_all',
            'covered_keys', 'key_id', 'is_active', 'revoked_at', 'created_at',
        )


class SealCreateSerializer(serializers.Serializer):
    covers_all = serializers.BooleanField(default=False)
    section_keys = serializers.ListField(
        child=serializers.CharField(max_length=250), required=False, default=list
    )


class SealValidityRecordSerializer(serializers.ModelSerializer):
    seal = SealSerializer(read_only=True)
    to_version = serializers.IntegerField(source='to_document_version.number', read_only=True)
    decided_by_email = serializers.EmailField(
        source='decided_by.email', read_only=True, default=None
    )

    class Meta:
        model = SealValidityRecord
        fields = (
            'seal', 'to_version', 'decision', 'proposed_decision', 'reason_code',
            'evidence', 'decided_mode', 'decided_by_email', 'decided_at', 'created_at',
        )


class SealPlanConfirmSerializer(serializers.Serializer):
    """{decisions: {seal_public_id: 'preserved'|'invalidated'}}"""

    decisions = serializers.DictField(
        child=serializers.ChoiceField(choices=['preserved', 'invalidated'])
    )
