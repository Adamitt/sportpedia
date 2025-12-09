from django.urls import path
from . import views


app_name = 'videos'

urlpatterns = [
    # Gallery and Detail
    path('', views.video_gallery, name='video_gallery'),
    path('<int:video_id>/', views.video_detail, name='video_detail'),
    
    # Interactions
    path('<int:video_id>/comment/', views.add_comment, name='add_comment'),
    path('<int:video_id>/like/', views.like_video, name='like_video'),
    path('<int:video_id>/bookmark/', views.bookmark_video, name='bookmark_video'),
    path('comment/<int:comment_id>/helpful/', views.helpful_comment, name='helpful_comment'),
    
    # CRUD Operations
    path('create/', views.video_create, name='video_create'),
    path('<int:video_id>/update/', views.video_update, name='video_update'),
    path('<int:video_id>/delete/', views.video_delete, name='video_delete'),

    # ============================================
    # API ENDPOINTS 
    # ============================================
    # API Login endpoint
    path('api/login/', views.api_login, name='api_login'),
    
    # List video 
    path('api/', views.api_video_list, name='api_video_list'),
    
    # Sports list
    path('api/sports/', views.api_sports_list, name='api_sports_list'),
    
    # Komentar video 
    path('api/<int:video_id>/comments/', views.api_video_comments, name='api_video_comments'),
    path('api/<int:video_id>/comment/', views.api_video_add_comment, name='api_video_add_comment'),
    path('api/comment/<int:comment_id>/reply/', views.api_comment_reply, name='api_comment_reply'),
    
    # Rating video
    path('api/<int:video_id>/rate/', views.api_video_rate, name='api_video_rate'),
    
    # Admin CRUD API endpoints (must be before detail endpoint)
    path('api/create/', views.api_video_create, name='api_video_create'),
    path('api/<int:video_id>/update/', views.api_video_update, name='api_video_update'),
    path('api/<int:video_id>/delete/', views.api_video_delete, name='api_video_delete'),
    
    path('api/<int:video_id>/', views.api_video_detail, name='api_video_detail'),
]