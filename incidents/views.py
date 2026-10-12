from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated

from .models import Incident
from .serializers import IncidentSerializer


class IncidentListCreateView(ListCreateAPIView):
	queryset = Incident.objects.all()
	serializer_class = IncidentSerializer
	permission_classes = [IsAuthenticated]
