from django.db import models
from django.contrib.auth.models import User

class Sport(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
<<<<<<< Updated upstream
=======
    
    # Field image harus ada dan nullable untuk data lama
    image = models.ImageField(upload_to='sports/', blank=True, null=True)
    
>>>>>>> Stashed changes
    category = models.CharField(max_length=20)
    difficulty = models.CharField(max_length=20)
    description = models.TextField()
    history = models.TextField()

    # JSONField untuk list data
    rules = models.JSONField(default=list)
    techniques = models.JSONField(default=list)
    benefits = models.JSONField(default=list)
    popular_countries = models.JSONField(default=list)
    tags = models.JSONField(default=list)

    # ManyToMany relation dengan Gear
    gears = models.ManyToManyField("gearguide.Gear", related_name="gear_relations", blank=True)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'sportlibrary_sport'  # Eksplisit define table name
        verbose_name = 'Sport'
        verbose_name_plural = 'Sports'

class SavedSport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_sports")
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name="saved_by_users")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'sport')
        db_table = 'sportlibrary_savedsport'

    def __str__(self):
        return f"{self.user.username} - {self.sport.name}"