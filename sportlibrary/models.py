from django.db import models
from django.contrib.auth.models import User
import uuid

class Sport(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20)
    difficulty = models.CharField(max_length=20)
    description = models.TextField()
    history = models.TextField()
    image = models.ImageField(upload_to='sports/', blank=True, null=True)

    rules = models.JSONField(default=list)
    techniques = models.JSONField(default=list)
    benefits = models.JSONField(default=list)
    popular_countries = models.JSONField(default=list)
    tags = models.JSONField(default=list)

    gears = models.ManyToManyField("gearguide.Gear", related_name="gear_relations")

    def __str__(self):
        return self.name
    
class SavedSport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_sports")
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name="saved_by_users")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'sport')  # biar user ga bisa save sport yg sama dua kali

    def __str__(self):
        return f"{self.user.username} - {self.sport.name}"