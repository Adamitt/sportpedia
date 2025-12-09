# Generated manually to fix database schema mismatch
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0001_initial'),
    ]

    operations = [
        # Add thumbnail_url if it doesn't exist (rename from thumbnail)
        migrations.AddField(
            model_name='video',
            name='thumbnail_url',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
        # Add instructor field
        migrations.AddField(
            model_name='video',
            name='instructor',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        # Add tags field
        migrations.AddField(
            model_name='video',
            name='tags',
            field=models.JSONField(blank=True, default=list),
        ),
        # Add total_likes field
        migrations.AddField(
            model_name='video',
            name='total_likes',
            field=models.PositiveIntegerField(default=0),
        ),
    ]

