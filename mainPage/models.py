# mainPage/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

User = get_user_model()

# =======================================================
#                      PAGE HIT
# =======================================================
class PageHit(models.Model):
    view_name = models.CharField(max_length=100, db_index=True)
    path      = models.CharField(max_length=255)
    title     = models.CharField(max_length=120, blank=True)
    hits      = models.PositiveIntegerField(default=0, db_index=True)
    last_hit  = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("view_name", "path")]
        indexes = [models.Index(fields=["-hits", "-last_hit"])]

    def __str__(self):
        return f"{self.view_name} • {self.path} ({self.hits})"


# =======================================================
#                      TESTIMONIAL
# =======================================================
class Testimonial(models.Model):
    CATEGORY_CHOICES = [
        ("library",   "Sports Library"),
        ("community", "Community"),
        ("gearguide", "Gear Guide"),
        ("video",     "Video"),
    ]

    user        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="testimonials")
    title       = models.CharField(max_length=120)
    text        = models.TextField()
    category    = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="library", db_index=True)
    image       = models.ImageField(upload_to="testimonials/", blank=True, null=True)
    rating      = models.PositiveSmallIntegerField(default=5)
    is_approved = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"


# =======================================================
#                      WHAT'S HOT
# =======================================================
class TimeStamped(models.Model):
    """Abstract base class untuk inheritance (created/updated)."""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class WhatsHot(TimeStamped):
    """Model dinamis untuk menampilkan konten 'What's Hot' dari berbagai modul."""
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="whats_hot_items"
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    label     = models.CharField(max_length=80, blank=True, help_text="Label kecil seperti 'Trending • Library'")
    priority  = models.IntegerField(default=0, help_text="Semakin besar, semakin di atas")
    starts_at = models.DateTimeField(default=timezone.now)
    ends_at   = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("-priority", "-created_at")
        verbose_name = "What's Hot"
        verbose_name_plural = "What's Hot"

    def __str__(self):
        return f"{self.label or 'WhatsHot'} → {self.content_type} #{self.object_id}"

    def active(self):
        """Return True kalau masih aktif berdasar waktu & flag."""
        now = timezone.now()
        if not self.is_active: return False
        if self.starts_at and self.starts_at > now: return False
        if self.ends_at and self.ends_at < now: return False
        return True

    # ==== UTIL UNTUK FRONTEND ====
    def get_title(self):
        for attr in ("title", "name", "headline"):
            if hasattr(self.content_object, attr):
                return getattr(self.content_object, attr)
        return f"{self.content_type} #{self.object_id}"

    def get_image_url(self):
        for attr in ("image", "cover", "thumbnail", "poster"):
            if hasattr(self.content_object, attr):
                img = getattr(self.content_object, attr)
                try:
                    return img.url
                except Exception:
                    if isinstance(img, str):
                        return img
        return ""

    def get_url(self):
        if hasattr(self.content_object, "get_absolute_url"):
            try:
                return self.content_object.get_absolute_url()
            except Exception:
                pass
        return "/"
