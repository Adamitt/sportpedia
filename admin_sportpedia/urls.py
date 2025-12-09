# admin_sportpedia/urls.py
from django.urls import path
from . import views

app_name = 'admin_sportpedia'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),

    # Gear 
    path('dashboard/gears/', views.manage_gear, name='manage_gear'),
    path('dashboard/gears/add/', views.add_gear, name='add_gear'),
    path('dashboard/gears/edit/<str:gear_id>/', views.edit_gear, name='edit_gear'),
    path('dashboard/gears/delete/<str:gear_id>/', views.delete_gear, name='delete_gear'),
    
    # Sport Library (pakai INT)
    path('dashboard/library/', views.manage_library, name='manage_library'),
    path('dashboard/library/add/', views.add_sport, name='add_sport'),
    path('dashboard/library/edit/<int:sport_id>/', views.edit_sport, name='edit_sport'),
    path('dashboard/library/delete/<int:sport_id>/', views.delete_sport, name='delete_sport'),

    path('dashboard/admins/', views.manage_admin, name='manage_admin'),
    path('dashboard/admins/add/', views.add_admin, name='add_admin'),
    path('dashboard/admins/edit/<int:admin_id>/', views.edit_admin, name='edit_admin'),
    path('api/admin-data/<int:admin_id>/', views.get_admin_data, name='get_admin_data'),
]
