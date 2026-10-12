from rest_framework.generics import ListCreateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from .models import Incident
from .serializers import IncidentSerializer


class IncidentPagination(PageNumberPagination):
	page_size = 10


class IncidentListCreateView(ListCreateAPIView):
	queryset = Incident.objects.order_by('-created_at', '-id')
	serializer_class = IncidentSerializer
	permission_classes = [IsAuthenticated]
	pagination_class = IncidentPagination
