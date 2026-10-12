from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Incident


class IncidentAPITests(APITestCase):
	url = '/api/incidents/'

	def setUp(self):
		user = get_user_model().objects.create_user(username='incident-tester')
		self.client.force_authenticate(user=user)

	def test_create_incident(self):
		response = self.client.post(
			self.url,
			{'title': 'Database unavailable', 'severity': 'high'},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data['title'], 'Database unavailable')
		self.assertEqual(Incident.objects.count(), 1)

	def test_creation_uses_default_values(self):
		start_time = timezone.now()
		response = self.client.post(
			self.url,
			{
				'title': 'Slow response',
				'status': Incident.Status.RESOLVED,
				'created_at': '2000-01-01T00:00:00Z',
			},
			format='json',
		)
		end_time = timezone.now()

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data['severity'], Incident.Severity.LOW)
		self.assertEqual(response.data['status'], Incident.Status.OPEN)
		created_at = parse_datetime(response.data['created_at'])
		self.assertIsNotNone(created_at)
		self.assertGreaterEqual(created_at, start_time)
		self.assertLessEqual(created_at, end_time)

	def test_rejects_empty_or_whitespace_only_title(self):
		for title in ('', '   '):
			with self.subTest(title=title):
				response = self.client.post(self.url, {'title': title}, format='json')

				self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
				self.assertIn('title', response.data)

	def test_rejects_invalid_severity(self):
		response = self.client.post(
			self.url,
			{'title': 'Database unavailable', 'severity': 'critical'},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('severity', response.data)

	def test_lists_incidents(self):
		incident = Incident.objects.create(title='Queue backlog')

		response = self.client.get(self.url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]['id'], incident.id)

	def test_anonymous_get_is_denied(self):
		self.client.force_authenticate(user=None)

		response = self.client.get(self.url)

		self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

	def test_anonymous_post_is_denied(self):
		self.client.force_authenticate(user=None)

		response = self.client.post(self.url, {'title': 'Anonymous incident'}, format='json')

		self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
