from django.urls import path
from . import views

app_name = 'sportlibrary'

urlpatterns = [
    path('', views.show_sports, name='show_sports'),
    path('<int:sport_id>/', views.sport_detail, name='sport_detail'),  # ⬅️ ini penting
]
