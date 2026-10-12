from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Incident


class IncidentAPITests(APITestCase):
	url = '/api/incidents/'

	def setUp(self):
		self.user = get_user_model().objects.create_user(username='incident-tester')
		self.client.force_authenticate(user=self.user)

	def test_create_incident(self):
		response = self.client.post(
			self.url,
			{'title': 'Database unavailable', 'severity': 'high'},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data['title'], 'Database unavailable')
		self.assertEqual(Incident.objects.count(), 1)
		self.assertEqual(Incident.objects.get().owner, self.user)

	def test_creation_defaults_and_server_timestamp(self):
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
		self.assertEqual(Incident.objects.get().owner, self.user)

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

	def test_anonymous_get_and_post_are_denied(self):
		self.client.force_authenticate(user=None)

		get_response = self.client.get(self.url)
		post_response = self.client.post(
			self.url,
			{'title': 'Anonymous incident'},
			format='json',
		)

		self.assertIn(get_response.status_code, (401, 403))
		self.assertIn(post_response.status_code, (401, 403))

	def test_list_orders_newest_first_with_id_tiebreaker(self):
		older = Incident.objects.create(title='Older', owner=self.user)
		tied_first = Incident.objects.create(title='Tied first', owner=self.user)
		tied_second = Incident.objects.create(title='Tied second', owner=self.user)
		now = timezone.now()
		Incident.objects.filter(pk=older.pk).update(created_at=now - timedelta(days=1))
		Incident.objects.filter(pk__in=(tied_first.pk, tied_second.pk)).update(created_at=now)

		response = self.client.get(self.url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(
			[item['id'] for item in response.data['results']],
			[tied_second.id, tied_first.id, older.id],
		)

	def test_list_is_paginated_with_ten_results(self):
		self.create_incidents(12)

		response = self.client.get(self.url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['count'], 12)
		self.assertIsNotNone(response.data['next'])
		self.assertIsNone(response.data['previous'])
		self.assertEqual(len(response.data['results']), 10)

	def test_second_page_contains_remaining_oldest_incidents(self):
		incident_ids = self.create_incidents(12)

		response = self.client.get(self.url, {'page': 2})

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['count'], 12)
		self.assertIsNone(response.data['next'])
		self.assertIsNotNone(response.data['previous'])
		self.assertEqual(
			[item['id'] for item in response.data['results']],
			list(reversed(incident_ids[:2])),
		)

	def create_incidents(self, count):
		incidents = [
			Incident.objects.create(title=f'Incident {index}', owner=self.user)
			for index in range(count)
		]
		Incident.objects.filter(owner=self.user).update(created_at=timezone.now())
		return [incident.id for incident in incidents]

	def test_lists_incidents(self):
		incident = Incident.objects.create(title='Queue backlog', owner=self.user)

		response = self.client.get(self.url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['count'], 1)
		self.assertEqual(len(response.data['results']), 1)
		self.assertEqual(response.data['results'][0]['id'], incident.id)

	def test_user_sees_only_their_own_incidents(self):
		own_incident = Incident.objects.create(title='Mine', owner=self.user)
		other_user = get_user_model().objects.create_user(username='other-user')
		Incident.objects.create(title='Theirs', owner=other_user)

		response = self.client.get(self.url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['count'], 1)
		self.assertEqual(response.data['results'][0]['id'], own_incident.id)

	def test_other_user_cannot_see_incidents(self):
		Incident.objects.create(title='User A incident', owner=self.user)
		other_user = get_user_model().objects.create_user(username='other-user')
		self.client.force_authenticate(user=other_user)

		response = self.client.get(self.url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['count'], 0)
		self.assertEqual(response.data['results'], [])

	def test_client_cannot_override_incident_owner(self):
		other_user = get_user_model().objects.create_user(username='other-user')

		response = self.client.post(
			self.url,
			{'title': 'Owned by requester', 'owner': other_user.pk},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		incident = Incident.objects.get()
		self.assertEqual(incident.owner, self.user)
		self.assertEqual(response.data['owner'], self.user.pk)

	def test_anonymous_get_is_denied(self):
		self.client.force_authenticate(user=None)

		response = self.client.get(self.url)

		self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

	def test_anonymous_post_is_denied(self):
		self.client.force_authenticate(user=None)

		response = self.client.post(self.url, {'title': 'Anonymous incident'}, format='json')

		self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
