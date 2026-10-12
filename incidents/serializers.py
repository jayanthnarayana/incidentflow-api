from rest_framework import serializers

from .models import Incident


class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = ('id', 'title', 'severity', 'status', 'created_at')
        read_only_fields = ('status', 'created_at')

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError('Title must not be empty.')
        return value