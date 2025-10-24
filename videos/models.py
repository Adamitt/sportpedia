from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from sportlibrary.models import Sport  

class Video(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='videos')  # ⬅️ Foreign Key ke Sport dari sportlibrary
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    
    video_url = models.URLField(blank=True, null=True)
    video_file = models.FileField(upload_to='videos/files/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='videos/thumbnails/', blank=True, null=True)
    
    duration = models.CharField(max_length=10)
    uploader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_videos')
    views_count = models.IntegerField(default=0)
    
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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('video', 'user')
    
    def __str__(self):
        return f"{self.user.username} - {self.video.title} - {self.rating}⭐"

class Comment(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('video', 'user')

class VideoBookmark(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='bookmarks')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('video', 'user')