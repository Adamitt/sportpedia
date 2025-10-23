from django.db import models
from django.contrib.auth.models import User
from sportlibrary.models import Sport
import uuid

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    olahraga_favorit = models.CharField(max_length=100, blank=True, null=True)
    preferensi = models.TextField(blank=True, null=True)
    foto_profil = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return self.user.username

class SportProgress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    time_spent = models.FloatField(default=0.0)  # dalam detik
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'sport')

    def __str__(self):
        return f"{self.user.username} - {self.sport.name} ({'Done' if self.completed else 'In Progress'})"