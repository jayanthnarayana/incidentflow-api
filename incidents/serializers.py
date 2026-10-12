from rest_framework import serializers

from .models import Incident


class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = ('id', 'title', 'severity', 'status', 'created_at', 'owner')
        read_only_fields = ('status', 'created_at', 'owner')