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
]