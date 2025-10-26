from django.db import models
from sportlibrary.models import Sport
from django.conf import settings  # ⬅️ TAMBAHKAN INI
# import uuid  # (opsional: hapus kalau tak dipakai)
# from django.contrib.auth.models import User  # (opsional: tidak dipakai)

class Gear(models.Model):
    id = models.AutoField(primary_key=True)
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name="gear_items")

    name = models.CharField(max_length=100)
    function = models.TextField(blank=True, null=True)
    description = models.TextField()
    required = models.BooleanField(default=True)

    image = models.URLField(blank=True, null=True)
    price_range = models.CharField(max_length=50, blank=True, null=True)
    ecommerce_link = models.URLField(blank=True, null=True)

    level = models.CharField(
        max_length=50,
        choices=[
            ('beginner', 'Pemula'),
            ('intermediate', 'Menengah'),
            ('advanced', 'Lanjutan'),
        ],
        default='beginner'
    )

    recommended_brands = models.JSONField(blank=True, null=True, default=list)
    materials = models.JSONField(blank=True, null=True, default=list)
    care_tips = models.TextField(blank=True, null=True)
    tags = models.JSONField(blank=True, null=True, default=list)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='gears'
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Gear'
        verbose_name_plural = 'Gears'

    def __str__(self):
        return f"{self.name} - {self.sport.name}"

    def to_dict(self):
        return {
            "id": str(self.id),
            "sport": self.sport.name,
            "name": self.name,
            "description": self.description,
            "price_range": self.price_range,
            "level": self.get_level_display(),
            "brands": self.recommended_brands or [],
            "tags": self.tags or [],
            "buy_link": self.ecommerce_link,
            "image": self.image,
        }
