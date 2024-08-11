from django.db import models
from accounts.models import User

class Event(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    location = models.CharField(max_length=255, db_index=True)
    start_datetime = models.DateTimeField(db_index=True)
    end_datetime = models.DateTimeField(db_index=True)
    eventCreator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='eventCreator', db_index=True)
    organizer = models.CharField(max_length=100)
    image = models.ImageField(upload_to='events/images', blank=True, null=True)
    attendees = models.CharField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['location']),
            models.Index(fields=['start_datetime']),
            models.Index(fields=['end_datetime']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
            models.Index(fields=['eventCreator']),  # Explicitly defining index for organizer
            models.Index(fields=['organizer']),  # Explicitly defining index for organizer
        ]

    def __str__(self):
        return self.title
