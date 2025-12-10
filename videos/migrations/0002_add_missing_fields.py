# No-op migration - all fields already exist in 0001_initial
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0001_initial'),
    ]

    operations = [
        # Intentionally left blank.
        # All fields (thumbnail_url, instructor, tags, total_likes) 
        # are already defined in 0001_initial.
    ]

