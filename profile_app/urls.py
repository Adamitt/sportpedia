from django.urls import path
from . import views

app_name = 'profile_app'

urlpatterns = [
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
]
