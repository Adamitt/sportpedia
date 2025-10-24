from django.urls import path
from . import views

app_name = 'sportlibrary'

urlpatterns = [
    path('', views.show_sports, name='show_sports'),
    path('saved/', views.saved_sports, name='saved_sports'),
    path('<int:sport_id>/', views.sport_detail, name='sport_detail'),  # ⬅️ ini penting
    path('api/update-progress/<int:sport_id>/', views.update_progress, name='update_progress'),
]