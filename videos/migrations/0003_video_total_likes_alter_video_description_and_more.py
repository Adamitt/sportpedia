# No-op migration - all fields already correctly defined in 0001_initial
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sportlibrary', '0001_initial'),
        ('videos', '0001_initial'),
    ]

    operations = [
        # Intentionally left blank.
        # All fields are already correctly defined in 0001_initial.
    ]
