from django.db import models
from django.utils import timezone
from main.models import School


class Event(models.Model):
    school = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=50)
    description = models.TextField()
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(default=timezone.now)
    location = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.title

    @classmethod
    def get_school_events(cls, request):
        user = request.user
        school = School.get_user_school(user)
        """Return all events for a specific school"""
        return cls.objects.filter(school=school).order_by('start_date')
