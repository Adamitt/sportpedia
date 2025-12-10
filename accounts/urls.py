from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # URL Web HTML
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # URL API FLUTTER 
    path('api/login/', views.api_login, name='api_login'),
    path('api/register/', views.api_register, name='api_register'),
    path('api/logout/', views.api_logout, name='api_logout'),
]