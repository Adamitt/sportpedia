from django.urls import path
from . import views

app_name = 'gearguide'

urlpatterns = [
    path('', views.show_all_gears, name='show_all_gears'),

    path('add/', views.add_gear, name='add_gear'),
    path('details/<int:gear_id>/', views.show_gear_detail, name='card_details'),

    path('json/', views.get_all_gears_json, name="get_all_gears_json"),
    path('json/<uuid:gear_id>/', views.get_gear_json, name="get_gear_json"),

    path('flutter/gears/', views.list_gears_flutter, name='flutter_list_gears'),
    path('flutter/gears/add/', views.add_gear_flutter, name='flutter_add_gear'),
    path(
        'flutter/sports/', 
        views.get_all_sports_json, 
        name='flutter_sports_list',
    ),
    
    path(
        'flutter/gears/<int:gear_id>/edit/', 
        views.edit_gear_flutter,
        name='flutter_edit_gear',
    ),
    path(
        'flutter/gears/<int:gear_id>/delete/',
        views.delete_gear_flutter,
        name='flutter_delete_gear',
    ),

    path('edit-gear-ajax/<uuid:gear_id>/', views.edit_gear, name='edit_gear'),
    path('delete/<uuid:gear_id>/', views.delete_gear, name='delete_gear'),

    path('<uuid:gear_id>/', views.show_gear_detail, name='card_details_short'),
]
