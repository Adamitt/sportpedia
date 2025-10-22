from django.db import models
import uuid

# Create your models here.
class Sport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)