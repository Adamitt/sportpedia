from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),                 # HTML
    path('flutter-login/', views.flutter_login, name='flutter_login'),  # JSON
    path('logout/', views.logout_view, name='logout'),
]
