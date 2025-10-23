from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    olahraga_favorit = models.CharField(max_length=100, blank=True, null=True)
    preferensi = models.TextField(blank=True, null=True)
    foto_profil = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return self.user.username