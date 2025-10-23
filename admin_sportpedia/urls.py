from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/gears/', views.manage_gear, name='manage_gear'),
    path('dashboard/gears/add/', views.add_gear, name='add_gear'),
    path('dashboard/gears/edit/<uuid:gear_id>/', views.edit_gear, name='edit_gear'),
    path('dashboard/gears/delete/<uuid:gear_id>/', views.delete_gear, name='delete_gear'),
]
