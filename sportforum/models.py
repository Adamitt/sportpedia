from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.contrib.auth.models import User

# 🏷️ 1. Kategori Olahraga
class SportCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


# 🧵 2. Forum Post / Topik Diskusi
class ForumPost(models.Model):
    sport = models.ForeignKey(SportCategory, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_posts')
    content = models.TextField()
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    views = models.PositiveIntegerField(default=0)
    date_posted = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField('Tag', blank=True, related_name='forum_posts')

    class Meta:
        ordering = ['-date_posted']

    def __str__(self):
        return f"{self.title} ({self.sport.name})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    @property
    def total_likes(self):
        return self.likes.count()


# 💬 3. Reply / Komentar Diskusi
class Reply(models.Model):
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply by {self.user} on {self.post}"


# 🏷️ 4. Tag (untuk kategorisasi tambahan)
class Tag(models.Model):
    name = models.CharField(max_length=30, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
