# videos/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from sportlibrary.models import Sport
from django.conf import settings

class Video(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Pemula'),
        ('intermediate', 'Menengah'),
        ('advanced', 'Lanjutan'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    sport = models.ForeignKey(Sport, on_delete=models.SET_NULL, null=True, blank=True, related_name='videos')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    
    video_url = models.URLField(max_length=500, blank=True, null=True)
    
    thumbnail_url = models.URLField(max_length=500, blank=True, null=True)
    instructor = models.CharField(max_length=100, blank=True, null=True)
    tags = models.JSONField(default=list, blank=True)
    
    duration = models.CharField(max_length=10, blank=True, null=True)
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='uploaded_videos')
    views_count = models.IntegerField(default=0)
    total_likes = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    @property
    def average_rating(self):
        ratings = self.ratings.all()
        if ratings.exists():
            return round(sum(r.rating for r in ratings) / ratings.count(), 1)
        return 0.0
    
    @property
    def ratings_count(self):
        return self.ratings.count()

class VideoRating(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('video', 'user')
    
    def __str__(self):
        return f"{self.user.username} - {self.video.title} - {self.rating}⭐"

class Comment(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    helpful_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.video.title}"

class VideoLike(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('video', 'user')

class VideoBookmark(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='bookmarks')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('video', 'user')