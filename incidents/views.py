from rest_framework.generics import ListCreateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from .models import Incident
from .serializers import IncidentSerializer


class IncidentPagination(PageNumberPagination):
	page_size = 10


class IncidentListCreateView(ListCreateAPIView):
	serializer_class = IncidentSerializer
	permission_classes = [IsAuthenticated]
	pagination_class = IncidentPagination

	def get_queryset(self):
		return Incident.objects.filter(owner=self.request.user).order_by('-created_at', '-id')

	def perform_create(self, serializer):
		serializer.save(owner=self.request.user)
