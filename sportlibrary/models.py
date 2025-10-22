from django.db import models
from django.contrib.auth.models import User
import uuid

# Create your models here.

class Sport(models.Model):
    CATEGORY_CHOICES = [
        ('indoor', 'Indoor'),
        ('outdoor', 'Outdoor'),
        ('water', 'Water'),
        ('extreme', 'Extreme'),
        ('team', 'Team'),
        ('individual', 'Individual'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('pemula', 'Pemula'),
        ('menengah', 'Menengah'),
        ('lanjutan', 'Lanjutan'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='belum di set'
    )
    difficulty = models.CharField(max_length=50, choices=DIFFICULTY_CHOICES)
    description = models.TextField()
    history = models.TextField()
    benefits = models.JSONField(default=list, help_text="List of benefits")
    popular_countries = models.JSONField(default=list, help_text="List of countries where sport is popular")
    tags = models.JSONField(default=list, help_text="List of tags for searching")
    thumbnail = models.ImageField(upload_to='sports/thumbnails/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Sport'
        verbose_name_plural = 'Sports'
    
    def __str__(self):
        return self.name


class Rule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='rules')
    rule_text = models.TextField()
    order = models.IntegerField(default=0, help_text="Order of display")
    
    class Meta:
        ordering = ['order']
        verbose_name = 'Rule'
        verbose_name_plural = 'Rules'
    
    def __str__(self):
        return f"{self.sport.name} - Rule {self.order}"


class Technique(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='techniques')
    technique_name = models.CharField(max_length=200)
    description = models.TextField()
    order = models.IntegerField(default=0, help_text="Order of display")
    
    class Meta:
        ordering = ['order']
        verbose_name = 'Technique'
        verbose_name_plural = 'Techniques'
    
    def __str__(self):
        return f"{self.sport.name} - {self.technique_name}"


class Video(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=200)
    url = models.URLField(help_text="YouTube or other video platform URL")
    thumbnail_url = models.URLField(blank=True, null=True)
    duration = models.IntegerField(null=True, blank=True, help_text="Duration in seconds")
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Video'
        verbose_name_plural = 'Videos'
    
    def __str__(self):
        return f"{self.sport.name} - {self.title}"


class Gear(models.Model):
    """Model untuk perlengkapan olahraga"""
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name="library_gears")
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(max_length=100)
    function = models.TextField(blank=True, null=True)  # fungsi alat
    description = models.TextField()
    required = models.BooleanField(default=True)
    
    image = models.URLField(blank=True, null=True)
    price_range = models.CharField(max_length=50, blank=True, null=True)
    ecommerce_link = models.URLField(blank=True, null=True)
    
    difficulty_level = models.CharField(
        max_length=50,
        choices=[
            ('beginner', 'Pemula'),
            ('intermediate', 'Menengah'),
            ('advanced', 'Lanjutan')
        ],
        default='beginner'
    )
    
    recommended_brands = models.TextField(blank=True, null=True)
    materials = models.TextField(blank=True, null=True)
    care_tips = models.TextField(blank=True, null=True)
    tags = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Gear'
        verbose_name_plural = 'Gears'
    
    def __str__(self):
        return f"{self.name} - {self.sport.name}"
    
    def get_brands_list(self):
        return [b.strip() for b in (self.recommended_brands or "").split(",") if b.strip()]
    
    def get_materials_list(self):
        return [m.strip() for m in (self.materials or "").split(",") if m.strip()]
    
    def get_tags_list(self):
        return [t.strip() for t in (self.tags or "").split(",") if t.strip()]


class Bookmark(models.Model):
    """Bookmark olahraga oleh user"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sport_bookmarks')
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='bookmarked_by')
    notes = models.TextField(blank=True, help_text="Personal notes about this sport")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'sport']
        verbose_name = 'Bookmark'
        verbose_name_plural = 'Bookmarks'
    
    def __str__(self):
        return f"{self.user.username} - {self.sport.name}"

class SportProgress(models.Model):
    """Track user's learning progress for each sport"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sport_progress')
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='user_progress')
    completed_videos = models.ManyToManyField(Video, blank=True, related_name='completed_by')
    progress_percentage = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-last_accessed']
        unique_together = ['user', 'sport']
        verbose_name = 'Sport Progress'
        verbose_name_plural = 'Sport Progress'
    
    def __str__(self):
        return f"{self.user.username} - {self.sport.name} ({self.progress_percentage}%)"