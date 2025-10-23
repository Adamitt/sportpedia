from django.contrib import admin
from .models import Gear

@admin.register(Gear)
class GearAdmin(admin.ModelAdmin):
    list_display = ('name', 'sport', 'level', 'price_range', 'required')
    search_fields = ('name', 'sport__name')
    list_filter = ('level', 'required')
