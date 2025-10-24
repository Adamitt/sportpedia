from django.urls import path
from . import views

app_name = 'sportlibrary'

urlpatterns = [
    path('', views.show_sports, name='show_sports'),
    path('saved/', views.saved_sports, name='saved_sports'),
    # Pakai <str:> supaya bisa angka biasa (e.g. "5") dan UUID-like (e.g. "0000...00a")
    path('<str:sport_id>/', views.sport_detail, name='sport_detail'),
]
