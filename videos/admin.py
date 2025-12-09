from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Video, VideoRating, Comment, VideoLike, VideoBookmark

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """
    READ ONLY Admin untuk Video - hanya untuk pengecekan data oleh asdos
    """
    
    list_display = (
        'thumbnail_preview',
        'title',
        'sport_link',
        'difficulty_badge',
        'duration',
        'uploader_display',
        'views_count',
        'rating_display',
        'created_at'
    )
    
    list_filter = ('difficulty', 'sport', 'created_at')
    search_fields = ('title', 'description', 'uploader__username', 'sport__name')
    ordering = ['-created_at']
    list_per_page = 25
    
    # READ ONLY - tidak bisa add/edit/delete
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    # Custom display methods
    @admin.display(description='Thumbnail')
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="width: 80px; height: 45px; object-fit: cover; border-radius: 4px;" />',
                obj.thumbnail.url
            )
        # YouTube thumbnail fallback
        if obj.video_url and 'youtube.com' in obj.video_url:
            video_id = obj.video_url.split('v=')[-1].split('&')[0]
            return format_html(
                '<img src="https://img.youtube.com/vi/{}/hqdefault.jpg" style="width: 80px; height: 45px; object-fit: cover; border-radius: 4px;" />',
                video_id
            )
        return format_html('<div style="width: 80px; height: 45px; background: #e0e0e0; border-radius: 4px; display: flex; align-items: center; justify-content: center;">🎥</div>')
    
    @admin.display(description='Sport', ordering='sport__name')
    def sport_link(self, obj):
        url = reverse('admin:sportlibrary_sport_change', args=[obj.sport.id])
        return format_html('<a href="{}">{}</a>', url, obj.sport.name)
    
    @admin.display(description='Difficulty')
    def difficulty_badge(self, obj):
        colors = {
            'beginner': '#4CAF50',
            'intermediate': '#FF9800',
            'advanced': '#F44336'
        }
        color = colors.get(obj.difficulty, '#999')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_difficulty_display()
        )
    
    @admin.display(description='Uploader')
    def uploader_display(self, obj):
        return format_html(
            '<span style="color: #1976d2;">👤 {}</span>',
            obj.uploader.username
        )
    
    @admin.display(description='Rating')
    @admin.display(description='Rating')
    def rating_display(self, obj):
        rating = obj.average_rating
        count = obj.ratings_count
        stars = '⭐' * int(rating)
        rating_str = f'{rating:.1f}'  
        return format_html(
            '<span title="{} ratings">{} {}</span>',
            count,
            stars,
            rating_str  
        )


@admin.register(VideoRating)
class VideoRatingAdmin(admin.ModelAdmin):
    """READ ONLY Admin untuk VideoRating"""
    
    list_display = ('video', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('video__title', 'user__username')
    ordering = ['-created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """READ ONLY Admin untuk Comment"""
    
    list_display = ('user', 'video', 'text_preview', 'rating', 'helpful_count', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('text', 'user__username', 'video__title')
    ordering = ['-created_at']
    
    @admin.display(description='Comment')
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(VideoLike)
class VideoLikeAdmin(admin.ModelAdmin):
    """READ ONLY Admin untuk VideoLike"""
    
    list_display = ('user', 'video', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'video__title')
    ordering = ['-created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(VideoBookmark)
class VideoBookmarkAdmin(admin.ModelAdmin):
    """READ ONLY Admin untuk VideoBookmark"""
    
    list_display = ('user', 'video', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'video__title')
    ordering = ['-created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False