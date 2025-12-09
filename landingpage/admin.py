# landingpage/admin.py
from django.contrib import admin
from .models import Testimonial

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "category", "user", "is_approved", "created_at")
    list_filter  = ("category", "is_approved", "created_at")
    search_fields = ("title", "text", "user__username", "user__first_name", "user__last_name")
    ordering = ("-created_at",)
