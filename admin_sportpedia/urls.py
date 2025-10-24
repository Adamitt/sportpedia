from django.urls import path
from . import views

app_name = 'admin_sportpedia'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/gears/', views.manage_gear, name='manage_gear'),
    path('dashboard/gears/add/', views.add_gear, name='add_gear'),
    path('dashboard/gears/edit/<uuid:gear_id>/', views.edit_gear, name='edit_gear'),
    path('dashboard/gears/delete/<uuid:gear_id>/', views.delete_gear, name='delete_gear'),

    path('dashboard/library/', views.manage_library, name='manage_library'),
    path('dashboard/library/add/', views.add_sport, name='add_sport'),
    path('dashboard/library/edit/<uuid:sport_id>/', views.edit_sport, name='edit_sport'), 
    path('dashboard/library/delete/<uuid:sport_id>/', views.delete_sport, name='delete_sport'),

    path('dashboard/admins/', views.manage_admin, name='manage_admin'), # Page with table & modal
    path('dashboard/admins/add/', views.add_admin, name='add_admin'),     # Handles POST for add
    path('dashboard/admins/edit/<int:admin_id>/', views.edit_admin, name='edit_admin'),   # Handles POST for edit
    path('dashboard/admins/delete/<int:admin_id>/', views.delete_admin, name='delete_admin'), # Handles POST for delete
    path('api/admin-data/<int:admin_id>/', views.get_admin_data, name='get_admin_data'),
]
