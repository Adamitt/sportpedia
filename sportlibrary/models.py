from django.db import models
import uuid

class Sport(models.Model):
    id = models.AutoField(primary_key=True)
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

    # pakai string reference biar gak import langsung
    gears = models.ManyToManyField(
        "gearguide.Gear",
        related_name="sports",
        blank=True
    )

    def __str__(self):
        return self.name
