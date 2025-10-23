from django.db import models

class ViewCounter(models.Model):
    # key unik per halaman: contoh "sportjson:12", "gear:uuid", "gearjson:7"
    key       = models.CharField(max_length=200, unique=True)
    title     = models.CharField(max_length=200)
    url       = models.CharField(max_length=300)
    category  = models.CharField(max_length=50)  # "Library" | "Gear Guide" | dst
    image     = models.CharField(max_length=500, blank=True, null=True)

    views     = models.PositiveIntegerField(default=0)
    first_seen= models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["-views"]),
            models.Index(fields=["category", "-views"]),
        ]

    def __str__(self):
        return f"{self.key} ({self.views})"
