from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Web views (HTML)
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # API views untuk Flutter
    path('api/login/', views.api_login, name='api_login'),
    path('api/register/', views.api_register, name='api_register'),
    path('api/logout/', views.api_logout, name='api_logout'),
    path('api/user-info/', views.api_user_info, name='api_user_info'),
]