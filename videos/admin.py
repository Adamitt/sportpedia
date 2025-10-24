from django.contrib import admin
from .models import Video, VideoRating, Comment, VideoLike, VideoBookmark


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'sport', 'difficulty', 'views_count', 'average_rating', 'created_at')
    list_filter = ('sport', 'difficulty', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('views_count', 'created_at', 'updated_at')

@admin.register(VideoRating)
class VideoRatingAdmin(admin.ModelAdmin):
    list_display = ('video', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'video', 'rating', 'helpful_count', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('text', 'user__username', 'video__title')

@admin.register(VideoLike)
class VideoLikeAdmin(admin.ModelAdmin):
    list_display = ('video', 'user', 'created_at')

@admin.register(VideoBookmark)
class VideoBookmarkAdmin(admin.ModelAdmin):
    list_display = ('video', 'user', 'created_at')