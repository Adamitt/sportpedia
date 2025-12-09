from django.urls import path
from . import views

app_name = 'profile_app'

urlpatterns = [
<<<<<<< Updated upstream
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Gear 
    path('dashboard/gears/', views.manage_gear, name='manage_gear'),
    path('dashboard/gears/add/', views.add_gear, name='add_gear'),
    path('dashboard/gears/edit/<uuid:gear_id>/', views.edit_gear, name='edit_gear'),
    path('dashboard/gears/delete/<uuid:gear_id>/', views.delete_gear, name='delete_gear'),
    
    # Sport Library (pakai INT)
    path('dashboard/library/', views.manage_library, name='manage_library'),
    path('dashboard/library/add/', views.add_sport, name='add_sport'),
    path('dashboard/library/edit/<int:sport_id>/', views.edit_sport, name='edit_sport'),  # ⬅️ INT
    path('dashboard/library/delete/<int:sport_id>/', views.delete_sport, name='delete_sport'),  # ⬅️ INT
=======
    # Web views (HTML)
    path('', views.profile_page, name='profile_page'),
    path('pengaturan/', views.pengaturan_akun, name='pengaturan_akun'),
    path('clear-history/', views.clear_activity_history, name='clear_activity_history'),
    
    # API views untuk Flutter
    path('api/profile/', views.api_get_profile, name='api_get_profile'),
    path('api/profile/update/', views.api_update_profile, name='api_update_profile'),
    path('api/activity/', views.api_get_activity, name='api_get_activity'),
    path('api/activity/log/', views.api_log_activity, name='api_log_activity'),
    path('api/activity/clear/', views.api_clear_activity, name='api_clear_activity'),
    path('api/change-password/', views.api_change_password, name='api_change_password'),
    path('api/change-email/', views.api_change_email, name='api_change_email'),
    path('api/delete-account/', views.api_delete_account, name='api_delete_account'),
    path('api/stats/', views.api_get_stats, name='api_get_stats'),
>>>>>>> Stashed changes
]