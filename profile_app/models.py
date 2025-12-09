from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name='profile')
    olahraga_favorit = models.CharField(max_length=100, blank=True, null=True)
    preferensi = models.TextField(blank=True, null=True)
    foto_profil = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.user.username

class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('MODULE_ACCESS', 'Accessed Module'),
        ('VIDEO_VIEW', 'Viewed Video'),
        ('FORUM_POST', 'Posted in Forum'),
        ('TESTIMONIAL_SUBMIT', 'Submitted Testimonial'),
        ('ADMIN_CREATE', 'Admin: Created Item'),
        ('ADMIN_UPDATE', 'Admin: Updated Item'),
        ('ADMIN_DELETE', 'Admin: Deleted Item'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activity_logs'
    )
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.get_action_type_display()} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"