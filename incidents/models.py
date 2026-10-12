from django.db import models


class Incident(models.Model):
	class Severity(models.TextChoices):
		LOW = 'low', 'Low'
		MEDIUM = 'medium', 'Medium'
		HIGH = 'high', 'High'

	class Status(models.TextChoices):
		OPEN = 'open', 'Open'
		RESOLVED = 'resolved', 'Resolved'

	title = models.CharField(max_length=200)
	severity = models.CharField(
		max_length=6,
		choices=Severity.choices,
		default=Severity.LOW,
	)
	status = models.CharField(
		max_length=8,
		choices=Status.choices,
		default=Status.OPEN,
	)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.title
