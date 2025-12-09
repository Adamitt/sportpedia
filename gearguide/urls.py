from django.urls import path
from . import views

app_name = 'gearguide'

urlpatterns = [
    # Halaman utama (HTML)
    path('', views.show_all_gears, name='show_all_gears'),

    # Tambah/Edit/Delete HTML
    path('add/', views.add_gear, name='add_gear'),
    path('details/<uuid:gear_id>/', views.show_gear_detail, name='card_details'),

    # API JSON (web)
    path('json/', views.get_all_gears_json, name="get_all_gears_json"),
    path('json/<uuid:gear_id>/', views.get_gear_json, name="get_gear_json"),

    # API FLUTTER (LIST + CRUD)
    path('flutter/gears/', views.list_gears_flutter, name='flutter_list_gears'),
    path('flutter/gears/add/', views.add_gear_flutter, name='flutter_add_gear'),
    # urls.py (BENAR jika ID Anda integer)
    path(
        'flutter/sports/', 
        views.get_all_sports_json, # Pastikan Anda memiliki view ini di views.py
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

    # AJAX EDIT/DELETE (WEB)
    path('edit-gear-ajax/<uuid:gear_id>/', views.edit_gear, name='edit_gear'),
    path('delete/<uuid:gear_id>/', views.delete_gear, name='delete_gear'),

    # **HARUS PALING TERAKHIR**: short detail
    path('<uuid:gear_id>/', views.show_gear_detail, name='card_details_short'),
]
