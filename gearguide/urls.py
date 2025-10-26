from django.urls import path
from . import views

app_name = 'gearguide'

urlpatterns = [
    path('', views.show_all_gears, name='show_all_gears'),
    path('add/', views.add_gear, name='add_gear'),
    path('details/<str:gear_id>/', views.show_gear_detail, name='card_details'),
    path('get-gear-json/<str:gear_id>/', views.get_gear_json, name='get_gear_json'),
    path('edit-gear-ajax/<str:gear_id>/', views.edit_gear, name='edit_gear'),
    path('delete/<str:gear_id>/', views.delete_gear, name='delete_gear'),
    path('<str:gear_id>/', views.show_gear_detail, name='card_details_short'),
]
