"""Project serializers (triple pattern — docs/plan/03 §1). Flows B1/B2/B4."""

from rest_framework import serializers

from .models import Project


class ProjectListSerializer(serializers.ModelSerializer):
    document_count = serializers.IntegerField(read_only=True, default=0)
    effective_role = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            'public_id', 'name', 'slug', 'description', 'status', 'is_sample',
            'document_count', 'effective_role', 'created_at', 'updated_at',
        )

    def get_effective_role(self, obj):
        roles = self.context.get('roles_by_project') or {}
        return roles.get(obj.pk)


class ProjectDetailSerializer(ProjectListSerializer):
    class Meta(ProjectListSerializer.Meta):
        fields = ProjectListSerializer.Meta.fields


class ProjectCreateUpdateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=140)
    description = serializers.CharField(allow_blank=True, required=False, default='')

    class Meta:
        model = Project
        fields = ('name', 'description')


class TrashItemSerializer(serializers.Serializer):
    type = serializers.CharField()
    public_id = serializers.UUIDField()
    name = serializers.CharField()
    context = serializers.CharField()
    deleted_at = serializers.DateTimeField()
    deleted_by = serializers.CharField(allow_null=True)
    purge_after = serializers.DateTimeField(allow_null=True)
