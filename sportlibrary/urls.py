from django.urls import path
from . import views

app_name = 'sportlibrary'

urlpatterns = [
    # Halaman utama (Library)
    path('', views.index, name='index'),

    # Halaman detail olahraga
    path('sport/<uuid:sport_id>/', views.sport_detail, name='sport_detail'),

    # Filter berdasarkan kategori
    path('sport/category/<str:category>/', views.sport_by_category, name='sport_by_category'),

    # Search olahraga (query string: ?q=...&category=...&difficulty=...)
    path('search/', views.search_sports, name='search_sports'),

    # Halaman olahraga populer
    path('popular/', views.popular_sports, name='popular_sports'),

    # Bookmark
    path('bookmark/toggle/<uuid:sport_id>/', views.toggle_bookmark, name='toggle_bookmark'),
    path('bookmarks/', views.bookmark_list, name='bookmark_list'),
    path('bookmark/update/<uuid:bookmark_id>/', views.update_bookmark_notes, name='update_bookmark_notes'),

    # Video
    path('sport/<uuid:sport_id>/videos/', views.video_list, name='video_list'),
    path('video/complete/<uuid:video_id>/', views.mark_video_complete, name='mark_video_complete'),

    # Gear detail
    path('gear/<uuid:gear_id>/', views.gear_detail, name='gear_detail'),

    # User progress
    path('my-progress/', views.my_progress, name='my_progress'),

    # API endpoints untuk AJAX
    path('api/bookmark-status/<uuid:sport_id>/', views.api_bookmark_status, name='api_bookmark_status'),
    path('api/progress-status/<uuid:sport_id>/', views.api_progress_status, name='api_progress_status'),
    path('import-items', views.import_sports_from_json, name='import_items'),

]
