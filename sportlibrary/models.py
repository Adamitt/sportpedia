from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import uuid

class Sport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20)
    difficulty = models.CharField(max_length=20)
    description = models.TextField()
    history = models.TextField()

    rules = models.JSONField(default=list)
    techniques = models.JSONField(default=list)
    benefits = models.JSONField(default=list)
    popular_countries = models.JSONField(default=list)
    tags = models.JSONField(default=list)

    # Tetap pertahankan M2M ini karena sudah dipakai tim (hindari pecah kompatibilitas)
    gears = models.ManyToManyField("gearguide.Gear", related_name="gear_relations")

    def __str__(self):
        return self.name

class SavedSport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'sport')
