"""Comparison serializers (flow E1)."""

from rest_framework import serializers

from .models import Comparison, SectionDiff


class SectionDiffListSerializer(serializers.ModelSerializer):
    """Light row for the modified-sections list (no word diff payload)."""

    class Meta:
        model = SectionDiff
        fields = (
            'stable_key', 'heading_from', 'heading_to', 'change_type',
            'similarity', 'order_index',
        )


class SectionDiffDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SectionDiff
        fields = (
            'stable_key', 'heading_from', 'heading_to', 'change_type', 'similarity',
            'order_index', 'word_diff', 'bboxes_from', 'bboxes_to',
        )


class ComparisonDetailSerializer(serializers.ModelSerializer):
    from_version = serializers.UUIDField(source='from_version.public_id', read_only=True)
    to_version = serializers.UUIDField(source='to_version.public_id', read_only=True)
    from_number = serializers.IntegerField(source='from_version.number', read_only=True)
    to_number = serializers.IntegerField(source='to_version.number', read_only=True)
    has_changes = serializers.BooleanField(read_only=True)
    section_changes = SectionDiffListSerializer(source='diffs', many=True, read_only=True)

    class Meta:
        model = Comparison
        fields = (
            'public_id', 'status', 'trigger', 'summary', 'has_changes',
            'from_version', 'to_version', 'from_number', 'to_number',
            'section_changes', 'created_at',
        )


class ComparisonCreateSerializer(serializers.Serializer):
    from_version = serializers.UUIDField()
    to_version = serializers.UUIDField()
