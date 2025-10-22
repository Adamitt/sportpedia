from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    olahraga_favorit = models.CharField(max_length=100, blank=True, null=True)
    preferensi = models.TextField(blank=True, null=True)
    foto_profil = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return self.user.username


class ProgressTracker(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    olahraga_dipelajari = models.CharField(max_length=100)
    video_ditonton = models.CharField(max_length=200, blank=True, null=True)
    artikel_dibaca = models.CharField(max_length=200, blank=True, null=True)
    tanggal_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Progress {self.user.username} - {self.olahraga_dipelajari}"

class ActivityLog(models.Model):
    ACTIVITY_CHOICES = [
        ('forum', 'Forum'),
        ('pustaka', 'Pustaka'),
        ('video', 'Video'),
        ('other', 'Lainnya'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    aktivitas = models.CharField(max_length=50, choices=ACTIVITY_CHOICES)
    deskripsi = models.TextField()
    waktu = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.aktivitas} ({self.waktu.strftime('%Y-%m-%d %H:%M')})"