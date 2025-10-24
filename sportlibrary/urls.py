from django.urls import path
from . import views

app_name = 'sportlibrary'

urlpatterns = [
    path('', views.show_sports, name='show_sports'),
    path('saved/', views.saved_sports, name='saved_sports'),
    path('<int:sport_id>/save/', views.save_sport, name='save_sport'),
    path('saved/<int:saved_id>/remove/', views.remove_sport, name='remove_sport'),
    path('saved/clear/', views.clear_all_sports, name='clear_all_sports'),
    # Pakai <str:> supaya bisa angka biasa (e.g. "5") dan UUID-like (e.g. "0000...00a")
    path('<str:sport_id>/', views.sport_detail, name='sport_detail'),
]
