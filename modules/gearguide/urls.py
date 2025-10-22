from django.urls import path
from . import views

app_name = 'gearguide'

urlpatterns = [
    path('', views.show_all_gears, name='show_all_gears'),
    path('<str:sport_name>/', views.show_gears_by_sport, name='show_gears_by_sport'),
]
