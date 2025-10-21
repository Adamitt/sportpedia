from django.db import models
from sportlibrary.models import Sport
import uuid

class Gear(models.Model):
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name="gears")
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    required = models.BooleanField(default=True)  # apakah alat wajib atau opsional
    image = models.URLField(blank=True, null=True)  # link gambar alat (opsional)
    price_range = models.CharField(max_length=50, blank=True, null=True)  # contoh: "Rp300.000 – Rp800.000"
    ecommerce_link = models.URLField(blank=True, null=True)  # link rekomendasi e-commerce
    difficulty_level = models.CharField(max_length=50, choices=[
        ('beginner', 'Pemula'),
        ('intermediate', 'Menengah'),
        ('advanced', 'Lanjutan')
    ], default='beginner')
    tips = models.TextField(blank=True, null=True)  # tips tambahan untuk pemakaian alat

    def __str__(self):
        return f"{self.name} - {self.sport.name}"
