from django.urls import path
from . import views
from django.shortcuts import render, get_object_or_404
from .models import Video

app_name = 'videos'

urlpatterns = [
    path('', views.video_gallery, name='gallery'), 
    path('<int:video_id>/', views.video_detail, name='detail'),
    path('<int:video_id>/comment/', views.add_comment, name='add_comment'),
    path('<int:video_id>/like/', views.like_video, name='like'),
    path('<int:video_id>/bookmark/', views.bookmark_video, name='bookmark'),
    path('comment/<int:comment_id>/helpful/', views.helpful_comment, name='helpful_comment'),
]

def video_detail(request, slug):
    video = get_object_or_404(Video, slug=slug)
    return render(request, 'videos/video_detail.html', {'video': video})