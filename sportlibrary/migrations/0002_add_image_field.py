from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('sportlibrary', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sport',
            name='image',
            field=models.ImageField(upload_to='sports/', blank=True, null=True),
        ),
    ]
