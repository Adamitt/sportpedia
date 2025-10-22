from django.db import models

class Sport(models.Model):
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

    # ⚠️ Ini penting banget: pastikan related_name = "gear_relations"
    gears = models.ManyToManyField("gearguide.Gear", related_name="gear_relations")

    def __str__(self):
        return self.name
