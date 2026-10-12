from rest_framework.generics import ListCreateAPIView

from .models import Incident
from .serializers import IncidentSerializer


class IncidentListCreateView(ListCreateAPIView):
	queryset = Incident.objects.all()
	serializer_class = IncidentSerializer
