from django.db import models
import uuid

class Sport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='sports/', blank=True, null=True) #
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
