from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.contrib.auth.models import User
import uuid

# Forum Post / Topik Diskusi
class ForumPost(models.Model):
    SPORT_CHOICES = [
        ('bulu-tangkis', 'Bulu Tangkis'),
        ('yoga', 'Yoga'),
        ('tenis', 'Tenis'),
        ('renang', 'Renang'),
        ('panahan', 'Panahan'),
        ('lari', 'Lari'),
        ('basket', 'Basket'),
        ('futsal', 'Futsal'),
        ('bersepeda', 'Bersepeda'),
        ('tenis-meja', 'Tenis Meja'),
        ('voli', 'Voli'),
        ('panjat-tebing', 'Panjat Tebing'),
        ('muay-thai', 'Muay Thai'),
        ('golf', 'Golf'),
        ('selancar', 'Selancar'),
        ('pencak-silat', 'Pencak Silat'),
        ('baseball', 'Baseball'),
        ('skateboard', 'Skateboard'),
        ('calisthenics', 'Calisthenics'),
        ('wall-climbing', 'Wall Climbing'),
    ]
    
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    sport = models.CharField(max_length=50, choices=SPORT_CHOICES)
    title = models.CharField(max_length=150)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_posts')
    content = models.TextField()
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    views = models.PositiveIntegerField(default=0)
    date_posted = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField('Tag', blank=True, related_name='forum_posts')

    class Meta:
        ordering = ['-date_posted']

    def __str__(self):
        return f"{self.title} ({self.get_sport_display()})"

    @property
    def total_likes(self):
        return self.likes.count()


# Reply / Komentar Diskusi
class Reply(models.Model):
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply by {self.user} on {self.post}"


# Tag (untuk kategorisasi tambahan)
class Tag(models.Model):
    name = models.CharField(max_length=30, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
