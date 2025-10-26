from django.db import models
from django.contrib.auth.models import User
from sportlibrary.models import Sport
import uuid
from django.conf import settings

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name='profile')
    olahraga_favorit = models.CharField(max_length=100, blank=True, null=True)
    preferensi = models.TextField(blank=True, null=True)
    foto_profil = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.user.username

class SportProgress(models.Model):
    TARGET_SECONDS = 240 # Target time in seconds for 100%

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE)
    # Ensure time_spent can store enough seconds (e.g., IntegerField)
    time_spent = models.PositiveIntegerField(default=0) # Store total seconds spent
    completed = models.BooleanField(default=False)
    last_accessed = models.DateTimeField(auto_now=True)

    @property
    def percent(self):
        """Calculates the completion percentage."""
        if self.completed:
            return 100
        # Calculate percentage, ensuring it doesn't exceed 100
        percentage = min(int((self.time_spent / self.TARGET_SECONDS) * 100), 100)
        return percentage

    def __str__(self):
        return f"{self.user.username} - {self.sport.name} ({self.percent}%)"

    class Meta:
        unique_together = ('user', 'sport') # Prevent duplicate entries
        ordering = ['-last_accessed']

class ActivityLog(models.Model):
    # Define choices for the type of action
    ACTION_CHOICES = [
        ('MODULE_ACCESS', 'Accessed Module'), # e.g., Sport Library detail, Gear Guide detail
        ('VIDEO_VIEW', 'Viewed Video'),       # Placeholder
        ('FORUM_POST', 'Posted in Forum'),    # Placeholder
        ('TESTIMONIAL_SUBMIT', 'Submitted Testimonial'),
        ('ADMIN_CREATE', 'Admin: Created Item'),
        ('ADMIN_UPDATE', 'Admin: Updated Item'),
        ('ADMIN_DELETE', 'Admin: Deleted Item'),
        # Add more types as needed
    ]

    # Link to the user who performed the action
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='activity_logs' # Helps retrieve logs for a user easily
    )
    # Type of action performed
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    # A human-readable description of the action
    description = models.TextField()
    # Timestamp when the action occurred (automatically set on creation)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True) # db_index helps sorting

    class Meta:
        ordering = ['-timestamp'] # Show newest activities first by default

    def __str__(self):
        # Useful representation in Django admin
        return f"{self.user.username} - {self.get_action_type_display()} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"