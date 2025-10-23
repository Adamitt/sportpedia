from django.urls import path
from . import views

app_name = 'sportlibrary'

urlpatterns = [
    path('', views.show_sports, name='show_sports'),
    path('saved/', views.saved_sports, name='saved_sports'),
    path('<int:sport_id>/', views.sport_detail, name='sport_detail'),  # ⬅️ ini penting
    path('<uuid:sport_id>/progress/', views.update_progress, name='update_progress'),
    path('saved/', views.get_saved_sports, name='get_saved_sports'),
    path('toggle/<int:sport_id>/', views.toggle_saved_sport, name='toggle_saved_sport'),
]
